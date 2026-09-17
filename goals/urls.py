from django.urls import path
from .views import GoalDeleteView, GoalListView, GoalDetailView, GoalCreateView, GoalUpdateView

urlpatterns = [
    path('', GoalListView.as_view(), name='objetivos'),
    path('nuevo/', GoalCreateView.as_view(), name='create_goal'),
    path('<int:pk>/mapa/', GoalDetailView.as_view(), name='mapa_objetivo'),
    path('<int:pk>/editar/', GoalUpdateView.as_view(), name='update_goal'),
    path('<int:pk>/eliminar/', GoalDeleteView.as_view(), name='delete_goal'),
]