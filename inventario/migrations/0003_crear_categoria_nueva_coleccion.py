from django.db import migrations

def crear_categoria(apps, schema_editor):
    Categoria = apps.get_model('inventario', 'Categoria')
    Categoria.objects.get_or_create(
        nombre='Nueva Colección',
        defaults={'descripcion': 'Productos recién agregados a la tienda'}
    )


def eliminar_categoria(apps, schema_editor):
    Categoria = apps.get_model('inventario', 'Categoria')
    Categoria.objects.filter(nombre='Nueva Colección').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0002_alter_producto_precio'),
    ]

    operations = [
        migrations.RunPython(crear_categoria, eliminar_categoria),
    ]