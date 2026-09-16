from django.views.generic import TemplateView
from django.utils import timezone
from activities.models import RunActivity, CyclingActivity, SwimActivity

class DashboardView(TemplateView):
    template_name = 'dashboard.html'

class ActividadesView(TemplateView):
    template_name = 'actividades.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtenemos la fecha actual
        now = timezone.now()
        current_year = now.year
        current_month = now.month

        # Filtramos estrictamente por el mes actual
        context['runs'] = RunActivity.objects.filter(date__year=current_year, date__month=current_month).order_by('-date')
        context['rides'] = CyclingActivity.objects.filter(date__year=current_year, date__month=current_month).order_by('-date')
        context['swims'] = SwimActivity.objects.filter(date__year=current_year, date__month=current_month).order_by('-date')
        
        # Mandamos el nombre del mes para el título
        context['mes_actual'] = now.strftime("%m/%Y")
        
        return context