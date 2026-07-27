 """
Pruebas unitarias de la app 'carrito'.

Qué cubre este archivo:
1) CarritoModeloTests            -> Carrito.total() / ItemCarrito.subtotal().
2) CantidadValidaTests           -> la función auxiliar _cantidad_valida().
3) ValidarDatosEnvioTests        -> la función auxiliar _validar_datos_envio().
4) VerCarritoVistaTests          -> vista ver_carrito.
5) AgregarAlCarritoVistaTests    -> vista agregar_al_carrito (incluye AJAX).
6) ComprarAhoraVistaTests        -> vista comprar_ahora (compra directa).
7) QuitarItemVistaTests          -> vista quitar_item.
8) CheckoutVistaTests            -> vista checkout.
9) ConfirmarPagoVistaTests       -> vista confirmar_pago (la más importante:
                                     valida datos, revisa stock, descuenta
                                     inventario y genera el Envio).


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

    def test_telefono_con_menos_de_10_digitos_es_invalido(self):
        datos = {**DATOS_ENVIO_VALIDOS, 'telefono': '30012345'}
        errores = _validar_datos_envio(**datos)
        self.assertTrue(any('teléfono' in e for e in errores))

    def test_correo_sin_arroba_es_invalido(self):
        datos = {**DATOS_ENVIO_VALIDOS, 'correo': 'lauratest.com'}
        errores = _validar_datos_envio(**datos)
        self.assertTrue(any('correo' in e for e in errores))

    def test_direccion_sin_numeros_es_invalida(self):
        datos = {**DATOS_ENVIO_VALIDOS, 'direccion': 'Calle sin numero'}
        errores = _validar_datos_envio(**datos)
        self.assertTrue(any('dirección' in e for e in errores))

    def test_direccion_muy_corta_es_invalida(self):
        datos = {**DATOS_ENVIO_VALIDOS, 'direccion': 'Cl 1'}
        errores = _validar_datos_envio(**datos)
        self.assertTrue(any('dirección' in e for e in errores))

    def test_departamento_con_numeros_es_invalido(self):
        datos = {**DATOS_ENVIO_VALIDOS, 'departamento': 'Antioquia1'}
        errores = _validar_datos_envio(**datos)
        self.assertTrue(any('departamento' in e for e in errores))

    def test_ciudad_con_numeros_es_invalida(self):
        datos = {**DATOS_ENVIO_VALIDOS, 'ciudad': 'Medellin2'}
        errores = _validar_datos_envio(**datos)
        self.assertTrue(any('ciudad' in e for e in errores))

    def test_metodo_de_pago_no_soportado_es_invalido(self):
        datos = {**DATOS_ENVIO_VALIDOS, 'metodo_pago': 'bitcoin'}
        errores = _validar_datos_envio(**datos)
        self.assertTrue(any('método de pago' in e for e in errores))

    def test_varios_campos_invalidos_generan_varios_errores(self):
        datos = {**DATOS_ENVIO_VALIDOS, 'nombre': 'A1', 'telefono': '123'}
        errores = _validar_datos_envio(**datos)
        self.assertEqual(len(errores), 2)


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


# ---------------------------------------------------------------------------
# 6) VISTA: comprar_ahora (compra directa, sin pasar por el carrito)
# ---------------------------------------------------------------------------
class ComprarAhoraVistaTests(TestCase):

    def setUp(self):
        self.cliente = crear_cliente()
        self.proveedor = crear_proveedor()
        self.producto = crear_producto(self.proveedor)
        self.client.login(username='cliente1', password='clave123')
        self.url = reverse('carrito:comprar_ahora', args=[self.producto.id])

    def test_guarda_la_compra_directa_en_la_sesion_y_redirige_a_checkout(self):
        response = self.client.get(self.url, {'cantidad': '2'})

        self.assertRedirects(response, reverse('carrito:checkout'))
        compra = self.client.session['compra_directa']
        self.assertEqual(compra['producto_id'], self.producto.id)
        self.assertEqual(compra['cantidad'], 2)


# ---------------------------------------------------------------------------
# 7) VISTA: quitar_item
# ---------------------------------------------------------------------------
class QuitarItemVistaTests(TestCase):

    def setUp(self):
        self.cliente = crear_cliente()
        self.proveedor = crear_proveedor()
        self.producto = crear_producto(self.proveedor)
        self.carrito = Carrito.objects.create(cliente=self.cliente)
        self.item = ItemCarrito.objects.create(
            carrito=self.carrito, producto=self.producto, cantidad=1
        )
        self.client.login(username='cliente1', password='clave123')

    def test_quita_un_item_propio(self):
        url = reverse('carrito:quitar_item', args=[self.item.id])
        response = self.client.get(url)

        self.assertRedirects(response, reverse('carrito:ver_carrito'))
        self.assertFalse(ItemCarrito.objects.filter(id=self.item.id).exists())

    def test_no_puede_quitar_item_de_otro_cliente(self):
        otro_cliente = crear_cliente(username='otro_cliente')
        self.client.logout()
        self.client.login(username='otro_cliente', password='clave123')

        url = reverse('carrito:quitar_item', args=[self.item.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)
        self.assertTrue(ItemCarrito.objects.filter(id=self.item.id).exists())


# ---------------------------------------------------------------------------
# 8) VISTA: checkout
# ---------------------------------------------------------------------------
class CheckoutVistaTests(TestCase):

    def setUp(self):
        self.cliente = crear_cliente()
        self.proveedor = crear_proveedor()
        self.client.login(username='cliente1', password='clave123')
        self.url = reverse('carrito:checkout')

    def test_carrito_vacio_redirige_con_mensaje(self):
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse('carrito:ver_carrito'))

    def test_con_items_en_el_carrito_calcula_envio_pago(self):
        producto = crear_producto(self.proveedor, precio=Decimal('20000.00'))
        carrito = Carrito.objects.create(cliente=self.cliente)
        ItemCarrito.objects.create(carrito=carrito, producto=producto, cantidad=1)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['subtotal'], Decimal('20000.00'))
        self.assertFalse(response.context['envio_gratis'])
        self.assertEqual(response.context['costo_envio'], COSTO_ENVIO)
        self.assertEqual(response.context['total'], Decimal('20000.00') + COSTO_ENVIO)

    def test_compra_que_supera_el_minimo_tiene_envio_gratis(self):
        producto = crear_producto(self.proveedor, precio=Decimal(str(MONTO_MINIMO_ENVIO_GRATIS)))
        carrito = Carrito.objects.create(cliente=self.cliente)
        ItemCarrito.objects.create(carrito=carrito, producto=producto, cantidad=1)

        response = self.client.get(self.url)

        self.assertTrue(response.context['envio_gratis'])
        self.assertEqual(response.context['costo_envio'], 0)

    def test_compra_directa_en_sesion_se_usa_en_lugar_del_carrito(self):
        producto = crear_producto(self.proveedor, precio=Decimal('15000.00'))
        session = self.client.session
        session['compra_directa'] = {'producto_id': producto.id, 'cantidad': 3}
        session.save()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['compra_directa'])
        self.assertEqual(response.context['subtotal'], Decimal('45000.00'))


# ---------------------------------------------------------------------------
# 9) VISTA: confirmar_pago (la más completa: valida, revisa stock, descuenta
#    inventario, crea el Envio y su HistorialEstado dentro de una transacción)
# ---------------------------------------------------------------------------
class ConfirmarPagoVistaTests(TestCase):

    def setUp(self):
        self.cliente = crear_cliente()
        self.proveedor = crear_proveedor()
        self.client.login(username='cliente1', password='clave123')
        self.url = reverse('carrito:confirmar_pago')

    def _armar_carrito(self, cantidad_disponible=20, cantidad_pedida=2, precio=Decimal('20000.00')):
        producto = crear_producto(self.proveedor, cantidad_disponible=cantidad_disponible, precio=precio)
        carrito = Carrito.objects.create(cliente=self.cliente)
        ItemCarrito.objects.create(carrito=carrito, producto=producto, cantidad=cantidad_pedida)
        return producto

    def test_solo_acepta_metodo_post(self):
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse('carrito:checkout'))

    def test_pago_exitoso_crea_envio_y_descuenta_stock(self):
        producto = self._armar_carrito(cantidad_disponible=20, cantidad_pedida=2)

        response = self.client.post(self.url, DATOS_ENVIO_VALIDOS)

        self.assertRedirects(response, reverse('rastreo:mis_envios'))

        producto.refresh_from_db()
        self.assertEqual(producto.cantidad_disponible, 18)  # 20 - 2

        envio = Envio.objects.get(cliente=self.cliente)
        self.assertEqual(envio.cantidad, 2)
        self.assertEqual(envio.estado_actual, 'preparando')
        self.assertEqual(envio.historial.count(), 1)

    def test_pago_exitoso_vacia_el_carrito(self):
        producto = self._armar_carrito()
        self.client.post(self.url, DATOS_ENVIO_VALIDOS)

        carrito = Carrito.objects.get(cliente=self.cliente)
        self.assertEqual(carrito.items.count(), 0)

    def test_sin_stock_suficiente_no_crea_envio_ni_descuenta_stock(self):
        producto = self._armar_carrito(cantidad_disponible=1, cantidad_pedida=5)

        response = self.client.post(self.url, DATOS_ENVIO_VALIDOS)

        self.assertRedirects(response, reverse('carrito:checkout'))
        producto.refresh_from_db()
        self.assertEqual(producto.cantidad_disponible, 1)  # sin cambios
        self.assertFalse(Envio.objects.filter(cliente=self.cliente).exists())

    def test_producto_pausado_no_permite_comprarlo(self):
        producto = self._armar_carrito()
        producto.esta_activo = False
        producto.save()

        response = self.client.post(self.url, DATOS_ENVIO_VALIDOS)

        self.assertRedirects(response, reverse('carrito:checkout'))
        self.assertFalse(Envio.objects.filter(cliente=self.cliente).exists())

    def test_datos_de_envio_invalidos_no_generan_el_pedido(self):
        self._armar_carrito()
        datos_malos = {**DATOS_ENVIO_VALIDOS, 'telefono': '123'}

        response = self.client.post(self.url, datos_malos)

        self.assertRedirects(response, reverse('carrito:checkout'))
        self.assertFalse(Envio.objects.filter(cliente=self.cliente).exists())

    def test_campos_faltantes_muestran_error_generico(self):
        self._armar_carrito()
        datos_incompletos = {**DATOS_ENVIO_VALIDOS}
        del datos_incompletos['telefono']

        response = self.client.post(self.url, datos_incompletos)
        self.assertRedirects(response, reverse('carrito:checkout'))

        mensajes = [m.message for m in get_messages(response.wsgi_request)]
        self.assertTrue(any('completa todos los datos' in m for m in mensajes))

    def test_compra_directa_tambien_genera_envio_correctamente(self):
        producto = crear_producto(self.proveedor, cantidad_disponible=10, precio=Decimal('10000.00'))
        session = self.client.session
        session['compra_directa'] = {'producto_id': producto.id, 'cantidad': 3}
        session.save()

        response = self.client.post(self.url, DATOS_ENVIO_VALIDOS)

        self.assertRedirects(response, reverse('rastreo:mis_envios'))
        producto.refresh_from_db()
        self.assertEqual(producto.cantidad_disponible, 7)
        # la sesión de compra directa se limpia después de pagar
        self.assertNotIn('compra_directa', self.client.session)
 
# Create your tests here.
