from django.db import models
from datetime import timedelta

class BaseActivity(models.Model):
    class Meta:
        abstract = True

    date = models.DateTimeField(verbose_name="Fecha y Hora")
    duration = models.DurationField(default=timedelta, verbose_name="Tiempo Total")
    avg_heart_rate = models.IntegerField(null=True, blank=True, verbose_name="FC Promedio (LPM)")
    #Métricas de Impacto
    te_aerobic = models.FloatField(null=True, blank=True, verbose_name="TE Aeróbico (0-5)")
    te_anaerobic = models.FloatField(null=True, blank=True, verbose_name="TE Anaeróbico (0-5)")
    #Campo para Nutrición, dolores o mecánica
    notes = models.TextField(blank=True, null=True, verbose_name="Notas / Nutrición / Mecánica")

    def __str__(self):
        return f"{self.date.strftime('%d/%m/%Y')} - {self.__class__.__name__}"


class RunActivity(BaseActivity):
    is_trail = models.BooleanField(default=False, verbose_name="¿Es Trail?")
    distance_km = models.FloatField(verbose_name="Distancia (km)")
    elevation_gain = models.IntegerField(default=0, verbose_name="Desnivel Positivo (+m)")
    avg_pace = models.CharField(max_length=10, blank=True, null=True, verbose_name="Ritmo Promedio (min/km)")
    #Dinámica de Carrera
    cadence = models.IntegerField(null=True, blank=True, verbose_name="Cadencia (ppm)")
    stride_length = models.FloatField(null=True, blank=True, verbose_name="Longitud de Zancada (m)")
    vertical_oscillation = models.FloatField(null=True, blank=True, verbose_name="Oscilación Vertical (cm)")
    ground_contact_time = models.IntegerField(null=True, blank=True, verbose_name="Tiempo de Contacto (ms)")

class CyclingActivity(BaseActivity):
    distance_km = models.FloatField(verbose_name="Distancia (km)")
    elevation_gain = models.IntegerField(default=0, verbose_name="Desnivel Positivo (+m)")
    avg_speed = models.FloatField(blank=True, null=True, verbose_name="Velocidad Promedio (km/h)")
    avg_cadence = models.IntegerField(null=True, blank=True, verbose_name="Cadencia Promedio (ppm)")
    avg_power = models.IntegerField(null=True, blank=True, verbose_name="Potencia Promedio (Watts)")


class SwimActivity(BaseActivity):
    is_open_water = models.BooleanField(default=False, verbose_name="¿Aguas Abiertas?")
    distance_meters = models.IntegerField(verbose_name="Distancia (metros)")
    strokes = models.IntegerField(null=True, blank=True, verbose_name="Cantidad de Brazadas")
    swolf = models.IntegerField(null=True, blank=True, verbose_name="SWOLF")
    avg_pace_100m = models.CharField(max_length=10, blank=True, null=True, verbose_name="Ritmo (min/100m)")


class BikeComponent(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nombre del Repuesto")
    installed_date = models.DateField(verbose_name="Fecha de Instalación")
    max_lifespan_km = models.FloatField(verbose_name="Vida Útil Estimada (km)")
    current_mileage = models.FloatField(default=0.0, verbose_name="Kilometraje Actual")
    is_active = models.BooleanField(default=True, verbose_name="¿Está en uso?")
    
    def __str__(self):
        return self.name