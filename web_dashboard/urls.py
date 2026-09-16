from django.urls import path
from .views import (DashboardView, ActividadesView, 
                    RunCreateView, RunUpdateView, RunDeleteView,
                    BikeCreateView, BikeUpdateView, BikeDeleteView,
                    SwimCreateView, SwimUpdateView, SwimDeleteView)

urlpatterns = [
    path('', DashboardView.as_view(), name='dashboard'),
    path('actividades/', ActividadesView.as_view(), name='actividades'),
    path('run/nueva/', RunCreateView.as_view(), name='create_run'),
    path('run/<int:pk>/editar/', RunUpdateView.as_view(), name='edit_run'),
    path('run/<int:pk>/eliminar/', RunDeleteView.as_view(), name='delete_run'),
    path('bike/nueva/', BikeCreateView.as_view(), name='create_bike'),
    path('bike/<int:pk>/editar/', BikeUpdateView.as_view(), name='edit_bike'),
    path('bike/<int:pk>/eliminar/', BikeDeleteView.as_view(), name='delete_bike'),
    path('swim/nueva/', SwimCreateView.as_view(), name='create_swim'),
    path('swim/<int:pk>/editar/', SwimUpdateView.as_view(), name='edit_swim'),
    path('swim/<int:pk>/eliminar/', SwimDeleteView.as_view(), name='delete_swim'),
]