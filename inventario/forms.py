from django import forms
from .models import Producto

CANTIDAD_MINIMA_PUBLICACION = 15


class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        exclude = ['proveedor', 'esta_activo']
        labels = {
            'categoria': 'Categoría del Producto',
            'nombre': 'Nombre del Producto',
            'marca': 'Marca',
            'descripcion': 'Descripción Detallada',
            'precio': 'Precio de Venta (COP)',
            'cantidad_disponible': 'Cantidad Inicial en Stock (Unidades)',
            'imagen': 'Foto del Producto',
        }

    def clean_cantidad_disponible(self):
        cantidad = self.cleaned_data.get('cantidad_disponible')
        es_producto_nuevo = self.instance.pk is None

        if es_producto_nuevo and cantidad is not None and cantidad < CANTIDAD_MINIMA_PUBLICACION:
            raise forms.ValidationError(
                f'La cantidad mínima para publicar un producto nuevo es de {CANTIDAD_MINIMA_PUBLICACION} unidades.'
            )

        return cantidad