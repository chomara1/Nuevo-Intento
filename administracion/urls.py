from django.urls import path
from . import views

app_name = 'administracion'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('proveedores/<int:perfil_id>/aprobar/', views.aprobar_proveedor, name='aprobar_proveedor'),
    path('proveedores/<int:perfil_id>/rechazar/', views.rechazar_proveedor, name='rechazar_proveedor'),
    path('proveedores/lista/', views.lista_proveedores, name='lista_proveedores'),
    path('proveedores/<int:perfil_id>/productos/', views.productos_proveedor, name='productos_proveedor'),
    path('proveedores/<int:perfil_id>/eliminar/', views.eliminar_proveedor, name='eliminar_proveedor'),
    path('productos/<int:producto_id>/eliminar/', views.eliminar_producto_admin, name='eliminar_producto_admin'),
    path('diseno/', views.gestion_diseno, name='gestion_diseno'),
    path('pagos/', views.pagos, name='pagos'),
    path('pedidos/', views.pedidos, name='pedidos'),
    path('pedidos/<int:envio_id>/actualizar/', views.actualizar_estado_pedido, name='actualizar_estado_pedido'),
]