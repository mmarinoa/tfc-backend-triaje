from django.urls import path
from . import views

urlpatterns = [
    path('auth/register/', views.register_view, name='register'),
    path('auth/login/', views.login_view, name='login'),

    path('consultas/', views.consultas_view, name='consultas'),
    path('consultas/<int:consulta_id>/', views.consulta_detail_view, name='consulta_detail'),
    path('panel/consultas/', views.panel_medico_view, name='panel_medico'),
    path('api/panel/consultas/<int:consulta_id>/atender/', views.panel_marcar_atendida_view, name='panel_marcar_atendida'),
]