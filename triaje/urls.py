from django.urls import path
from . import views

urlpatterns = [
    path('consultas/', views.consultas_view, name='consultas'),
    path('consultas/<int:consulta_id>/', views.consulta_detail_view, name='consulta_detail'),
]