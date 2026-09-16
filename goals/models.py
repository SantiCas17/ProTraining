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

    name = models.CharField(max_length=200, verbose_name="Nombre de la Carrera")
    race_type = models.CharField(max_length=20, choices=RACE_TYPES, verbose_name="Tipo")
    date = models.DateField(verbose_name="Fecha del Evento")
    
    # NUEVO: El punto de partida para el cálculo de Readiness
    training_start_date = models.DateField(default=timezone.now, verbose_name="Inicio del Entrenamiento")
    
    target_distance_km = models.FloatField(verbose_name="Distancia (km)")
    target_elevation_gain = models.IntegerField(default=0, verbose_name="Desnivel Positivo (+m)")
    target_pace = models.CharField(max_length=10, blank=True, null=True, verbose_name="Ritmo/Tiempo Objetivo")
    
    gpx_file = models.FileField(upload_to='gpx_tracks/', blank=True, null=True, verbose_name="Archivo GPX")
    is_completed = models.BooleanField(default=False, verbose_name="¿Completada?")

    @property
    def elevation_per_km(self):
        if self.target_distance_km > 0:
            return round(self.target_elevation_gain / self.target_distance_km, 2)
        return 0

    @property
    def days_to_race(self):
        """días restantes hasta la carrera"""
        delta = self.date - date.today()
        return delta.days if delta.days > 0 else 0

    def __str__(self):
        return f"{self.name} ({self.date.year})"