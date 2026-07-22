from django.urls import path
from . import views

app_name = 'rastreo'

urlpatterns = [
    path('mis-envios/', views.lista_mis_envios, name='mis_envios'),
    path('seguimiento/<str:codigo>/', views.mi_rastreo, name='detalle'),
    path('envio/<int:envio_id>/actualizar/', views.actualizar_estado, name='actualizar'),
]