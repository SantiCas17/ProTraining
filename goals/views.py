import gpxpy
from django.views.generic import DeleteView, ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.db.models import Sum, Avg
from .models import RaceGoal
from .forms import RaceGoalForm
from activities.models import RunActivity, CyclingActivity

class GoalListView(ListView):
    model = RaceGoal
    template_name = 'objetivos.html' # El panel general de metas
    context_object_name = 'goals'

    def get_queryset(self):
        # Ordenamos para que las carreras más próximas salgan primero
        return RaceGoal.objects.filter(is_completed=False).order_by('date')

class GoalDetailView(DetailView):
    model = RaceGoal
    template_name = 'objetivo_mapa.html'
    context_object_name = 'goal'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        goal = self.get_object()
        
        track_points = []
        elevation_profile = []
        km_markers = [] # NUEVO: Array para guardar los puntos cada 5km
        
        # 1. MOTOR GEOESPACIAL Y ALTIMETRÍA (GPX)
        if goal.gpx_file:
            try:
                with goal.gpx_file.open('r') as gpx_file:
                    gpx = gpxpy.parse(gpx_file)
                    
                    distancia_acumulada = 0
                    punto_anterior = None
                    siguiente_marcador_km = 5 # Queremos el primer marcador en el km 5

                    for track in gpx.tracks:
                        for segment in track.segments:
                            for point in segment.points:
                                track_points.append([point.latitude, point.longitude])
                                
                                if punto_anterior:
                                    distancia_acumulada += point.distance_2d(punto_anterior)
                                
                                # ¿Cruzamos la barrera de los próximos 5km?
                                distancia_km = distancia_acumulada / 1000.0
                                if distancia_km >= siguiente_marcador_km:
                                    km_markers.append({
                                        'km': siguiente_marcador_km,
                                        'lat': point.latitude,
                                        'lng': point.longitude
                                    })
                                    siguiente_marcador_km += 5 # Preparamos el siguiente múltiplo de 5
                                
                                if point.elevation is not None:
                                    elevation_profile.append({
                                        'x': round(distancia_km, 2),
                                        'y': round(point.elevation, 1)
                                    })
                                
                                punto_anterior = point
            except Exception as e:
                print(f"Error procesando GPX: {e}")
                
        context['track_points'] = track_points
        context['elevation_profile'] = elevation_profile
        context['km_markers'] = km_markers # Mandamos los marcadores al frontend

        # 2. MOTOR PREDICTIVO (READINESS) MULTI-FACTOR
        volumen_km = 0
        volumen_desnivel = 0
        promedio_te = 0

        # Filtramos entrenamientos del bloque
        if goal.race_type in ['TRAIL', 'STREET']:
            entrenamientos = RunActivity.objects.filter(date__gte=goal.training_start_date, date__lte=goal.date)
            volumen_km = entrenamientos.aggregate(Sum('distance_km'))['distance_km__sum'] or 0
            volumen_desnivel = entrenamientos.aggregate(Sum('elevation_gain'))['elevation_gain__sum'] or 0
            promedio_te = entrenamientos.aggregate(Avg('te_aerobic'))['te_aerobic__avg'] or 0

        elif goal.race_type == 'MTB':
            entrenamientos = CyclingActivity.objects.filter(date__gte=goal.training_start_date, date__lte=goal.date)
            volumen_km = entrenamientos.aggregate(Sum('distance_km'))['distance_km__sum'] or 0
            volumen_desnivel = entrenamientos.aggregate(Sum('elevation_gain'))['elevation_gain__sum'] or 0
            promedio_te = entrenamientos.aggregate(Avg('te_aerobic'))['te_aerobic__avg'] or 0

        # Sistema de Puntuación (Score de 0 a 100)
        estado_forma = "Sin Datos"
        color_estado = "secondary"
        progreso_porcentaje = 0
        diagnosticos = [] # Guardará los avisos específicos

        # A. Evaluación de Volumen (Km)
        if goal.target_distance_km > 0:
            ratio_km = volumen_km / goal.target_distance_km
            if ratio_km >= 4:
                diagnosticos.append("✅ Km: Volumen sobrado para la distancia.")
                progreso_porcentaje += 50
            elif ratio_km >= 2.5:
                diagnosticos.append("⚠️ Km: Volumen aceptable, pero justo.")
                progreso_porcentaje += 30
            else:
                diagnosticos.append("❌ Km: Volumen insuficiente. ¡Riesgo!")
                progreso_porcentaje += 10
        else:
            progreso_porcentaje += 50 # Si no hay meta, damos puntaje completo

        # B. Evaluación de Desnivel
        if goal.target_elevation_gain > 0:
            ratio_desnivel = volumen_desnivel / goal.target_elevation_gain
            if ratio_desnivel >= 4:
                diagnosticos.append("✅ Desnivel: Piernas de acero. Excelente acumulación.")
                progreso_porcentaje += 50
            elif ratio_desnivel >= 2.5:
                diagnosticos.append("⚠️ Desnivel: Aceptable. Vas a sufrir un poco las trepadas.")
                progreso_porcentaje += 30
            else:
                diagnosticos.append("❌ Desnivel: ¡Falta trepada urgente!")
                progreso_porcentaje += 10
        else:
            progreso_porcentaje += 50 # Si es llano, damos puntaje completo

        # C. Evaluación Fisiológica (Training Effect)
        if promedio_te > 0:
            if goal.expected_te and promedio_te < (goal.expected_te - 1.5):
                diagnosticos.append(f"⚠️ Impacto: TE promedio ({round(promedio_te, 1)}) muy bajo vs la exigencia de carrera.")
            elif promedio_te >= 3.0:
                diagnosticos.append(f"✅ Impacto: Buena adaptación aeróbica (TE: {round(promedio_te, 1)}).")
            else:
                diagnosticos.append(f"ℹ️ Impacto: Mayormente regenerativo/mantenimiento (TE: {round(promedio_te, 1)}).")

        # Asignación Final de Estado
        if progreso_porcentaje >= 80:
            estado_forma, color_estado = "Óptimo", "success"
        elif progreso_porcentaje >= 50:
            estado_forma, color_estado = "Aceptable", "info"
        elif progreso_porcentaje > 0:
            estado_forma, color_estado = "Riesgo", "danger"

        context['readiness'] = {
            'acumulado_km': float(volumen_km),
            'acumulado_desnivel': int(volumen_desnivel),
            'estado': estado_forma,
            'color': color_estado,
            'porcentaje': int(progreso_porcentaje),
            'diagnosticos': diagnosticos
        }
        # 3. AUTO-MATCH CON GARMIN (Post-Carrera)
        if goal.is_completed:
            garmin_match = None
            # Buscamos si hay una actividad real registrada el mismo día del objetivo
            if goal.race_type in ['TRAIL', 'STREET']:
                garmin_match = RunActivity.objects.filter(date__date=goal.date).first()
            elif goal.race_type == 'MTB':
                garmin_match = CyclingActivity.objects.filter(date__date=goal.date).first()
            
            if garmin_match:
                context['garmin_match'] = {
                    'distancia': garmin_match.distance_km,
                    'desnivel': garmin_match.elevation_gain,
                    'te_aerobico': garmin_match.te_aerobic,
                    'fc_promedio': garmin_match.avg_heart_rate,
                }

        return context

class GoalCreateView(CreateView):
    model = RaceGoal
    form_class = RaceGoalForm
    template_name = 'objetivo_form.html' # 
    success_url = reverse_lazy('objetivos')
    
class GoalUpdateView(UpdateView):
    model = RaceGoal
    form_class = RaceGoalForm
    template_name = 'objetivo_form.html' 
    success_url = reverse_lazy('objetivos')

class GoalDeleteView(DeleteView):
    model = RaceGoal
    template_name = 'objetivo_confirm_delete.html' # Ahora creamos este
    success_url = reverse_lazy('objetivos')