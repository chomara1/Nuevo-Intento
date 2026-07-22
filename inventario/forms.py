from django import forms
from .models import Producto

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
        