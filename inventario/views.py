from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.apps import apps
from django.db.models import Sum, F, DecimalField
from django.db.models.functions import Coalesce
from django.utils import timezone
from .models import Producto
from .forms import ProductoForm


@login_required
def dashboard_proveedor(request):
    if request.user.perfil.rol != 'PROVEEDOR':
        return redirect('login')

    Envio = apps.get_model('rastreo', 'Envio')

    # Productos de este proveedor
    mis_productos = Producto.objects.filter(proveedor=request.user)

    # Envíos (ventas) de productos de este proveedor, sin contar los cancelados
    ventas_proveedor = Envio.objects.filter(
        producto__proveedor=request.user
    ).exclude(estado_actual='cancelado')

    # --- Ingresos del mes actual ---
    ahora = timezone.now()
    ventas_del_mes = ventas_proveedor.filter(
        fecha_creacion__year=ahora.year,
        fecha_creacion__month=ahora.month,
    )

    ingresos_mes = ventas_del_mes.aggregate(
        total=Coalesce(
            Sum(F('cantidad') * F('precio_unitario'), output_field=DecimalField()),
            0,
            output_field=DecimalField(),
        )
    )['total']

    # --- Producto más vendido (histórico, de todas las ventas) ---
    producto_mas_vendido = (
        ventas_proveedor
        .values('producto__id', 'producto__nombre')
        .annotate(total_vendido=Sum('cantidad'))
        .order_by('-total_vendido')
        .first()
    )

    if producto_mas_vendido:
        # Le damos forma de objeto simple para usarlo fácil en el template
        producto_mas_vendido = {
            'nombre': producto_mas_vendido['producto__nombre'],
            'total_vendido': producto_mas_vendido['total_vendido'],
        }

    return render(request, 'dashboard_proveedor.html', {
        'inventario': mis_productos,
        'ingresos_mes': ingresos_mes,
        'producto_mas_vendido': producto_mas_vendido,
    })


@login_required
def agregar_producto(request):
    if request.user.perfil.rol != 'PROVEEDOR':
        return redirect('login')

    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():
            producto = form.save(commit=False)
            producto.proveedor = request.user
            producto.save()
            messages.success(request, '¡Producto añadido con éxito al inventario!')
            return redirect('dashboard')
    else:
        form = ProductoForm()

    return render(request, 'agregar_producto.html', {'form': form})


@login_required
def editar_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id, proveedor=request.user)

    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, f"'{producto.nombre}' fue actualizado.")
            return redirect('dashboard')
    else:
        form = ProductoForm(instance=producto)

    return render(request, 'agregar_producto.html', {'form': form, 'editando': True})


@login_required
def eliminar_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id, proveedor=request.user)
    producto.esta_activo = False
    producto.save()
    messages.success(request, f"'{producto.nombre}' fue eliminado.")
    return redirect('dashboard')