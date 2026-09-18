import os
import time
from garminconnect import Garmin
from dotenv import load_dotenv
from datetime import timedelta
from django.utils.dateparse import parse_datetime
from tqdm import tqdm
from activities.models import RunActivity, CyclingActivity, SwimActivity
from health.models import DailyHealth

#variables .env
load_dotenv()

def get_garmin_client():
    """Inicializa y autentica el cliente de Garmin Connect."""
    email = os.getenv("GARMIN_EMAIL")
    password = os.getenv("GARMIN_PASSWORD")
    
    if not email or not password:
        raise ValueError("⚠️ Faltan las credenciales de Garmin en el archivo .env")

    try:
        #Inicializamos el cliente
        client = Garmin(email, password)
        client.login()
        return client
    except Exception as e:
        raise ConnectionError(f"Error al conectar con Garmin: {e}")
    
def sync_garmin_by_date(start_date, end_date):
    """Descarga actividades y métricas de salud en un rango de fechas."""
    client = get_garmin_client()
    saved_acts = 0
    saved_health = 0
    
    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')
    
    #ACTIVIDADES
    try:
        activities = client.get_activities_by_date(start_str, end_str, '')
        for act in activities:
            act_type = act.get('activityType', {}).get('typeKey', '')
            start_time = parse_datetime(act.get('startTimeLocal'))
            duration = timedelta(seconds=act.get('duration', 0))
            distance_km = act.get('distance', 0) / 1000
            elevation_gain = int(act.get('elevationGain', 0))
            
            # Running
            if act_type in ['running', 'trail_running']:
                if not RunActivity.objects.filter(date=start_time).exists():
                    RunActivity.objects.create(
                        date=start_time, duration=duration, distance_km=distance_km,
                        elevation_gain=elevation_gain, is_trail=(act_type == 'trail_running'),
                        avg_heart_rate=act.get('averageHR'), te_aerobic=act.get('aerobicTrainingEffect'),
                        te_anaerobic=act.get('anaerobicTrainingEffect'),
                        cadence=act.get('averageRunningCadenceInStepsPerMinute'),
                        stride_length=act.get('avgStrideLength'),
                        vertical_oscillation=act.get('avgVerticalOscillation'),
                        ground_contact_time=act.get('avgGroundContactTime')
                    )
                    saved_acts += 1
            # Ciclismo
            elif act_type == 'cycling':
                if not CyclingActivity.objects.filter(date=start_time).exists():
                    CyclingActivity.objects.create(
                        date=start_time, duration=duration, distance_km=distance_km,
                        elevation_gain=elevation_gain, avg_speed=act.get('averageSpeed', 0) * 3.6,
                        avg_heart_rate=act.get('averageHR'), te_aerobic=act.get('aerobicTrainingEffect'),
                        te_anaerobic=act.get('anaerobicTrainingEffect'),
                        avg_cadence=act.get('averageBikingCadenceInRevPerMinute')
                    )
                    saved_acts += 1
            # Natación
            elif act_type in ['lap_swimming', 'open_water_swimming']:
                if not SwimActivity.objects.filter(date=start_time).exists():
                    SwimActivity.objects.create(
                        date=start_time, duration=duration, distance_meters=int(act.get('distance', 0)),
                        is_open_water=(act_type == 'open_water_swimming'),
                        avg_heart_rate=act.get('averageHR'), strokes=act.get('averageStrokes'),
                        swolf=act.get('averageSWOLF')
                    )
                    saved_acts += 1
    except Exception as e:
        print(f"Error descargando actividades: {e}")

    #SALUD
    delta_days = (end_date - start_date).days + 1
    current_date = start_date
    
    print("\nProcesando métricas diarias de Salud (Garmin API):")
    
    #rango de días
    for _ in tqdm(range(delta_days), desc="Progreso", unit="día"):
        d_str = current_date.isoformat()
        try:
            stats = client.get_stats(d_str)
            sleep = client.get_sleep_data(d_str)
            
            sleep_score = None
            if sleep and 'dailySleepDTO' in sleep:
                dto = sleep['dailySleepDTO']
                # Formato viejo
                if 'sleepScore' in dto and isinstance(dto['sleepScore'], dict):
                    sleep_score = dto['sleepScore'].get('value')
                # Formato nuevo
                elif 'sleepScores' in dto and 'overall' in dto['sleepScores']:
                    sleep_score = dto['sleepScores']['overall'].get('value')
                # Formato directo
                elif 'sleepScore' in dto and isinstance(dto['sleepScore'], (int, float)):
                    sleep_score = dto['sleepScore']
                    
            DailyHealth.objects.update_or_create(
                date=current_date,
                defaults={
                    'resting_heart_rate': stats.get('restingHeartRate'),
                    'stress_level': stats.get('averageStressLevel'),
                    'sleep_score': sleep_score
                }
            )
            saved_health += 1
        except Exception as e:
            print(f"Error procesando salud para {d_str}: {e}")
            
        current_date += timedelta(days=1)
        time.sleep(0.5) 
        
    return saved_acts, saved_health