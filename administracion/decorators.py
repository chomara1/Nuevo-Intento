from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def admin_required(view_func):
    """
    Solo deja pasar a usuarios autenticados cuyo Perfil tenga rol='ADMIN'.
    Cualquier otro caso se redirige a la tienda pública con un mensaje.
    """
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('usuarios:registro')

        perfil = getattr(request.user, 'perfil', None)
        if not perfil or perfil.rol != 'ADMIN':
            messages.error(request, "No tienes permisos para acceder al panel de administración.")
            return redirect('usuarios:tienda_home')

        return view_func(request, *args, **kwargs)
    return _wrapped