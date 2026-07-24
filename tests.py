from django.test import TestCase
from django.contrib.auth.models import User


class UsuarioTest(TestCase):
    """
    Pruebas relacionadas con la creacion de usuarios.
    """

    def test_crear_usuario(self):
        """
        Verifica que un usuario pueda registrarse correctamente.
        """

        # Crear el usuario
        usuario = User.objects.create_user(
            username="santiago",
            email="santiago@gmail.com",
            password="123456789"
        )

        # Comprobar que se creó correctamente tanto el usuario como el correo
        self.assertEqual(usuario.username, "santiago")
        self.assertEqual(usuario.email, "santiago@gmail.com")

        # Comprobar que la contraseña fue almacenada correctamente
        self.assertTrue(usuario.check_password("123456789"))

        # Comprobar que existe en la base de datos
        self.assertEqual(User.objects.count(), 1)
