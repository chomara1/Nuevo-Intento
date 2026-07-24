from django.test import TestCase
"""
Pruebas unitarias de la app 'rastreo'.

Qué cubre este archivo:
1) EnvioModeloTests          -> Envio.subtotal() y __str__.
2) MiRastreoVistaTests       -> vista mi_rastreo (detalle de un envío propio).
3) ListaMisEnviosVistaTests  -> vista lista_mis_envios.
4) ActualizarEstadoVistaTests-> vista actualizar_estado (solo el proveedor
                                 dueño del producto puede actualizar el envío).

 
"""

from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

from .models import Envio, HistorialEstado
from inventario.models import Producto


def crear_cliente(username='cliente1'):
    return User.objects.create_user(
        username=username, email=f'{username}@test.com', password='clave123'
    )


def crear_proveedor(username='proveedor1'):
    usuario = User.objects.create_user(
        username=username, email=f'{username}@test.com', password='clave123'
    )
    usuario.perfil.rol = 'PROVEEDOR'
    usuario.perfil.aprobado = True
    usuario.perfil.save()
    return usuario


def crear_producto(proveedor, **overrides):
    datos = {
        'proveedor': proveedor,
        'nombre': 'Labial Mate',
        'descripcion': 'Larga duración',
        'precio': Decimal('15000.00'),
        'cantidad_disponible': 20,
        'esta_activo': True,
    }
    datos.update(overrides)
    return Producto.objects.create(**datos)


def crear_envio(cliente, producto, numero_guia, **overrides):
    datos = {
        'cliente': cliente,
        'producto': producto,
        'numero_guia': numero_guia,
        'cantidad': 1,
        'precio_unitario': producto.precio,
        'estado_actual': 'preparando',
    }
    datos.update(overrides)
    return Envio.objects.create(**datos)


# ---------------------------------------------------------------------------
# 1) MODELO: Envio
# ---------------------------------------------------------------------------
class EnvioModeloTests(TestCase):

    def setUp(self):
        self.cliente = crear_cliente()
        self.proveedor = crear_proveedor()
        self.producto = crear_producto(self.proveedor)

    def test_subtotal_es_cantidad_por_precio_unitario(self):
        envio = crear_envio(
            self.cliente, self.producto, 'ABC12345',
            cantidad=3, precio_unitario=Decimal('15000.00'),
        )
        self.assertEqual(envio.subtotal(), Decimal('45000.00'))

    def test_str_incluye_numero_de_guia(self):
        envio = crear_envio(self.cliente, self.producto, 'GUIA0001')
        self.assertIn('GUIA0001', str(envio))


# ---------------------------------------------------------------------------
# 2) VISTA: mi_rastreo
# ---------------------------------------------------------------------------
class MiRastreoVistaTests(TestCase):

    def setUp(self):
        self.cliente = crear_cliente()
        self.proveedor = crear_proveedor()
        self.producto = crear_producto(self.proveedor)
        self.envio = crear_envio(self.cliente, self.producto, 'MIGUIA01')
        self.client.login(username='cliente1', password='clave123')

    def test_dueno_del_envio_puede_verlo(self):
        url = reverse('rastreo:detalle', args=[self.envio.numero_guia])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['envio'], self.envio)

    def test_otro_cliente_no_puede_ver_el_envio_ajeno(self):
        crear_cliente(username='otro_cliente')
        self.client.logout()
        self.client.login(username='otro_cliente', password='clave123')

        url = reverse('rastreo:detalle', args=[self.envio.numero_guia])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_codigo_de_guia_inexistente_devuelve_404(self):
        url = reverse('rastreo:detalle', args=['NOEXISTE'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


# ---------------------------------------------------------------------------
# 3) VISTA: lista_mis_envios
# ---------------------------------------------------------------------------
class ListaMisEnviosVistaTests(TestCase):

    def setUp(self):
        self.cliente = crear_cliente()
        self.proveedor = crear_proveedor()
        self.producto = crear_producto(self.proveedor)
        self.client.login(username='cliente1', password='clave123')

    def test_solo_muestra_envios_del_cliente_logueado(self):
        crear_envio(self.cliente, self.producto, 'MIO0001')

        otro_cliente = crear_cliente(username='otro_cliente2')
        crear_envio(otro_cliente, self.producto, 'AJENO001')

        response = self.client.get(reverse('rastreo:mis_envios'))

        guias = [e.numero_guia for e in response.context['envios']]
        self.assertIn('MIO0001', guias)
        self.assertNotIn('AJENO001', guias)


# ---------------------------------------------------------------------------
# 4) VISTA: actualizar_estado
# ---------------------------------------------------------------------------
class ActualizarEstadoVistaTests(TestCase):

    def setUp(self):
        self.cliente = crear_cliente()
        self.proveedor = crear_proveedor()
        self.producto = crear_producto(self.proveedor)
        self.envio = crear_envio(self.cliente, self.producto, 'EST00001')
        self.url = reverse('rastreo:actualizar', args=[self.envio.id])

    def test_cliente_no_puede_actualizar_el_estado(self):
        self.client.login(username='cliente1', password='clave123')
        response = self.client.post(self.url, {'estado': 'en_camino'})
        self.assertEqual(response.status_code, 403)

    def test_proveedor_dueno_del_producto_puede_actualizar(self):
        self.client.login(username='proveedor1', password='clave123')
        response = self.client.post(
            self.url, {'estado': 'en_camino', 'comentario': 'Salió de bodega'}
        )

        self.assertRedirects(
            response, reverse('inventario:dashboard'), fetch_redirect_response=False
        )
        self.envio.refresh_from_db()
        self.assertEqual(self.envio.estado_actual, 'en_camino')
        self.assertEqual(self.envio.historial.count(), 1)
        self.assertEqual(self.envio.historial.first().comentario, 'Salió de bodega')

    def test_proveedor_de_otro_producto_no_puede_actualizar_este_envio(self):
        otro_proveedor = crear_proveedor(username='otro_proveedor')
        self.client.login(username='otro_proveedor', password='clave123')

        response = self.client.post(self.url, {'estado': 'en_camino'})
        self.assertEqual(response.status_code, 404)

    def test_estado_invalido_no_actualiza_el_envio(self):
        self.client.login(username='proveedor1', password='clave123')
        response = self.client.post(self.url, {'estado': 'estado_que_no_existe'})

        self.assertEqual(response.status_code, 200)  # vuelve a mostrar el form
        self.envio.refresh_from_db()
        self.assertEqual(self.envio.estado_actual, 'preparando')  # sin cambios

# Create your tests here.

# Create your tests here.
