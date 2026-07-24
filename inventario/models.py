from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from django.core.validators import MinValueValidator


class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    categoria_padre = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subcategorias',
        help_text="Déjalo vacío si esta es una categoría principal (ej. 'Cuidado del cabello')"
    )

    def __str__(self):
        if self.categoria_padre:
            return f"{self.categoria_padre.nombre} → {self.nombre}"
        return self.nombre

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"

class Producto(models.Model):
    proveedor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='productos')
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, related_name='articulos')

    nombre = models.CharField(max_length=150)
    marca = models.CharField(max_length=100, blank=True, null=True)
    descripcion = models.TextField()
    precio = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    cantidad_disponible = models.PositiveIntegerField(default=0)
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True)
    esta_activo = models.BooleanField(default=True, help_text="Permite pausar la venta del producto sin eliminarlo")

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    ultima_actualizacion = models.DateTimeField(auto_now=True)

    HORAS_LIMITE_NUEVO = 5

    @property
    def es_nuevo(self):
        """True mientras no hayan pasado más de 5 horas desde que se creó el producto."""
        limite = self.fecha_creacion + timedelta(hours=self.HORAS_LIMITE_NUEVO)
        return timezone.now() < limite

    def __str__(self):
        return self.nombre