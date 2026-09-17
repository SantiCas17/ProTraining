from django.shortcuts import redirect
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from .services import sync_garmin_by_date

def trigger_garmin_sync(request):
    try:
        # 1. Calculamos la última semana para que la web responda rápido
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=7)
        
        # 2. Llamamos a tu motor ETL
        saved_acts, saved_health = sync_garmin_by_date(start_date, end_date)
        
        # 3. Avisamos al usuario
        if saved_acts > 0 or saved_health > 0:
            messages.success(request, f"¡Sincronización exitosa! Nuevas actividades: {saved_acts} | Métricas de salud: {saved_health}.")
        else:
            messages.info(request, "Tu historial de los últimos 7 días ya estaba al día. No hay datos nuevos.")
            
    except Exception as e:
        messages.error(request, f"Error al sincronizar con Garmin: {str(e)}")
        
    return redirect('dashboard')