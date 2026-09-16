from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date
from garmin_ingest.services import sync_garmin_by_date

class Command(BaseCommand):
    help = 'Carga histórica de Garmin (Actividades y Salud)'

    def handle(self, *args, **options):
        # Fecha de inicio estática: 1 de Enero de 2026
        start_date = date(2026, 1, 1)
        end_date = timezone.now().date()
        
        self.stdout.write(self.style.WARNING(f'Iniciando Backfill desde {start_date} hasta {end_date}... esto puede demorar un par de minutos.'))
        
        try:
            acts, health = sync_garmin_by_date(start_date, end_date)
            self.stdout.write(self.style.SUCCESS(f'¡Éxito! Se guardaron {acts} actividades y {health} días de métricas de salud.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error fatal: {e}'))