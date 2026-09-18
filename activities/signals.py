from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CyclingActivity, BikeComponent

@receiver(post_save, sender=CyclingActivity)
def update_bike_components(sender, instance, created, **kwargs):
    """
    suma los kilómetros a los componentes activos de la bici
    """
    if created:  #suma solo si es una actividad nueva, no si la estamos editando
        active_components = BikeComponent.objects.filter(is_active=True)
        for component in active_components:
            component.current_mileage += instance.distance_km
            component.save()