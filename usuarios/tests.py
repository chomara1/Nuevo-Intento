 """
Pruebas unitarias de la app 'usuarios'.

Qué cubre este archivo:
1) PerfilModelTests      -> el modelo Perfil y las señales (signals) que lo crean.
2) RegistroVistaTests    -> la vista de registro (usuarios.views.registro).
3) LoginVistaTests       -> la vista de login (usuarios.views.login_view) y
                             la función redirect_por_rol.
4) PerfilVistaTests      -> la vista de perfil, protegida con @login_required.
5) TiendaHomeVistaTests  -> la vista pública tienda_home.

  
"""

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.db.models.signals import post_save

from .models import Perfil, crear_perfil_usuario


# ---------------------------------------------------------------------------
# 1) MODELO
# ---------------------------------------------------------------------------
class PerfilModelTests(TestCase):
    """
    Probamos el modelo directamente, sin pasar por vistas ni por el cliente
    HTTP. Esto es lo más rápido de probar y donde deben vivir la mayoría de
    tus tests: si la lógica de negocio está en el modelo, pruébala ahí.
    """

    def test_crear_usuario_crea_perfil_automaticamente(self):
        """
        usuarios/models.py conecta la señal post_save de User a
        crear_perfil_usuario, que crea un Perfil cuando created=True.
        """
        usuario = User.objects.create_user(
            username='juan', email='juan@test.com', password='clave123'
        )
        self.assertTrue(Perfil.objects.filter(usuario=usuario).exists())

    def test_perfil_por_defecto_tiene_rol_cliente_y_esta_aprobado(self):
        usuario = User.objects.create_user(
            username='maria', email='maria@test.com', password='clave123'
        )
        perfil = usuario.perfil
        self.assertEqual(perfil.rol, 'CLIENTE')
        self.assertTrue(perfil.aprobado)

    def test_str_devuelve_username_y_rol_legible(self):
        usuario = User.objects.create_user(
            username='pedro', email='pedro@test.com', password='clave123'
        )
        perfil = usuario.perfil
        self.assertEqual(str(perfil), f"pedro - {perfil.get_rol_display()}")

    def test_perfil_nuevo_creado_directamente_como_proveedor_queda_sin_aprobar(self):
        """
        Este test aísla la regla de negocio que vive en Perfil.save():

            if self.pk is None and self.rol == 'PROVEEDOR':
                self.aprobado = False

        Como la señal post_save de User SIEMPRE crea un Perfil con rol
        CLIENTE apenas se crea el User, para poder probar la rama
        "Perfil nuevo con rol PROVEEDOR" desconectamos momentáneamente la
        señal, así el User queda "pelado" (sin Perfil) y podemos crear
        nosotros mismos el Perfil con rol='PROVEEDOR'.

        El bloque try/finally garantiza que la señal se reconecte SIEMPRE,
        incluso si el test falla, para no romper el resto de la suite.
        """
        post_save.disconnect(crear_perfil_usuario, sender=User)
        try:
            usuario = User.objects.create_user(
                username='nuevo_prov', email='prov@test.com', password='clave123'
            )
            self.assertFalse(Perfil.objects.filter(usuario=usuario).exists())

            perfil = Perfil(usuario=usuario, rol='PROVEEDOR')
            perfil.save()
            perfil.refresh_from_db()

            self.assertFalse(perfil.aprobado)
        finally:
            post_save.connect(crear_perfil_usuario, sender=User)

    def test_perfil_cliente_no_requiere_aprobacion_al_crearse(self):
        post_save.disconnect(crear_perfil_usuario, sender=User)
        try:
            usuario = User.objects.create_user(
                username='nuevo_cli', email='cli@test.com', password='clave123'
            )
            perfil = Perfil(usuario=usuario, rol='CLIENTE')
            perfil.save()
            self.assertTrue(perfil.aprobado)
        finally:
            post_save.connect(crear_perfil_usuario, sender=User)


# ---------------------------------------------------------------------------
# 2) VISTA: registro
# ---------------------------------------------------------------------------
class RegistroVistaTests(TestCase):

    def setUp(self):
        # setUp corre ANTES de cada test_* de esta clase. Aquí dejamos listo
        # todo lo que todos los tests de esta clase necesitan.
        self.url = reverse('usuarios:registro')

    def test_get_muestra_formulario_de_registro(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registro.html')

    def test_registro_exitoso_como_cliente(self):
        datos = {
            'username': 'ana',
            'email': 'ana@test.com',
            'password': 'clave123',
            'tipo_cuenta': 'CLIENTE',
        }
        response = self.client.post(self.url, datos)

        # No seguimos el redirect (fetch_redirect_response=False) para que
        # este test no dependa de que la vista tienda_home renderice bien;
        # aquí solo nos interesa el comportamiento de "registro", no el de
        # tienda_home (eso se prueba aparte).
        self.assertRedirects(
            response, reverse('usuarios:tienda_home'), fetch_redirect_response=False
        )

        usuario = User.objects.get(username='ana')
        self.assertEqual(usuario.perfil.rol, 'CLIENTE')
        self.assertTrue(usuario.perfil.aprobado)

        # El usuario debe quedar autenticado (auth_login fue llamado)
        self.assertIn('_auth_user_id', self.client.session)

    def test_registro_exitoso_como_proveedor_queda_pendiente_de_aprobacion(self):
        datos = {
            'username': 'proveedor1',
            'email': 'proveedor1@test.com',
            'password': 'clave123',
            'tipo_cuenta': 'PROVEEDOR',
        }
        response = self.client.post(self.url, datos)

        usuario = User.objects.get(username='proveedor1')
        self.assertFalse(usuario.perfil.aprobado)

        # El mensaje se guarda con messages.info() antes del redirect; para
        # leerlo necesitamos "seguir" la respuesta hasta la próxima página.
        response_seguido = self.client.get(reverse('usuarios:tienda_home'))
        mensajes = [m.message for m in get_messages(response_seguido.wsgi_request)]
        # (alternativa más directa, sin una segunda petición:)
        mensajes_directos = [m.message for m in get_messages(response.wsgi_request)]
        self.assertTrue(
            any('pendiente de aprobación' in m for m in mensajes_directos)
        )

    def test_password_muy_corta_no_registra_y_muestra_error(self):
        datos = {
            'username': 'x1', 'email': 'x1@test.com',
            'password': 'ab', 'tipo_cuenta': 'CLIENTE',
        }
        response = self.client.post(self.url, datos)

        self.assertEqual(response.status_code, 200)
        self.assertIn('error', response.context)
        self.assertEqual(
            response.context['error'],
            'La contraseña debe tener entre 5 y 16 caracteres.',
        )
        self.assertFalse(User.objects.filter(username='x1').exists())

    def test_password_muy_larga_no_registra_y_muestra_error(self):
        datos = {
            'username': 'x2', 'email': 'x2@test.com',
            'password': 'a' * 17, 'tipo_cuenta': 'CLIENTE',
        }
        response = self.client.post(self.url, datos)

        self.assertEqual(response.status_code, 200)
        self.assertIn('error', response.context)
        self.assertFalse(User.objects.filter(username='x2').exists())

    def test_username_duplicado_muestra_error(self):
        User.objects.create_user(
            username='repetido', email='otro@test.com', password='clave123'
        )
        datos = {
            'username': 'repetido', 'email': 'nuevo@test.com',
            'password': 'clave123', 'tipo_cuenta': 'CLIENTE',
        }
        response = self.client.post(self.url, datos)

        self.assertEqual(response.status_code, 200)
        self.assertIn('error', response.context)
        # Sigue existiendo solo el original, no se creó uno nuevo
        self.assertEqual(User.objects.filter(username='repetido').count(), 1)

    def test_email_duplicado_muestra_error(self):
        User.objects.create_user(
            username='original', email='mismo@test.com', password='clave123'
        )
        datos = {
            'username': 'otronombre', 'email': 'mismo@test.com',
            'password': 'clave123', 'tipo_cuenta': 'CLIENTE',
        }
        response = self.client.post(self.url, datos)

        self.assertEqual(response.status_code, 200)
        self.assertIn('error', response.context)
        self.assertFalse(User.objects.filter(username='otronombre').exists())


# ---------------------------------------------------------------------------
# 3) VISTA: login_view + redirect_por_rol
# ---------------------------------------------------------------------------
class LoginVistaTests(TestCase):

    def setUp(self):
        self.url = reverse('usuarios:login')
        self.usuario = User.objects.create_user(
            username='cliente1', email='cliente1@test.com', password='clave123'
        )

    def test_get_muestra_formulario(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_login_correcto_de_cliente_redirige_a_tienda_home(self):
        response = self.client.post(
            self.url, {'username': 'cliente1@test.com', 'password': 'clave123'}
        )
        self.assertRedirects(
            response, reverse('usuarios:tienda_home'), fetch_redirect_response=False
        )
        self.assertIn('_auth_user_id', self.client.session)

    def test_login_correo_inexistente_muestra_error(self):
        response = self.client.post(
            self.url, {'username': 'noexiste@test.com', 'password': 'clave123'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['error'], 'No existe la cuenta.')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_login_password_incorrecta_muestra_error(self):
        response = self.client.post(
            self.url, {'username': 'cliente1@test.com', 'password': 'incorrecta'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['error'], 'Contraseña incorrecta.')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_login_redirige_proveedor_a_su_dashboard(self):
        self.usuario.perfil.rol = 'PROVEEDOR'
        self.usuario.perfil.save()

        response = self.client.post(
            self.url, {'username': 'cliente1@test.com', 'password': 'clave123'}
        )
        self.assertRedirects(
            response, reverse('inventario:dashboard'), fetch_redirect_response=False
        )

    def test_login_redirige_admin_a_panel_administracion(self):
        self.usuario.perfil.rol = 'ADMIN'
        self.usuario.perfil.save()

        response = self.client.post(
            self.url, {'username': 'cliente1@test.com', 'password': 'clave123'}
        )
        self.assertRedirects(
            response, reverse('administracion:dashboard'), fetch_redirect_response=False
        )


# ---------------------------------------------------------------------------
# 4) VISTA: perfil (protegida con @login_required)
# ---------------------------------------------------------------------------
class PerfilVistaTests(TestCase):

    def setUp(self):
        self.url = reverse('usuarios:perfil')
        self.usuario = User.objects.create_user(
            username='con_sesion', email='con_sesion@test.com', password='clave123'
        )

    def test_usuario_anonimo_es_redirigido_a_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('usuarios:login'), response.url)

    def test_usuario_autenticado_puede_ver_su_perfil(self):
        self.client.login(username='con_sesion', password='clave123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'perfil.html')


# ---------------------------------------------------------------------------
# 5) VISTA: tienda_home (pública)
# ---------------------------------------------------------------------------
class TiendaHomeVistaTests(TestCase):

    def test_pagina_publica_responde_200_sin_login(self):
        response = self.client.get(reverse('usuarios:tienda_home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tienda_home.html')
        self.assertIn('productos', response.context)
        self.assertIn('diseno', response.context)
