from django.db import models
from django.conf import settings
from inventario.models import Producto


class Envio(models.Model):
    ESTADOS = [
        ('preparando', 'Preparando pedido'),
        ('en_camino', 'En camino'),
        ('en_reparto', 'En reparto local'),
        ('entregado', 'Entregado'),
        ('cancelado', 'Cancelado'),
    ]

    METODOS_PAGO = [
        ('nequi', 'Nequi'),
        ('tarjeta', 'Tarjeta (Visa/Mastercard)'),
        ('pse', 'PSE'),
        ('mercadopago', 'Mercado Pago'),
        ('contraentrega', 'Pago contraentrega'),
    ]

    cliente = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='envios')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    estado_actual = models.CharField(max_length=20, choices=ESTADOS, default='preparando')
    numero_guia = models.CharField(max_length=20, unique=True)

    # Datos de la venta (nuevos)
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Datos de envío (capturados en el checkout)
    nombre_destinatario = models.CharField(max_length=150, blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    correo = models.EmailField(blank=True)
    direccion = models.CharField(max_length=255, blank=True)
    departamento = models.CharField(max_length=100, blank=True)
    ciudad = models.CharField(max_length=100, blank=True)
    metodo_pago = models.CharField(max_length=20, choices=METODOS_PAGO, blank=True)

    def subtotal(self):
        return self.cantidad * self.precio_unitario

    def __str__(self):
        return f"Envío #{self.numero_guia} - {self.cliente}"


class HistorialEstado(models.Model):
    envio = models.ForeignKey(Envio, on_delete=models.CASCADE, related_name='historial')
    estado = models.CharField(max_length=20, choices=Envio.ESTADOS)
    fecha = models.DateTimeField(auto_now_add=True)
    comentario = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ['fecha']

    def __str__(self):
        return f"{self.estado} - {self.fecha.strftime('%d/%m/%Y %H:%M')}"