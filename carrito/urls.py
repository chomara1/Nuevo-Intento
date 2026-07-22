from django.urls import path
from . import views

app_name = 'carrito'

urlpatterns = [
    path('', views.ver_carrito, name='ver_carrito'),
    path('agregar/<int:producto_id>/', views.agregar_al_carrito, name='agregar_al_carrito'),
    path('comprar-ahora/<int:producto_id>/', views.comprar_ahora, name='comprar_ahora'),
    path('quitar/<int:item_id>/', views.quitar_item, name='quitar_item'),
    path('checkout/', views.checkout, name='checkout'),
    path('pagar/', views.confirmar_pago, name='confirmar_pago'),
]