from django.test import TestCase
"""
Pruebas unitarias de la app 'carrito'.

Qué cubre este archivo:
1) CarritoModeloTests            -> Carrito.total() / ItemCarrito.subtotal().
2) CantidadValidaTests           -> la función auxiliar _cantidad_valida().
3) ValidarDatosEnvioTests        -> la función auxiliar _validar_datos_envio().
4) VerCarritoVistaTests          -> vista ver_carrito.
5) AgregarAlCarritoVistaTests    -> vista agregar_al_carrito (incluye AJAX).
 
"""

from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.messages import get_messages

from .models import Carrito, ItemCarrito
from .views import _cantidad_valida, _validar_datos_envio, MONTO_MINIMO_ENVIO_GRATIS, COSTO_ENVIO
from inventario.models import Producto
from rastreo.models import Envio


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
        'nombre': 'Perfume Floral',
        'descripcion': 'Fragancia de larga duración',
        'precio': Decimal('50000.00'),
        'cantidad_disponible': 20,
        'esta_activo': True,
    }
    datos.update(overrides)
    return Producto.objects.create(**datos)


DATOS_ENVIO_VALIDOS = {
    'nombre': 'Laura Gomez',
    'telefono': '3001234567',
    'correo': 'laura@test.com',
    'direccion': 'Calle 10 # 20-30',
    'departamento': 'Antioquia',
    'ciudad': 'Medellin',
    'metodo_pago': 'nequi',
}


# ---------------------------------------------------------------------------
# 1) MODELOS: Carrito.total() / ItemCarrito.subtotal()
# ---------------------------------------------------------------------------
class CarritoModeloTests(TestCase):

    def setUp(self):
        self.cliente = crear_cliente()
        self.proveedor = crear_proveedor()
        self.carrito = Carrito.objects.get_or_create(cliente=self.cliente)[0]

    def test_carrito_vacio_tiene_total_cero(self):
        self.assertEqual(self.carrito.total(), 0)

    def test_subtotal_de_un_item_es_precio_por_cantidad(self):
        producto = crear_producto(self.proveedor, precio=Decimal('10000.00'))
        item = ItemCarrito.objects.create(carrito=self.carrito, producto=producto, cantidad=3)
        self.assertEqual(item.subtotal(), Decimal('30000.00'))

    def test_total_del_carrito_suma_el_subtotal_de_todos_los_items(self):
        producto1 = crear_producto(self.proveedor, nombre='P1', precio=Decimal('10000.00'))
        producto2 = crear_producto(self.proveedor, nombre='P2', precio=Decimal('5000.00'))
        ItemCarrito.objects.create(carrito=self.carrito, producto=producto1, cantidad=2)  # 20000
        ItemCarrito.objects.create(carrito=self.carrito, producto=producto2, cantidad=4)  # 20000

        self.assertEqual(self.carrito.total(), Decimal('40000.00'))

    def test_str_item_carrito(self):
        producto = crear_producto(self.proveedor, nombre='Crema')
        item = ItemCarrito.objects.create(carrito=self.carrito, producto=producto, cantidad=2)
        self.assertEqual(str(item), '2 x Crema')


# ---------------------------------------------------------------------------
# 2) FUNCION AUXILIAR: _cantidad_valida
# ---------------------------------------------------------------------------
class CantidadValidaTests(TestCase):
    """
    Esta es una función "pura" (sin base de datos, sin request): el
    candidato ideal para probar con casos simples de entrada/salida.
    """

    def test_numero_valido_como_string_se_convierte_a_entero(self):
        self.assertEqual(_cantidad_valida('5'), 5)

    def test_numero_valido_como_entero(self):
        self.assertEqual(_cantidad_valida(3), 3)

    def test_valor_no_numerico_devuelve_1_por_defecto(self):
        self.assertEqual(_cantidad_valida('abc'), 1)

    def test_valor_none_devuelve_1_por_defecto(self):
        self.assertEqual(_cantidad_valida(None), 1)

    def test_cantidad_cero_se_normaliza_a_1(self):
        self.assertEqual(_cantidad_valida('0'), 1)

    def test_cantidad_negativa_se_normaliza_a_1(self):
        self.assertEqual(_cantidad_valida('-4'), 1)


# ---------------------------------------------------------------------------
# 3) FUNCION AUXILIAR: _validar_datos_envio
# ---------------------------------------------------------------------------
class ValidarDatosEnvioTests(TestCase):

    def test_datos_completamente_validos_no_generan_errores(self):
        errores = _validar_datos_envio(**DATOS_ENVIO_VALIDOS)
        self.assertEqual(errores, [])

    def test_nombre_con_numeros_es_invalido(self):
        datos = {**DATOS_ENVIO_VALIDOS, 'nombre': 'Laura123'}
        errores = _validar_datos_envio(**datos)
        self.assertTrue(any('nombre' in e for e in errores))

    def test_nombre_muy_corto_es_invalido(self):
        datos = {**DATOS_ENVIO_VALIDOS, 'nombre': 'Al'}
        errores = _validar_datos_envio(**datos)
        self.assertTrue(any('nombre' in e for e in errores))

    def test_telefono_que_no_empieza_en_3_es_invalido(self):
        datos = {**DATOS_ENVIO_VALIDOS, 'telefono': '6001234567'}
        errores = _validar_datos_envio(**datos)
        self.assertTrue(any('teléfono' in e for e in errores))

     

# ---------------------------------------------------------------------------
# 4) VISTA: ver_carrito
# ---------------------------------------------------------------------------
class VerCarritoVistaTests(TestCase):

    def setUp(self):
        self.cliente = crear_cliente()
        self.url = reverse('carrito:ver_carrito')

    def test_usuario_anonimo_es_redirigido_a_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_primera_visita_crea_el_carrito_automaticamente(self):
        self.assertFalse(Carrito.objects.filter(cliente=self.cliente).exists())
        self.client.login(username='cliente1', password='clave123')
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Carrito.objects.filter(cliente=self.cliente).exists())


# ---------------------------------------------------------------------------
# 5) VISTA: agregar_al_carrito
# ---------------------------------------------------------------------------
class AgregarAlCarritoVistaTests(TestCase):

    def setUp(self):
        self.cliente = crear_cliente()
        self.proveedor = crear_proveedor()
        self.producto = crear_producto(self.proveedor)
        self.client.login(username='cliente1', password='clave123')
        self.url = reverse('carrito:agregar_al_carrito', args=[self.producto.id])

    def test_agregar_producto_nuevo_crea_item_con_cantidad_1_por_defecto(self):
        self.client.get(self.url)
        carrito = Carrito.objects.get(cliente=self.cliente)
        item = carrito.items.get(producto=self.producto)
        self.assertEqual(item.cantidad, 1)

    def test_agregar_con_cantidad_especifica_respeta_esa_cantidad(self):
        self.client.get(self.url, {'cantidad': '4'})
        carrito = Carrito.objects.get(cliente=self.cliente)
        item = carrito.items.get(producto=self.producto)
        self.assertEqual(item.cantidad, 4)

    def test_agregar_el_mismo_producto_dos_veces_suma_cantidades(self):
        self.client.get(self.url, {'cantidad': '2'})
        self.client.get(self.url, {'cantidad': '3'})

        carrito = Carrito.objects.get(cliente=self.cliente)
        item = carrito.items.get(producto=self.producto)
        self.assertEqual(item.cantidad, 5)

    def test_peticion_ajax_devuelve_json(self):
        response = self.client.get(
            self.url, HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['total_items'], 1)

    def test_peticion_normal_redirige(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_producto_inexistente_devuelve_404(self):
        url = reverse('carrito:agregar_al_carrito', args=[9999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


 
# Create your tests here.
