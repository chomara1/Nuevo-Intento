from django.urls import path
from . import views
 
app_name = 'administracion'
 
urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('proveedores/<int:perfil_id>/aprobar/', views.aprobar_proveedor, name='aprobar_proveedor'),
    path('proveedores/<int:perfil_id>/rechazar/', views.rechazar_proveedor, name='rechazar_proveedor'),
    path('diseno/', views.gestion_diseno, name='gestion_diseno'),
]
 