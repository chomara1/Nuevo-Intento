from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.apps import apps
from .decorators import admin_required
from .models import DisenoSitio
from .forms import DisenoSitioForm


@admin_required
def dashboard(request):
    Perfil = apps.get_model("usuarios", "Perfil")
    
    proveedores_pendientes = (
        Perfil.objects
        .filter(rol='PROVEEDOR', aprobado=False)
        .select_related('usuario')
        .order_by('-id')
    )
    return render(request, 'administracion/dashboard.html', {
        'proveedores_pendientes': proveedores_pendientes,
        'active': 'proveedores',
    })


@admin_required
def aprobar_proveedor(request, perfil_id):
    Perfil = apps.get_model("usuarios", "Perfil")
    
    perfil = get_object_or_404(Perfil, id=perfil_id, rol='PROVEEDOR')
    perfil.aprobado = True
    perfil.save()
    messages.success(request, f"El proveedor {perfil.usuario.username} fue aprobado correctamente.")
    return redirect('administracion:dashboard')


@admin_required
def rechazar_proveedor(request, perfil_id):
    Perfil = apps.get_model("usuarios", "Perfil")
    
    perfil = get_object_or_404(Perfil, id=perfil_id, rol='PROVEEDOR')
    usuario = perfil.usuario
    nombre = usuario.username
    usuario.delete()  # borra el User y, en cascada, su Perfil
    messages.warning(request, f"La solicitud de {nombre} fue rechazada y eliminada.")
    return redirect('administracion:dashboard')


# ==========================================
# LISTA COMPLETA DE PROVEEDORES (aprobados y no aprobados)
# ==========================================
@admin_required
def lista_proveedores(request):
    Perfil = apps.get_model("usuarios", "Perfil")
    Producto = apps.get_model("inventario", "Producto")

    proveedores = (
        Perfil.objects
        .filter(rol='PROVEEDOR')
        .select_related('usuario')
        .order_by('usuario__username')
    )

    # Le agregamos a cada perfil cuántos productos tiene registrados
    for perfil in proveedores:
        perfil.total_productos = Producto.objects.filter(proveedor=perfil.usuario).count()

    return render(request, 'administracion/lista_proveedores.html', {
        'proveedores': proveedores,
        'active': 'lista_proveedores',
    })


# ==========================================
# PRODUCTOS SUBIDOS POR UN PROVEEDOR ESPECÍFICO
# ==========================================
@admin_required
def productos_proveedor(request, perfil_id):
    Perfil = apps.get_model("usuarios", "Perfil")
    Producto = apps.get_model("inventario", "Producto")

    perfil = get_object_or_404(Perfil, id=perfil_id, rol='PROVEEDOR')
    productos = Producto.objects.filter(proveedor=perfil.usuario).order_by('-fecha_creacion')

    return render(request, 'administracion/productos_proveedor.html', {
        'perfil_proveedor': perfil,
        'productos': productos,
        'active': 'lista_proveedores',
    })


# ==========================================
# ELIMINAR CUENTA DE UN PROVEEDOR (y sus productos, en cascada)
# ==========================================
@admin_required
def eliminar_proveedor(request, perfil_id):
    Perfil = apps.get_model("usuarios", "Perfil")

    perfil = get_object_or_404(Perfil, id=perfil_id, rol='PROVEEDOR')
    usuario = perfil.usuario
    nombre = usuario.username
    usuario.delete()  # borra el User, su Perfil y todos sus Producto en cascada
    messages.warning(request, f"La cuenta del proveedor '{nombre}' y todos sus productos fueron eliminados.")
    return redirect('administracion:lista_proveedores')


# ==========================================
# ELIMINAR UN PRODUCTO ESPECÍFICO DE CUALQUIER PROVEEDOR
# ==========================================
@admin_required
def eliminar_producto_admin(request, producto_id):
    Producto = apps.get_model("inventario", "Producto")

    producto = get_object_or_404(Producto, id=producto_id)
    perfil_id = producto.proveedor.perfil.id
    nombre_producto = producto.nombre
    producto.delete()
    messages.success(request, f"El producto '{nombre_producto}' fue eliminado.")
    return redirect('administracion:productos_proveedor', perfil_id=perfil_id)


@admin_required
def gestion_diseno(request):
    diseno = DisenoSitio.cargar()

    if request.method == 'POST':
        form = DisenoSitioForm(request.POST, request.FILES, instance=diseno)
        if form.is_valid():
            form.save()
            messages.success(request, "El diseño de la página se actualizó correctamente.")
            return redirect('administracion:gestion_diseno')
    else:
        form = DisenoSitioForm(instance=diseno)

    return render(request, 'administracion/gestion_diseno.html', {
        'form': form,
        'active': 'diseno',
    })


@admin_required
def pagos(request):
    Envio = apps.get_model('rastreo', 'Envio')
    pagos_lista = (
        Envio.objects
        .exclude(estado_actual='cancelado')
        .select_related('cliente', 'producto')
        .order_by('-fecha_creacion')
    )
    return render(request, 'administracion/pagos.html', {
        'pagos': pagos_lista,
        'active': 'pagos',
    })


@admin_required
def pedidos(request):
    Envio = apps.get_model('rastreo', 'Envio')
    pedidos_lista = (
        Envio.objects
        .select_related('cliente', 'producto')
        .order_by('-fecha_creacion')
    )
    return render(request, 'administracion/pedidos.html', {
        'pedidos': pedidos_lista,
        'estados': Envio.ESTADOS,
        'active': 'pedidos',
    })


@admin_required
def actualizar_estado_pedido(request, envio_id):
    Envio = apps.get_model('rastreo', 'Envio')
    HistorialEstado = apps.get_model('rastreo', 'HistorialEstado')
    envio = get_object_or_404(Envio, id=envio_id)

    if request.method == 'POST':
        nuevo_estado = request.POST.get('estado_actual')
        estados_validos = dict(Envio.ESTADOS)
        if nuevo_estado in estados_validos:
            envio.estado_actual = nuevo_estado
            envio.save()
            HistorialEstado.objects.create(envio=envio, estado=nuevo_estado)
            messages.success(request, f"El pedido {envio.numero_guia} se actualizó a '{estados_validos[nuevo_estado]}'.")
        else:
            messages.error(request, "Estado inválido.")

    return redirect('administracion:pedidos')