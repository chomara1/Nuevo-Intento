from functools import wraps
from django.shortcuts import redirect, render


def proveedor_aprobado_requerido(vista):
    @wraps(vista)
    def wrapper(request, *args, **kwargs):
        perfil = getattr(request.user, 'perfil', None)

        if perfil is None or perfil.rol != 'PROVEEDOR':
            return redirect('usuarios:login')

        if not perfil.aprobado:
            return render(request, 'pendiente_aprobacion.html')

        return vista(request, *args, **kwargs)

    return wrapper