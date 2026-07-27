from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.apps import apps
from django.utils import timezone
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


#Lista de proveedores(aprobados y no aprobados)
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
    #Le agregamos a cada perfil cuántos productos tiene registrados
    for perfil in proveedores:
        perfil.total_productos = Producto.objects.filter(proveedor=perfil.usuario).count()

    return render(request, 'administracion/lista_proveedores.html', {
        'proveedores': proveedores,
        'active': 'lista_proveedores',
    })

#Mostrar los productos de cada proveedor

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

#Eliminar cuenta de proveedor y sus productos
@admin_required
def eliminar_proveedor(request, perfil_id):
    Perfil = apps.get_model("usuarios", "Perfil")

    perfil = get_object_or_404(Perfil, id=perfil_id, rol='PROVEEDOR')
    usuario = perfil.usuario
    nombre = usuario.username
    usuario.delete()  # borra el User, su Perfil y todos sus Producto en cascada
    messages.warning(request, f"La cuenta del proveedor '{nombre}' y todos sus productos fueron eliminados.")
    return redirect('administracion:lista_proveedores')

#Eliminar un producto especifico de un proveedor
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
    EmpresaEnvio = apps.get_model('rastreo', 'EmpresaEnvio')
    pedidos_lista = (
        Envio.objects
        .select_related('cliente', 'producto', 'empresa_envio')
        .order_by('-fecha_creacion')
    )
    for envio in pedidos_lista:
        envio.actualizar_estado_automatico()
    return render(request, 'administracion/pedidos.html', {
        'pedidos': pedidos_lista,
        'estados': Envio.ESTADOS,
        'empresas_envio': EmpresaEnvio.objects.all(),
        'active': 'pedidos',
    })


@admin_required
def asignar_empresa_pedido(request, envio_id):
    Envio = apps.get_model('rastreo', 'Envio')
    EmpresaEnvio = apps.get_model('rastreo', 'EmpresaEnvio')
    envio = get_object_or_404(Envio, id=envio_id)

    if request.method == 'POST':
        empresa_envio_id = request.POST.get('empresa_envio')

        if empresa_envio_id:
            empresa = get_object_or_404(EmpresaEnvio, id=empresa_envio_id)
            if envio.empresa_envio_id != empresa.id:
                envio.fecha_asignacion_empresa = timezone.now()
            envio.empresa_envio = empresa
            messages.success(request, f"Se asignó '{empresa.nombre_empresa}' al pedido {envio.numero_guia}. El estado avanzará automáticamente.")
        else:
            envio.empresa_envio = None
            envio.fecha_asignacion_empresa = None
            messages.success(request, f"Se quitó la empresa de envíos del pedido {envio.numero_guia}.")

        envio.save()

    return redirect('administracion:pedidos')


@admin_required
def cancelar_pedido(request, envio_id):
    Envio = apps.get_model('rastreo', 'Envio')
    HistorialEstado = apps.get_model('rastreo', 'HistorialEstado')
    envio = get_object_or_404(Envio, id=envio_id)

    if request.method == 'POST':
        envio.estado_actual = 'cancelado'
        envio.save()
        HistorialEstado.objects.create(envio=envio, estado='cancelado', comentario='Cancelado por el administrador')
        messages.success(request, f"El pedido {envio.numero_guia} fue cancelado.")

    return redirect('administracion:pedidos')