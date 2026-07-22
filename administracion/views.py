from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.apps import apps
from .decorators import admin_required
from .models import DisenoSitio
from .forms import DisenoSitioForm


@admin_required
def dashboard(request):
    proveedores_pendientes = (
        apps.get_model('usuarios', 'Perfil').objects
        .filter(rol='PROVEEDOR', aprobado=False)
        .select_related('usuario')
        .order_by('-id')
    )
    return render(request, 'administracion/dashboard.html', {
        'proveedores_pendientes': proveedores_pendientes,
    })


@admin_required
def aprobar_proveedor(request, perfil_id):
    perfil = get_object_or_404(apps.get_model('usuarios', 'Perfil'), id=perfil_id, rol='PROVEEDOR')
    perfil.aprobado = True
    perfil.save()
    messages.success(request, f"El proveedor {perfil.usuario.username} fue aprobado correctamente.")
    return redirect('administracion:dashboard')


@admin_required
def rechazar_proveedor(request, perfil_id):
    perfil = get_object_or_404(apps.get_model('usuarios', 'Perfil'), id=perfil_id, rol='PROVEEDOR')
    usuario = perfil.usuario
    nombre = usuario.username
    usuario.delete()  # borra el User y, en cascada, su Perfil
    messages.warning(request, f"La solicitud de {nombre} fue rechazada y eliminada.")
    return redirect('administracion:dashboard')


@admin_required
def gestion_diseno(request):
    diseno = DisenoSitio.cargar()

    if request.method == 'POST':
        form = DisenoSitioForm(request.POST, instance=diseno)
        if form.is_valid():
            form.save()
            messages.success(request, "El diseño de la página se actualizó correctamente.")
            return redirect('administracion:gestion_diseno')
    else:
        form = DisenoSitioForm(instance=diseno)

    return render(request, 'administracion/gestion_diseno.html', {'form': form})