from django.db import models

class ErgometryTest(models.Model):
    """Historial de chequeos médicos y actualización de Zonas HR"""
    date = models.DateField(verbose_name="Fecha del Estudio")
    doctor_or_clinic = models.CharField(max_length=200, blank=True, null=True, verbose_name="Doctor / Institución")
    
    #Biometría
    weight_kg = models.FloatField(verbose_name="Peso (kg)")
    height_cm = models.FloatField(default=173, verbose_name="Altura (cm)")
    
    #Zonas HR
    z1_min = models.IntegerField(default=127, verbose_name="Z1 Min (Regenerativo)")
    z1_max = models.IntegerField(default=141, verbose_name="Z1 Max")
    z2_min = models.IntegerField(default=142, verbose_name="Z2 Min (Aeróbico)")
    z2_max = models.IntegerField(default=154, verbose_name="Z2 Max")
    z3_min = models.IntegerField(default=155, verbose_name="Z3 Min (Umbral)")
    z3_max = models.IntegerField(default=169, verbose_name="Z3 Max")
    z4_min = models.IntegerField(default=170, verbose_name="Z4 Min (Anaeróbico)")
    z4_max = models.IntegerField(default=182, verbose_name="Z4 Max")
    z5_min = models.IntegerField(default=183, verbose_name="Z5 Min (Máximo)")
    z5_max = models.IntegerField(default=198, verbose_name="Z5 Max")

    notes = models.TextField(blank=True, null=True, verbose_name="Conclusiones / Notas del Médico")

    @property
    def imc(self):
        """Calcula el Índice de Masa Corporal (IMC) del día del estudio"""
        if self.height_cm > 0:
            height_m = self.height_cm / 100
            return round(self.weight_kg / (height_m ** 2), 2)
        return 0

    def __str__(self):
        return f"Ergometría del {self.date.strftime('%d/%m/%Y')} - {self.doctor_or_clinic}"
    @property
    def imc_status(self):
        """Evalúa la situación del peso según la OMS"""
        val = self.imc
        if val == 0: return "Sin datos"
        if val < 18.5: return "Bajo Peso"
        if val <= 24.9: return "Peso Normal"
        if val <= 29.9: return "Sobrepeso"
        return "Obesidad"

    @property
    def imc_color(self):
        """Asigna un color para la interfaz según el estado"""
        val = self.imc
        if 18.5 <= val <= 24.9: return "text-success"
        if val > 0 and (val < 18.5 or val <= 29.9): return "text-warning"
        return "text-danger"

    @property
    def ideal_weight_range(self):
        """Calcula el rango de peso ideal basado en la altura"""
        if self.height_cm > 0:
            height_m = self.height_cm / 100
            min_w = round(18.5 * (height_m ** 2), 1)
            max_w = round(24.9 * (height_m ** 2), 1)
            return f"{min_w} - {max_w} kg"
        return "-"


class DailyHealth(models.Model):
    """Historial diario. Sse arma la curva de peso, estrés y sueño"""
    date = models.DateField(unique=True, verbose_name="Fecha")
    weight_kg = models.FloatField(null=True, blank=True, verbose_name="Peso Diario (kg)")
    resting_heart_rate = models.IntegerField(null=True, blank=True, verbose_name="FC Reposo (LPM)")
    sleep_score = models.IntegerField(null=True, blank=True, verbose_name="Puntuación de Sueño (0-100)")
    stress_level = models.IntegerField(null=True, blank=True, verbose_name="Nivel de Estrés (0-100)")
    notes = models.TextField(blank=True, null=True, verbose_name="Notas (Ej: dolor de garganta, cansancio extremo)")

    def __str__(self):
        return f"Salud - {self.date.strftime('%d/%m/%Y')}"