from django.urls import reverse_lazy
from django.views.generic import DeleteView, TemplateView, UpdateView, CreateView
from django.utils import timezone
from django.db.models import Sum
from datetime import timedelta
from activities.models import RunActivity, CyclingActivity, SwimActivity
from health.models import ErgometryTest
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
        
        #totales del mes en curso
        run_stats = runs.aggregate(km=Sum('distance_km'), desnivel=Sum('elevation_gain'), tiempo=Sum('duration'))
        bike_stats = rides.aggregate(km=Sum('distance_km'), desnivel=Sum('elevation_gain'), tiempo=Sum('duration'))
        swim_stats = swims.aggregate(m=Sum('distance_meters'), tiempo=Sum('duration'))

        #stats formateados al frontend
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
class RunUpdateView(UpdateView):
    model = RunActivity
    form_class = RunActivityForm
    template_name = 'actividad_form.html'
    success_url = reverse_lazy('actividades') # Vuelve a la tabla al guardar

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