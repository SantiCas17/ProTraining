from django.views.generic import TemplateView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.utils import timezone
from datetime import timedelta
from .models import DailyHealth, ErgometryTest
from .forms import ErgometryTestForm

class HealthDashboardView(TemplateView):
    template_name = 'salud_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 1. Traer los estudios médicos ordenados por fecha
        context['ergometries'] = ErgometryTest.objects.all().order_by('-date')
        
        # 2. Datos para los gráficos de Chart.js (Últimos 30 días)
        hace_30_dias = timezone.now().date() - timedelta(days=30)
        daily_health = DailyHealth.objects.filter(date__gte=hace_30_dias).order_by('date')
        
        fechas = []
        fc_reposo = []
        estres = []
        sueño = []

        for record in daily_health:
            fechas.append(record.date.strftime('%d %b'))
            fc_reposo.append(record.resting_heart_rate or 0)
            estres.append(record.stress_level or 0)
            sueño.append(record.sleep_score or 0)

        # Empaquetamos todo para mandarlo al Javascript
        context['health_chart_data'] = {
            'labels': fechas,
            'resting_hr': fc_reposo,
            'stress': estres,
            'sleep': sueño
        }
        
        return context

# ==========================================
# CRUD DE ERGOMETRÍA
# ==========================================
class ErgometryCreateView(CreateView):
    model = ErgometryTest
    form_class = ErgometryTestForm
    template_name = 'actividad_form.html' # Reciclamos el genérico porque es simple
    success_url = reverse_lazy('salud')

class ErgometryUpdateView(UpdateView):
    model = ErgometryTest
    form_class = ErgometryTestForm
    template_name = 'actividad_form.html'
    success_url = reverse_lazy('salud')

class ErgometryDeleteView(DeleteView):
    model = ErgometryTest
    template_name = 'objetivo_confirm_delete.html' # Reciclamos la pantalla de confirmación
    success_url = reverse_lazy('salud')