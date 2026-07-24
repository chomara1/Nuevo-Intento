from django.test import TestCase
"""
Pruebas unitarias de la app 'administracion'.

Qué cubre este archivo:
1) DisenoSitioModeloTests        -> el modelo "singleton" DisenoSitio.
2) DashboardVistaTests           -> vista dashboard.
3) AprobarRechazarProveedorTests -> vistas aprobar_proveedor / rechazar_proveedor.
4) ListaYProductosProveedorTests -> lista_proveedores / productos_proveedor.
5) EliminarProveedorYProductoTests -> eliminar_proveedor / eliminar_producto_admin.
6) GestionDisenoVistaTests       -> vista gestion_diseno (formulario del carrusel).
7) PagosYPedidosVistaTests       -> pagos / pedidos / actualizar_estado_pedido.

 
from decimal import Decimal

from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.contrib.auth.models import User, AnonymousUser
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware

from .models import DisenoSitio
from .decorators import admin_required
from inventario.models import Producto
from rastreo.models import Envio


def crear_admin(username='admin1'):
    usuario = User.objects.create_user(
        username=username, email=f'{username}@test.com', password='clave123'
    )
    usuario.perfil.rol = 'ADMIN'
    usuario.perfil.save()
    return usuario


def crear_proveedor(username='proveedor1', aprobado=False):
    usuario = User.objects.create_user(
        username=username, email=f'{username}@test.com', password='clave123'
    )
    usuario.perfil.rol = 'PROVEEDOR'
    usuario.perfil.aprobado = aprobado
    usuario.perfil.save()
    return usuario


def crear_cliente(username='cliente1'):
    return User.objects.create_user(
        username=username, email=f'{username}@test.com', password='clave123'
    )


def crear_producto(proveedor, **overrides):
    datos = {
        'proveedor': proveedor,
        'nombre': 'Base Líquida',
        'descripcion': 'Cobertura media',
        'precio': Decimal('40000.00'),
        'cantidad_disponible': 20,
        'esta_activo': True,
    }
    datos.update(overrides)
    return Producto.objects.create(**datos)


# ---------------------------------------------------------------------------
# 1) MODELO: DisenoSitio (singleton)
# ---------------------------------------------------------------------------
class DisenoSitioModeloTests(TestCase):

    def test_cargar_crea_el_registro_si_no_existe(self):
        self.assertEqual(DisenoSitio.objects.count(), 0)
        diseno = DisenoSitio.cargar()
        self.assertEqual(diseno.pk, 1)
        self.assertEqual(DisenoSitio.objects.count(), 1)

    def test_cargar_devuelve_siempre_el_mismo_registro(self):
        primero = DisenoSitio.cargar()
        primero.slide1_titulo = 'Título editado'
        primero.save()

        segundo = DisenoSitio.cargar()
        self.assertEqual(segundo.pk, 1)
        self.assertEqual(segundo.slide1_titulo, 'Título editado')
        self.assertEqual(DisenoSitio.objects.count(), 1)

    def test_guardar_una_instancia_nueva_fuerza_pk_1(self):
        diseno = DisenoSitio(slide1_titulo='Otro título')
        diseno.save()
        self.assertEqual(diseno.pk, 1)

    def test_intentar_guardar_una_segunda_instancia_sobrescribe_la_primera(self):
        DisenoSitio.objects.create(slide1_titulo='Primero')
        DisenoSitio.objects.create(slide1_titulo='Segundo')

        self.assertEqual(DisenoSitio.objects.count(), 1)
        self.assertEqual(DisenoSitio.objects.get(pk=1).slide1_titulo, 'Segundo')

    def test_delete_no_borra_el_registro(self):
        diseno = DisenoSitio.cargar()
        diseno.delete()
        self.assertTrue(DisenoSitio.objects.filter(pk=1).exists())



# ---------------------------------------------------------------------------
# 3) VISTA: dashboard
# ---------------------------------------------------------------------------
class DashboardVistaTests(TestCase):

    def setUp(self):
        self.admin = crear_admin()
        self.url = reverse('administracion:dashboard')

    def test_no_admin_no_puede_entrar(self):
        crear_cliente()
        self.client.login(username='cliente1', password='clave123')
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse('usuarios:tienda_home'))

    def test_admin_ve_proveedores_pendientes_de_aprobacion(self):
        crear_proveedor(username='pendiente1', aprobado=False)
        crear_proveedor(username='aprobado1', aprobado=True)

        self.client.login(username='admin1', password='clave123')
        response = self.client.get(self.url)

        usernames = [p.usuario.username for p in response.context['proveedores_pendientes']]
        self.assertIn('pendiente1', usernames)
        self.assertNotIn('aprobado1', usernames)


# ---------------------------------------------------------------------------
# 4) VISTAS: aprobar_proveedor / rechazar_proveedor
# ---------------------------------------------------------------------------
class AprobarRechazarProveedorVistaTests(TestCase):

    def setUp(self):
        self.admin = crear_admin()
        self.proveedor = crear_proveedor(username='pendiente2', aprobado=False)
        self.client.login(username='admin1', password='clave123')

    def test_aprobar_proveedor_marca_aprobado_true(self):
        url = reverse('administracion:aprobar_proveedor', args=[self.proveedor.perfil.id])
        response = self.client.get(url)

        self.assertRedirects(response, reverse('administracion:dashboard'))
        self.proveedor.perfil.refresh_from_db()
        self.assertTrue(self.proveedor.perfil.aprobado)

    def test_rechazar_proveedor_elimina_el_usuario(self):
        url = reverse('administracion:rechazar_proveedor', args=[self.proveedor.perfil.id])
        response = self.client.get(url)

        self.assertRedirects(response, reverse('administracion:dashboard'))
        self.assertFalse(User.objects.filter(username='pendiente2').exists())


# ---------------------------------------------------------------------------
# 5) VISTAS: lista_proveedores / productos_proveedor
# ---------------------------------------------------------------------------
class ListaYProductosProveedorVistaTests(TestCase):

    def setUp(self):
        self.admin = crear_admin()
        self.proveedor = crear_proveedor(username='prov_lista', aprobado=True)
        self.client.login(username='admin1', password='clave123')

    def test_lista_proveedores_incluye_conteo_de_productos(self):
        crear_producto(self.proveedor, nombre='P1')
        crear_producto(self.proveedor, nombre='P2')

        response = self.client.get(reverse('administracion:lista_proveedores'))
        proveedores = list(response.context['proveedores'])
        perfil_encontrado = next(p for p in proveedores if p.usuario == self.proveedor)
        self.assertEqual(perfil_encontrado.total_productos, 2)

    def test_productos_proveedor_muestra_solo_los_de_ese_proveedor(self):
        crear_producto(self.proveedor, nombre='Propio')
        otro_proveedor = crear_proveedor(username='otro_prov', aprobado=True)
        crear_producto(otro_proveedor, nombre='Ajeno')

        url = reverse('administracion:productos_proveedor', args=[self.proveedor.perfil.id])
        response = self.client.get(url)

        nombres = [p.nombre for p in response.context['productos']]
        self.assertIn('Propio', nombres)
        self.assertNotIn('Ajeno', nombres)


# ---------------------------------------------------------------------------
# 6) VISTAS: eliminar_proveedor / eliminar_producto_admin
# ---------------------------------------------------------------------------
class EliminarProveedorYProductoVistaTests(TestCase):

    def setUp(self):
        self.admin = crear_admin()
        self.proveedor = crear_proveedor(username='prov_borrar', aprobado=True)
        self.client.login(username='admin1', password='clave123')

    def test_eliminar_proveedor_borra_tambien_sus_productos(self):
        crear_producto(self.proveedor, nombre='Producto a borrar')
        url = reverse('administracion:eliminar_proveedor', args=[self.proveedor.perfil.id])

        response = self.client.get(url)

        self.assertRedirects(response, reverse('administracion:lista_proveedores'))
        self.assertFalse(User.objects.filter(username='prov_borrar').exists())
        self.assertEqual(Producto.objects.filter(nombre='Producto a borrar').count(), 0)

    def test_eliminar_producto_puntual_no_afecta_al_proveedor(self):
        producto = crear_producto(self.proveedor, nombre='Solo este')
        url = reverse('administracion:eliminar_producto_admin', args=[producto.id])

        response = self.client.get(url)

        self.assertRedirects(
            response,
            reverse('administracion:productos_proveedor', args=[self.proveedor.perfil.id]),
        )
        self.assertFalse(Producto.objects.filter(id=producto.id).exists())
        self.assertTrue(User.objects.filter(username='prov_borrar').exists())


# ---------------------------------------------------------------------------
# 7) VISTA: gestion_diseno
# ---------------------------------------------------------------------------
class GestionDisenoVistaTests(TestCase):

    def setUp(self):
        self.admin = crear_admin()
        self.client.login(username='admin1', password='clave123')
        self.url = reverse('administracion:gestion_diseno')

    def test_get_muestra_formulario_con_valores_actuales(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)

    def test_post_valido_actualiza_el_diseno(self):
        datos = {
            'slide1_titulo': 'Nuevo título 1', 'slide1_texto': 'texto 1',
            'slide1_color_a': '#111111', 'slide1_color_b': '#222222',
            'slide2_titulo': 'Nuevo título 2', 'slide2_texto': 'texto 2',
            'slide2_color_a': '#333333', 'slide2_color_b': '#444444',
            'slide3_titulo': 'Nuevo título 3', 'slide3_texto': 'texto 3',
            'slide3_color_a': '#555555', 'slide3_color_b': '#666666',
        }
        response = self.client.post(self.url, datos)

        self.assertRedirects(response, self.url)
        diseno = DisenoSitio.cargar()
        self.assertEqual(diseno.slide1_titulo, 'Nuevo título 1')
        self.assertEqual(diseno.slide2_color_a, '#333333')


# ---------------------------------------------------------------------------
# 8) VISTAS: pagos / pedidos / actualizar_estado_pedido
# ---------------------------------------------------------------------------
class PagosYPedidosVistaTests(TestCase):

    def setUp(self):
        self.admin = crear_admin()
        self.cliente = crear_cliente()
        self.proveedor = crear_proveedor(username='prov_pedidos', aprobado=True)
        self.producto = crear_producto(self.proveedor)
        self.client.login(username='admin1', password='clave123')

    def _crear_envio(self, numero_guia, estado_actual='preparando'):
        return Envio.objects.create(
            cliente=self.cliente,
            producto=self.producto,
            numero_guia=numero_guia,
            cantidad=1,
            precio_unitario=self.producto.precio,
            estado_actual=estado_actual,
        )

    def test_pagos_excluye_los_envios_cancelados(self):
        self._crear_envio('PAGO0001', estado_actual='preparando')
        self._crear_envio('PAGO0002', estado_actual='cancelado')

        response = self.client.get(reverse('administracion:pagos'))
        guias = [p.numero_guia for p in response.context['pagos']]
        self.assertIn('PAGO0001', guias)
        self.assertNotIn('PAGO0002', guias)

    def test_pedidos_incluye_todos_los_estados(self):
        self._crear_envio('PED0001', estado_actual='preparando')
        self._crear_envio('PED0002', estado_actual='cancelado')

        response = self.client.get(reverse('administracion:pedidos'))
        guias = [p.numero_guia for p in response.context['pedidos']]
        self.assertIn('PED0001', guias)
        self.assertIn('PED0002', guias)

    def test_actualizar_estado_pedido_cambia_el_estado_y_registra_historial(self):
        envio = self._crear_envio('UPD0001')
        url = reverse('administracion:actualizar_estado_pedido', args=[envio.id])

        response = self.client.post(url, {'estado_actual': 'entregado'})

        self.assertRedirects(response, reverse('administracion:pedidos'))
        envio.refresh_from_db()
        self.assertEqual(envio.estado_actual, 'entregado')
        self.assertEqual(envio.historial.count(), 1)

    def test_estado_invalido_no_actualiza_el_pedido(self):
        envio = self._crear_envio('UPD0002')
        url = reverse('administracion:actualizar_estado_pedido', args=[envio.id])

        response = self.client.post(url, {'estado_actual': 'no_existe'})

        self.assertRedirects(response, reverse('administracion:pedidos'))
        envio.refresh_from_db()
        self.assertEqual(envio.estado_actual, 'preparando')
# Create your tests here.
