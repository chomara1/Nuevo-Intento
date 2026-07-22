from django.db import models


class DisenoSitio(models.Model):
    """
    Modelo tipo 'singleton': siempre existe un único registro (pk=1)
    que guarda el contenido editable del carrusel de la tienda pública.
    El admin lo edita desde el panel; la plantilla de usuarios lo consume.
    """

    # --- Slide 1 ---
    slide1_titulo = models.CharField(
        max_length=100,
        default="El clóset de belleza que sí quieren tener"
    )
    slide1_texto = models.TextField(
        default="Cosmetiqueras, accesorios y maquillaje de tus personajes "
                 "favoritos, pensados para manos pequeñas."
    )
    slide1_color_a = models.CharField(max_length=7, default="#6C3B8C")
    slide1_color_b = models.CharField(max_length=7, default="#2D1B4E")

    # --- Slide 2 ---
    slide2_titulo = models.CharField(
        max_length=100,
        default="Hasta 20% menos en set seleccionados"
    )
    slide2_texto = models.TextField(
        default="Aprovecha antes de que se agoten las referencias más "
                 "buscadas del mes."
    )
    slide2_color_a = models.CharField(max_length=7, default="#8E44AD")
    slide2_color_b = models.CharField(max_length=7, default="#4A1F6A")

    # --- Slide 3 ---
    slide3_titulo = models.CharField(
        max_length=100,
        default="Nueva colección Toy Story ya está aquí"
    )
    slide3_texto = models.TextField(
        default="Sombras, brillos y accesorios de cabello para armar looks "
                 "llenos de imaginación."
    )
    slide3_color_a = models.CharField(max_length=7, default="#9B59B6")
    slide3_color_b = models.CharField(max_length=7, default="#2D1B4E")

    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Diseño del sitio"
        verbose_name_plural = "Diseño del sitio"

    def save(self, *args, **kwargs):
        # Fuerza siempre el mismo pk => nunca hay más de un registro
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass  # evita que se borre el único registro por accidente

    @classmethod
    def cargar(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return "Configuración de diseño (carrusel de inicio)"
