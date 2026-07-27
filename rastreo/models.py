from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from inventario.models import Producto


class EmpresaEnvio(models.Model):
    nombre_empresa = models.CharField(max_length=150)
    contacto = models.CharField(max_length=100, blank=True)
    correo = models.EmailField(blank=True)

    def __str__(self):
        return self.nombre_empresa

    class Meta:
        verbose_name = "Empresa de Envíos"
        verbose_name_plural = "Empresas de Envíos"


class Envio(models.Model):
    ESTADOS = [
        ('preparando', 'En preparación'),
        ('listo', 'Listo'),
        ('en_camino', 'En viaje'),
        ('entregado', 'Llegó a su destino'),
        ('cancelado', 'Cancelado'),
    ]

    METODOS_PAGO = [
        ('nequi', 'Nequi'),
        ('tarjeta', 'Tarjeta (Visa/Mastercard)'),
        ('pse', 'PSE'),
        ('mercadopago', 'Mercado Pago'),
        ('contraentrega', 'Pago contraentrega'),
    ]

    # Tiempos que debe esperar el estado automático después de asignar la
    # empresa de envíos. Ajusta estos valores libremente.
    TIEMPO_LISTO = timedelta(hours=2)
    TIEMPO_EN_CAMINO = timedelta(days=1)
    TIEMPO_ENTREGADO = timedelta(days=3)

    ORDEN_ESTADOS = ['preparando', 'listo', 'en_camino', 'entregado']

    cliente = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='envios')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    empresa_envio = models.ForeignKey(
        EmpresaEnvio,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='envios'
    )
    fecha_asignacion_empresa = models.DateTimeField(null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    estado_actual = models.CharField(max_length=20, choices=ESTADOS, default='preparando')
    numero_guia = models.CharField(max_length=20, unique=True)

    # Datos de la venta
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

    def actualizar_estado_automatico(self):
        """
        Si ya se le asignó una empresa de envíos, revisa cuánto tiempo ha
        pasado desde esa asignación y avanza el estado solo (preparando ->
        listo -> en_camino -> entregado), sin que el administrador tenga
        que hacerlo a mano. Se llama cada vez que se muestra el envío.
        """
        if not self.empresa_envio or not self.fecha_asignacion_empresa:
            return
        if self.estado_actual in ('entregado', 'cancelado'):
            return

        transcurrido = timezone.now() - self.fecha_asignacion_empresa

        if transcurrido >= self.TIEMPO_ENTREGADO:
            estado_esperado = 'entregado'
        elif transcurrido >= self.TIEMPO_EN_CAMINO:
            estado_esperado = 'en_camino'
        elif transcurrido >= self.TIEMPO_LISTO:
            estado_esperado = 'listo'
        else:
            estado_esperado = self.estado_actual

        if self.ORDEN_ESTADOS.index(estado_esperado) > self.ORDEN_ESTADOS.index(self.estado_actual):
            self.estado_actual = estado_esperado
            self.save(update_fields=['estado_actual'])
            HistorialEstado.objects.create(
                envio=self,
                estado=estado_esperado,
                comentario='Actualizado automáticamente por la empresa de envíos'
            )

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