from django.urls import path
from .views import trigger_garmin_sync

urlpatterns = [
    path('sync/', trigger_garmin_sync, name='garmin_sync'),
]