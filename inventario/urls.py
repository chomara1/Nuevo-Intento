from django.urls import path
from . import views

app_name = 'inventario'

urlpatterns = [
    path('dashboard/', views.dashboard_proveedor, name='dashboard'),
    path('agregar/', views.agregar_producto, name='agregar'),
    path('producto/<int:producto_id>/editar/', views.editar_producto, name='editar'),
    path('producto/<int:producto_id>/eliminar/', views.eliminar_producto, name='eliminar_producto'),
    path('producto/<int:producto_id>/cambiar-estado/', views.cambiar_estado_producto, name='cambiar_estado'),
]