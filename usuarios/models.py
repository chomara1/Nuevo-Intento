from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Perfil(models.Model):
    ROLES = [
        ('ADMIN', 'Administrador de la Plataforma'),
        ('PROVEEDOR', 'Proveedor de Herramientas'),
        ('CLIENTE', 'Cliente Final'),
    ]
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    rol = models.CharField(max_length=15, choices=ROLES, default='CLIENTE')
    telefono = models.CharField(max_length=20, blank=True, null=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    ciudad = models.CharField(max_length=100, blank=True, null=True)
    aprobado = models.BooleanField(default=True)
 
    def save(self, *args, **kwargs):
        # Solo se fuerza aprobado=False la PRIMERA vez que se crea
        # un perfil de tipo PROVEEDOR (self.pk is None = aún no existe en BD).
        # Así, si el admin lo aprueba después y vuelve a guardar, no se
        # le pisa el valor.
        if self.pk is None and self.rol == 'PROVEEDOR':
            self.aprobado = False
        super().save(*args, **kwargs)
 
    def __str__(self):
        return f"{self.usuario.username} - {self.get_rol_display()}"


@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    if created:
        Perfil.objects.create(usuario=instance)

@receiver(post_save, sender=User)
def guardar_perfil_usuario(sender, instance, **kwargs):
    instance.perfil.save()  