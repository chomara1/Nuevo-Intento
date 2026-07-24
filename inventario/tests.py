from django.test import TestCase
"""
Pruebas unitarias de la app 'inventario'.

Qué cubre este archivo:
1) CategoriaModelTests        -> __str__ del modelo Categoria.
2) ProductoModelTests         -> la property es_nuevo del modelo Producto.
3) ProductoFormTests          -> la validación clean_cantidad_disponible.
4) DashboardProveedorTests    -> vista dashboard_proveedor.
5) AgregarProductoVistaTests  -> vista agregar_producto.
6) EditarProductoVistaTests   -> vista editar_producto.
7) EliminarProductoVistaTests -> vista eliminar_producto.
8) CambiarEstadoVistaTests    -> vista cambiar_estado_producto.

 
"""

from decimal import Decimal
from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone

from .models import Categoria, Producto
from .forms import ProductoForm, CANTIDAD_MINIMA_PUBLICACION


def crear_proveedor(username='proveedor1'):
    """Helper reutilizable: crea un User cuyo Perfil tiene rol PROVEEDOR."""
    usuario = User.objects.create_user(
        username=username, email=f'{username}@test.com', password='clave123'
    )
    usuario.perfil.rol = 'PROVEEDOR'
    usuario.perfil.aprobado = True
    usuario.perfil.save()
    return usuario


def crear_producto(proveedor, **overrides):
    """Helper: crea un Producto con valores por defecto razonables."""
    datos = {
        'proveedor': proveedor,
        'nombre': 'Shampoo Reparador',
        'descripcion': 'Shampoo para cabello dañado',
        'precio': Decimal('25000.00'),
        'cantidad_disponible': 20,
        'esta_activo': True,
    }
    datos.update(overrides)
    return Producto.objects.create(**datos)


# ---------------------------------------------------------------------------
# 1) MODELO: Categoria
# ---------------------------------------------------------------------------
class CategoriaModelTests(TestCase):

    def test_str_sin_categoria_padre_devuelve_solo_el_nombre(self):
        categoria = Categoria.objects.create(nombre='Cuidado del cabello')
        self.assertEqual(str(categoria), 'Cuidado del cabello')

    def test_str_con_categoria_padre_incluye_la_jerarquia(self):
        padre = Categoria.objects.create(nombre='Cuidado del cabello')
        hija = Categoria.objects.create(nombre='Shampoos', categoria_padre=padre)
        self.assertEqual(str(hija), 'Cuidado del cabello → Shampoos')


# ---------------------------------------------------------------------------
# 2) MODELO: Producto (property es_nuevo)
# ---------------------------------------------------------------------------
class ProductoModelTests(TestCase):

    def setUp(self):
        self.proveedor = crear_proveedor()

    def test_producto_recien_creado_es_nuevo(self):
        producto = crear_producto(self.proveedor)
        self.assertTrue(producto.es_nuevo)

    def test_producto_deja_de_ser_nuevo_tras_pasar_horas_limite(self):
        producto = crear_producto(self.proveedor)

        # fecha_creacion tiene auto_now_add=True, así que no se puede pasar
        # por el constructor ni por producto.save(). Para simular que el
        # producto se creó hace tiempo, se actualizo la fecha directamente
        # en la base de datos con .update(), que sí ignora auto_now_add.
        fecha_vieja = timezone.now() - timedelta(hours=Producto.HORAS_LIMITE_NUEVO + 1)
        Producto.objects.filter(pk=producto.pk).update(fecha_creacion=fecha_vieja)
        producto.refresh_from_db()

        self.assertFalse(producto.es_nuevo)

    

# ---------------------------------------------------------------------------
# 3) FORM: ProductoForm.clean_cantidad_disponible
# ---------------------------------------------------------------------------
class ProductoFormTests(TestCase):

    def setUp(self):
        self.proveedor = crear_proveedor()
        self.datos_base = {
            'nombre': 'Acondicionador',
            'marca': 'MarcaX',
            'descripcion': 'Acondicionador hidratante',
            'precio': '18000',
            'cantidad_disponible': 20,
        }

    def test_producto_nuevo_con_menos_del_minimo_es_invalido(self):
        datos = {**self.datos_base, 'cantidad_disponible': CANTIDAD_MINIMA_PUBLICACION - 1}
        form = ProductoForm(data=datos)
        self.assertFalse(form.is_valid())
        self.assertIn('cantidad_disponible', form.errors)

    def test_producto_nuevo_con_exactamente_el_minimo_es_valido(self):
        datos = {**self.datos_base, 'cantidad_disponible': CANTIDAD_MINIMA_PUBLICACION}
        form = ProductoForm(data=datos)
        self.assertTrue(form.is_valid(), form.errors)

    def test_producto_nuevo_con_mas_del_minimo_es_valido(self):
        form = ProductoForm(data=self.datos_base)
        self.assertTrue(form.is_valid(), form.errors)

    def test_editar_producto_existente_permite_cantidad_menor_al_minimo(self):
        """
        clean_cantidad_disponible solo exige el mínimo cuando
        self.instance.pk is None (producto nuevo). Al editar (instance ya
        tiene pk) la regla no debe aplicar.
        """
        producto = crear_producto(self.proveedor, cantidad_disponible=20)
        datos = {**self.datos_base, 'cantidad_disponible': 2}
        form = ProductoForm(data=datos, instance=producto)
        self.assertTrue(form.is_valid(), form.errors)


# ---------------------------------------------------------------------------
# 4) VISTA: dashboard_proveedor
# ---------------------------------------------------------------------------
class DashboardProveedorVistaTests(TestCase):

    def setUp(self):
        self.proveedor = crear_proveedor()
        self.url = reverse('inventario:dashboard')

    def test_usuario_anonimo_es_redirigido_a_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_usuario_que_no_es_proveedor_es_redirigido(self):
        cliente = User.objects.create_user(
            username='soycliente', email='soycliente@test.com', password='clave123'
        )
        self.client.login(username='soycliente', password='clave123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_proveedor_ve_su_propio_inventario(self):
        crear_producto(self.proveedor, nombre='Producto propio')
        otro_proveedor = crear_proveedor(username='otro')
        crear_producto(otro_proveedor, nombre='Producto ajeno')

        self.client.login(username='proveedor1', password='clave123')
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        nombres = [p.nombre for p in response.context['inventario']]
        self.assertIn('Producto propio', nombres)
        self.assertNotIn('Producto ajeno', nombres)

    def test_productos_con_stock_bajo_aparecen_en_su_lista(self):
        crear_producto(self.proveedor, nombre='Con poco stock', cantidad_disponible=3)
        crear_producto(self.proveedor, nombre='Con stock normal', cantidad_disponible=50)

        self.client.login(username='proveedor1', password='clave123')
        response = self.client.get(self.url)

        nombres_stock_bajo = [p.nombre for p in response.context['productos_stock_bajo']]
        self.assertIn('Con poco stock', nombres_stock_bajo)
        self.assertNotIn('Con stock normal', nombres_stock_bajo)


# ---------------------------------------------------------------------------
# 5) VISTA: agregar_producto
# ---------------------------------------------------------------------------
class AgregarProductoVistaTests(TestCase):

    def setUp(self):
        self.proveedor = crear_proveedor()
        self.url = reverse('inventario:agregar')
        self.client.login(username='proveedor1', password='clave123')

    def test_post_valido_crea_producto_asignado_al_proveedor_logueado(self):
        datos = {
            'nombre': 'Mascarilla Capilar',
            'marca': 'MarcaY',
            'descripcion': 'Hidratación profunda',
            'precio': '32000',
            'cantidad_disponible': 20,
        }
        response = self.client.post(self.url, datos)

        self.assertRedirects(
            response, reverse('inventario:dashboard'), fetch_redirect_response=False
        )
        producto = Producto.objects.get(nombre='Mascarilla Capilar')
        self.assertEqual(producto.proveedor, self.proveedor)

    def test_post_con_cantidad_insuficiente_no_crea_producto(self):
        datos = {
            'nombre': 'Producto Chico',
            'descripcion': 'desc',
            'precio': '10000',
            'cantidad_disponible': 3,  # menor al mínimo (15)
        }
        response = self.client.post(self.url, datos)

        self.assertEqual(response.status_code, 200)  # vuelve a mostrar el form
        self.assertFalse(Producto.objects.filter(nombre='Producto Chico').exists())

    def test_usuario_no_proveedor_no_puede_acceder(self):
        cliente = User.objects.create_user(
            username='soycliente2', email='soycliente2@test.com', password='clave123'
        )
        self.client.logout()
        self.client.login(username='soycliente2', password='clave123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)


# ---------------------------------------------------------------------------
# 6) VISTA: editar_producto
# ---------------------------------------------------------------------------
class EditarProductoVistaTests(TestCase):

    def setUp(self):
        self.proveedor = crear_proveedor()
        self.producto = crear_producto(self.proveedor, nombre='Original')
        self.url = reverse('inventario:editar', args=[self.producto.id])
        self.client.login(username='proveedor1', password='clave123')

    def test_post_valido_actualiza_el_producto(self):
        datos = {
            'nombre': 'Nombre Actualizado',
            'descripcion': self.producto.descripcion,
            'precio': str(self.producto.precio),
            'cantidad_disponible': self.producto.cantidad_disponible,
        }
        response = self.client.post(self.url, datos)

        self.assertRedirects(
            response, reverse('inventario:dashboard'), fetch_redirect_response=False
        )
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.nombre, 'Nombre Actualizado')

    def test_no_se_puede_editar_producto_de_otro_proveedor(self):
        otro_proveedor = crear_proveedor(username='otro2')
        producto_ajeno = crear_producto(otro_proveedor, nombre='Ajeno')
        url_ajena = reverse('inventario:editar', args=[producto_ajeno.id])

        response = self.client.get(url_ajena)
        self.assertEqual(response.status_code, 404)


# ---------------------------------------------------------------------------
# 7) VISTA: eliminar_producto
# ---------------------------------------------------------------------------
class EliminarProductoVistaTests(TestCase):

    def setUp(self):
        self.proveedor = crear_proveedor()
        self.producto = crear_producto(self.proveedor)
        self.client.login(username='proveedor1', password='clave123')

    def test_elimina_el_producto_propio(self):
        url = reverse('inventario:eliminar_producto', args=[self.producto.id])
        response = self.client.get(url)

        self.assertRedirects(
            response, reverse('inventario:dashboard'), fetch_redirect_response=False
        )
        self.assertFalse(Producto.objects.filter(id=self.producto.id).exists())

    def test_no_puede_eliminar_producto_de_otro_proveedor(self):
        otro_proveedor = crear_proveedor(username='otro3')
        producto_ajeno = crear_producto(otro_proveedor)
        url = reverse('inventario:eliminar_producto', args=[producto_ajeno.id])

        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Producto.objects.filter(id=producto_ajeno.id).exists())


# ---------------------------------------------------------------------------
# 8) VISTA: cambiar_estado_producto
# ---------------------------------------------------------------------------
class CambiarEstadoProductoVistaTests(TestCase):

    def setUp(self):
        self.proveedor = crear_proveedor()
        self.producto = crear_producto(self.proveedor, esta_activo=True)
        self.client.login(username='proveedor1', password='clave123')
        self.url = reverse('inventario:cambiar_estado', args=[self.producto.id])

    def test_pausa_un_producto_activo(self):
        response = self.client.get(self.url)
        self.producto.refresh_from_db()

        self.assertRedirects(
            response, reverse('inventario:dashboard'), fetch_redirect_response=False
        )
        self.assertFalse(self.producto.esta_activo)

    def test_reactiva_un_producto_pausado(self):
        self.producto.esta_activo = False
        self.producto.save()

        self.client.get(self.url)
        self.producto.refresh_from_db()
        self.assertTrue(self.producto.esta_activo)
# Create your tests here.

# Create your tests here.
