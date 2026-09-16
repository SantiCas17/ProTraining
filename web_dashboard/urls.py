from django.urls import path
from .views import ActividadesView, DashboardView

urlpatterns = [
    path('', DashboardView.as_view(), name='dashboard'),
    path('actividades/', ActividadesView.as_view(), name='actividades'),
]