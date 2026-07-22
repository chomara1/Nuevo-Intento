from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from .models import Envio, HistorialEstado


@login_required
def mi_rastreo(request, codigo):
    envio = get_object_or_404(Envio, numero_guia=codigo, cliente=request.user)
    return render(request, 'detalle_envio.html', {'envio': envio})


@login_required
def lista_mis_envios(request):
    envios = Envio.objects.filter(cliente=request.user).order_by('-fecha_creacion')
    return render(request, 'mis_envios.html', {'envios': envios})


@login_required
def actualizar_estado(request, envio_id):
    if request.user.perfil.rol != 'PROVEEDOR':
        raise PermissionDenied

    # Solo se puede actualizar un envío si el producto pertenece a este proveedor
    envio = get_object_or_404(Envio, id=envio_id, producto__proveedor=request.user)

    if request.method == 'POST':
        nuevo_estado = request.POST.get('estado')
        comentario = request.POST.get('comentario', '')

        estados_validos = dict(Envio.ESTADOS)
        if nuevo_estado not in estados_validos:
            messages.error(request, 'Estado no válido.')
            return render(request, 'actualizar_estado.html', {'envio': envio})

        envio.estado_actual = nuevo_estado
        envio.save()
        HistorialEstado.objects.create(envio=envio, estado=nuevo_estado, comentario=comentario)
        return redirect('dashboard')
    return render(request, 'actualizar_estado.html', {'envio': envio})