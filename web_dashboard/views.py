from django.urls import reverse_lazy
from django.views.generic import DeleteView, TemplateView, UpdateView, CreateView
from django.utils import timezone
from django.db.models import Sum, Q, Avg
from django.db.models.functions import ExtractMonth, ExtractDay
from datetime import timedelta
import calendar

from activities.models import RunActivity, CyclingActivity, SwimActivity
from health.models import ErgometryTest, DailyHealth
from goals.models import RaceGoal
from .forms import BikeActivityForm, RunActivityForm, SwimActivityForm

def formatear_horas(td):
    """Convierte un timedelta en formato HH:MM:SS incluso si supera las 24 horas"""
    if not td: return "00:00:00"
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

class DashboardView(TemplateView):
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        hoy = now.date()
        year = now.year
        month = now.month

        context['mes_actual'] = now.strftime("%m/%Y")
        context['anio_actual'] = year

        # ==========================================
        # 0. CENTRO DE COMANDO (Presente y Futuro)
        # ==========================================
        proximo_objetivo = RaceGoal.objects.filter(date__gte=hoy).order_by('date').first()
        context['proximo_objetivo'] = proximo_objetivo

        ultima_salud = DailyHealth.objects.order_by('-date').first()
        context['motor_salud'] = ultima_salud
        
        estado_motor = "Óptimo"
        color_motor = "success"
        alerta_motor = ""

        if ultima_salud:
            if ultima_salud.sleep_score and ultima_salud.sleep_score < 50:
                estado_motor, color_motor = "Fatiga", "warning"
                alerta_motor = "⚠️ Descanso pobre anoche. Considerá bajar la intensidad hoy."
            elif ultima_salud.stress_level and ultima_salud.stress_level > 70:
                estado_motor, color_motor = "Sobrecarga", "danger"
                alerta_motor = "🔥 Estrés alto. Sugerencia: Día de recuperación activa o descanso."
        
        context['estado_motor'] = estado_motor
        context['color_motor'] = color_motor
        context['alerta_motor'] = alerta_motor

        # ==========================================
        # 0.5. RESUMEN SEMANAL (Semana Actual vs Pasada Separada)
        # ==========================================
        start_current_week = hoy - timedelta(days=hoy.weekday())
        start_previous_week = start_current_week - timedelta(days=7)

        def get_weekly_data(start_date):
            end_date = start_date + timedelta(days=6)
            run_km = [0] * 7
            run_elev = [0] * 7
            bike_km = [0] * 7
            
            runs = RunActivity.objects.filter(date__date__gte=start_date, date__date__lte=end_date)
            bikes = CyclingActivity.objects.filter(date__date__gte=start_date, date__date__lte=end_date)
            
            for run in runs:
                idx = run.date.weekday()
                run_km[idx] += float(run.distance_km or 0)
                run_elev[idx] += int(run.elevation_gain or 0)
                
            for bike in bikes:
                idx = bike.date.weekday()
                bike_km[idx] += float(bike.distance_km or 0)
                
            return (
                [round(km, 1) for km in run_km], 
                run_elev, 
                [round(km, 1) for km in bike_km], 
                round(sum(run_km), 1), 
                sum(run_elev), 
                round(sum(bike_km), 1)
            )

        (curr_run_daily, curr_run_elev, curr_bike_daily, 
         curr_run_total, curr_run_elev_total, curr_bike_total) = get_weekly_data(start_current_week)
         
        (prev_run_daily, prev_run_elev, prev_bike_daily, 
         prev_run_total, prev_run_elev_total, prev_bike_total) = get_weekly_data(start_previous_week)

        dias_semana = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
        calendario_semanal = []
        
        for i in range(7):
            calendario_semanal.append({
                'dia': dias_semana[i],
                'run_actual': curr_run_daily[i],
                'run_pasada': prev_run_daily[i],
                'elev_actual': curr_run_elev[i],
                'bike_actual': curr_bike_daily[i],
                'bike_pasada': prev_bike_daily[i]
            })

        context['resumen_semanal'] = {
            'calendario': calendario_semanal,
            'run_total_actual': curr_run_total,
            'run_total_pasada': prev_run_total,
            'run_elev_total': curr_run_elev_total,
            'bike_total_actual': curr_bike_total,
            'bike_total_pasada': prev_bike_total,
            'run_tendencia': "positiva" if curr_run_total >= prev_run_total else "negativa",
            'bike_tendencia': "positiva" if curr_bike_total >= prev_bike_total else "negativa"
        }

        # ==========================================
        # 1. MÉTRICAS MENSUALES
        # ==========================================
        runs_month = RunActivity.objects.filter(date__year=year, date__month=month)
        bikes_month = CyclingActivity.objects.filter(date__year=year, date__month=month)
        swims_month = SwimActivity.objects.filter(date__year=year, date__month=month)
        
        run_month_km = runs_month.aggregate(Sum('distance_km'))['distance_km__sum'] or 0
        bike_month_km = bikes_month.aggregate(Sum('distance_km'))['distance_km__sum'] or 0
        swim_month_km = (swims_month.aggregate(Sum('distance_meters'))['distance_meters__sum'] or 0) / 1000.0

        trail_km = runs_month.filter(is_trail=True).aggregate(Sum('distance_km'))['distance_km__sum'] or 0
        calle_km = runs_month.filter(is_trail=False).aggregate(Sum('distance_km'))['distance_km__sum'] or 0
        
        days_in_month = calendar.monthrange(year, month)[1]
        run_mensual_desnivel = [0] * days_in_month
        
        runs_daily_elev = runs_month.annotate(day=ExtractDay('date')).values('day').annotate(elev=Sum('elevation_gain'))
        for item in runs_daily_elev:
            if item['day']:
                run_mensual_desnivel[item['day'] - 1] = int(item['elev'] or 0)

        total_desnivel_mes = runs_month.aggregate(Sum('elevation_gain'))['elevation_gain__sum'] or 0

        run_te = runs_month.aggregate(aer=Avg('te_aerobic'), ana=Avg('te_anaerobic'))
        bike_te = bikes_month.aggregate(aer=Avg('te_aerobic'), ana=Avg('te_anaerobic'))
        swim_te = swims_month.aggregate(aer=Avg('te_aerobic'), ana=Avg('te_anaerobic'))

        def td_to_minutes(td):
            return int(td.total_seconds() / 60) if td else 0

        run_time = runs_month.aggregate(Sum('duration'))['duration__sum']
        bike_time = bikes_month.aggregate(Sum('duration'))['duration__sum']
        swim_time = swims_month.aggregate(Sum('duration'))['duration__sum']
        
        context['mensual'] = {
            'run_km': float(run_month_km),
            'bike_km': float(bike_month_km),
            'swim_km': float(swim_month_km),
            'trail_km': float(trail_km),
            'calle_km': float(calle_km),
            'run_desnivel_diario': run_mensual_desnivel,
            'total_desnivel': int(total_desnivel_mes),
            'dias_del_mes': list(range(1, days_in_month + 1)),
            'run_min': td_to_minutes(run_time),
            'bike_min': td_to_minutes(bike_time),
            'swim_min': td_to_minutes(swim_time),
            'te_aerobic': [float(run_te['aer'] or 0), float(bike_te['aer'] or 0), float(swim_te['aer'] or 0)],
            'te_anaerobic': [float(run_te['ana'] or 0), float(bike_te['ana'] or 0), float(swim_te['ana'] or 0)]
        }

        # ==========================================
        # 2. MÉTRICAS ANUALES
        # ==========================================
        run_anual_km = [0] * 12
        bike_anual_km = [0] * 12
        swim_anual_km = [0] * 12
        run_anual_desnivel = [0] * 12

        runs_grouped = RunActivity.objects.filter(date__year=year).annotate(month=ExtractMonth('date')).values('month').annotate(total_km=Sum('distance_km'), total_elev=Sum('elevation_gain'))
        bikes_grouped = CyclingActivity.objects.filter(date__year=year).annotate(month=ExtractMonth('date')).values('month').annotate(total=Sum('distance_km'))
        swims_grouped = SwimActivity.objects.filter(date__year=year).annotate(month=ExtractMonth('date')).values('month').annotate(total=Sum('distance_meters'))

        for item in runs_grouped:
            run_anual_km[item['month'] - 1] = float(item['total_km'])
            run_anual_desnivel[item['month'] - 1] = int(item['total_elev'] or 0)
            
        for item in bikes_grouped:
            bike_anual_km[item['month'] - 1] = float(item['total'])
            
        for item in swims_grouped:
            swim_anual_km[item['month'] - 1] = float(item['total']) / 1000.0

        total_desnivel_anio = RunActivity.objects.filter(date__year=year).aggregate(Sum('elevation_gain'))['elevation_gain__sum'] or 0
        
        total_run_anio = RunActivity.objects.filter(date__year=year).aggregate(Sum('distance_km'))['distance_km__sum'] or 0
        total_bike_anio = CyclingActivity.objects.filter(date__year=year).aggregate(Sum('distance_km'))['distance_km__sum'] or 0
        total_swim_anio = (SwimActivity.objects.filter(date__year=year).aggregate(Sum('distance_meters'))['distance_meters__sum'] or 0) / 1000.0

        context['graficos_anuales'] = {
            'run': run_anual_km,
            'bike': bike_anual_km,
            'swim': swim_anual_km,
            'run_desnivel': run_anual_desnivel,
            'total_desnivel': int(total_desnivel_anio),
            'total_run_km': float(total_run_anio),
            'total_bike_km': float(total_bike_anio),
            'total_swim_km': float(total_swim_anio)
        }

        return context

class ActividadesView(TemplateView):
    template_name = 'actividades.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        
        runs = RunActivity.objects.filter(date__year=now.year, date__month=now.month).order_by('-date')
        rides = CyclingActivity.objects.filter(date__year=now.year, date__month=now.month).order_by('-date')
        swims = SwimActivity.objects.filter(date__year=now.year, date__month=now.month).order_by('-date')
        
        context['runs'] = runs
        context['rides'] = rides
        context['swims'] = swims
        context['mes_actual'] = now.strftime("%m/%Y")
        
        run_stats = runs.aggregate(km=Sum('distance_km'), desnivel=Sum('elevation_gain'), tiempo=Sum('duration'))
        bike_stats = rides.aggregate(km=Sum('distance_km'), desnivel=Sum('elevation_gain'), tiempo=Sum('duration'))
        swim_stats = swims.aggregate(m=Sum('distance_meters'), tiempo=Sum('duration'))

        context['stats'] = {
            'run': {
                'km': run_stats['km'] or 0,
                'desnivel': run_stats['desnivel'] or 0,
                'tiempo': formatear_horas(run_stats['tiempo'])
            },
            'bike': {
                'km': bike_stats['km'] or 0,
                'desnivel': bike_stats['desnivel'] or 0,
                'tiempo': formatear_horas(bike_stats['tiempo'])
            },
            'swim': {
                'm': swim_stats['m'] or 0,
                'tiempo': formatear_horas(swim_stats['tiempo'])
            }
        }
        
        context['zonas_hr'] = ErgometryTest.objects.order_by('-date').first()
        
        return context

# --- CRUD RUNNING ---
class RunUpdateView(UpdateView):
    model = RunActivity
    form_class = RunActivityForm
    template_name = 'actividad_form.html'
    success_url = reverse_lazy('actividades')

class RunDeleteView(DeleteView):
    model = RunActivity
    template_name = 'actividad_confirm_delete.html'
    success_url = reverse_lazy('actividades')
    
class RunCreateView(CreateView):
    model = RunActivity
    form_class = RunActivityForm
    template_name = 'actividad_form.html'
    success_url = reverse_lazy('actividades')
    
# --- CRUD CICLISMO ---
class BikeCreateView(CreateView):
    model = CyclingActivity
    form_class = BikeActivityForm
    template_name = 'actividad_form.html'
    success_url = reverse_lazy('actividades')

class BikeUpdateView(UpdateView):
    model = CyclingActivity
    form_class = BikeActivityForm
    template_name = 'actividad_form.html'
    success_url = reverse_lazy('actividades')

class BikeDeleteView(DeleteView):
    model = CyclingActivity
    template_name = 'actividad_confirm_delete.html'
    success_url = reverse_lazy('actividades')

# --- CRUD NATACIÓN ---
class SwimCreateView(CreateView):
    model = SwimActivity
    form_class = SwimActivityForm
    template_name = 'actividad_form.html'
    success_url = reverse_lazy('actividades')

class SwimUpdateView(UpdateView):
    model = SwimActivity
    form_class = SwimActivityForm
    template_name = 'actividad_form.html'
    success_url = reverse_lazy('actividades')

class SwimDeleteView(DeleteView):
    model = SwimActivity
    template_name = 'actividad_confirm_delete.html'
    success_url = reverse_lazy('actividades')