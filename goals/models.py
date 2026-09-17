from django.db import models
from datetime import date
from django.utils import timezone

class RaceGoal(models.Model):
    RACE_TYPES = [
        ('TRAIL', 'Trail Running'),
        ('STREET', 'Carrera de Calle'),
        ('TRIATHLON', 'Triatlón'),
        ('MTB', 'Mountain Bike'),
    ]

    WEATHER_CHOICES = [
        ('SUNNY', '☀️ Despejado / Soleado'),
        ('CLOUDY', '☁️ Nublado'),
        ('RAIN', '🌧️ Lluvia'),
        ('SNOW', '❄️ Nieve / Frío extremo'),
    ]

    HR_ZONES = [
        ('Z1', 'Zona 1 (Regenerativo)'),
        ('Z2', 'Zona 2 (Fondo Aeróbico)'),
        ('Z3', 'Zona 3 (Tempo)'),
        ('Z4', 'Zona 4 (Umbral)'),
        ('Z5', 'Zona 5 (Máximo)'),
    ]

    # 1. DATOS GENERALES
    name = models.CharField(max_length=200, verbose_name="Nombre de la Carrera")
    race_type = models.CharField(max_length=20, choices=RACE_TYPES, verbose_name="Tipo")
    date = models.DateField(verbose_name="Fecha del Evento")
    training_start_date = models.DateField(default=timezone.now, verbose_name="Inicio del Entrenamiento")
    
    # 2. MÉTRICAS PRINCIPALES
    target_distance_km = models.FloatField(verbose_name="Distancia Total (km)")
    target_elevation_gain = models.IntegerField(default=0, verbose_name="Desnivel Positivo (+m)")
    target_pace = models.CharField(max_length=10, blank=True, null=True, verbose_name="Ritmo/Tiempo Objetivo")
    
    # 3. DESGLOSE TRIATLÓN
    swim_distance_m = models.IntegerField(default=0, blank=True, null=True, verbose_name="Natación (m)")
    swim_pace = models.CharField(max_length=10, blank=True, null=True, verbose_name="Ritmo Nado (min/100m)")
    t1_time = models.CharField(max_length=10, blank=True, null=True, verbose_name="Tiempo T1")
    bike_distance_km = models.FloatField(default=0, blank=True, null=True, verbose_name="Ciclismo (km)")
    bike_speed = models.FloatField(default=0, blank=True, null=True, verbose_name="Velocidad Bici (km/h)")
    t2_time = models.CharField(max_length=10, blank=True, null=True, verbose_name="Tiempo T2")
    run_distance_km = models.FloatField(default=0, blank=True, null=True, verbose_name="Running (km)")
    run_pace = models.CharField(max_length=10, blank=True, null=True, verbose_name="Ritmo Run (min/km)")
    
    # 4. CONDICIONES Y ESTRATEGIA (NUEVO)
    weather_condition = models.CharField(max_length=20, choices=WEATHER_CHOICES, blank=True, null=True, verbose_name="Clima Esperado")
    temperature = models.IntegerField(blank=True, null=True, verbose_name="Temperatura Estimada (°C)")
    nutrition_strategy = models.TextField(blank=True, null=True, verbose_name="Estrategia de Nutrición e Hidratación", help_text="Ej: Gel cada 45min, 500ml isotónica por hora.")
    
    # 5. FISIOLOGÍA Y READINESS (NUEVO)
    target_hr_zone = models.CharField(max_length=5, choices=HR_ZONES, blank=True, null=True, verbose_name="Zona FC Objetivo")
    expected_te = models.FloatField(blank=True, null=True, verbose_name="Training Effect Esperado (1.0 - 5.0)")

    # 6. ARCHIVOS
    gpx_file = models.FileField(upload_to='gpx_tracks/', blank=True, null=True, verbose_name="Archivo GPX")
    is_completed = models.BooleanField(default=False, verbose_name="¿Completada?")

    @property
    def elevation_per_km(self):
        if self.target_distance_km > 0:
            return round(self.target_elevation_gain / self.target_distance_km, 2)
        return 0

    @property
    def days_to_race(self):
        delta = self.date - date.today()
        return delta.days if delta.days > 0 else 0

    def __str__(self):
        return f"{self.name} ({self.date.year})"


# NUEVO MODELO: PUNTOS DE CONTROL (PAS)
class RaceCheckpoint(models.Model):
    goal = models.ForeignKey(RaceGoal, on_delete=models.CASCADE, related_name='checkpoints')
    name = models.CharField(max_length=100, verbose_name="Nombre del PAS / Control")
    km_mark = models.FloatField(verbose_name="Kilómetro")
    cut_off_time = models.TimeField(blank=True, null=True, verbose_name="Tiempo de Corte")
    
    class Meta:
        ordering = ['km_mark'] # Se ordenan solos por kilómetro

    def __str__(self):
        return f"{self.name} - Km {self.km_mark}"