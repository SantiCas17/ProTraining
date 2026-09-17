from django.urls import path
from .views import HealthDashboardView, ErgometryCreateView, ErgometryUpdateView, ErgometryDeleteView

urlpatterns = [
    path('', HealthDashboardView.as_view(), name='salud'),
    path('ergometria/nueva/', ErgometryCreateView.as_view(), name='create_ergometry'),
    path('ergometria/<int:pk>/editar/', ErgometryUpdateView.as_view(), name='update_ergometry'),
    path('ergometria/<int:pk>/eliminar/', ErgometryDeleteView.as_view(), name='delete_ergometry'),
]