from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.apps import apps
from .models import Perfil

# ==========================================
# 1. TIENDA HOME (VISTA PÚBLICA)
# ==========================================
def tienda_home(request):
    Producto = apps.get_model('inventario', 'Producto')
    DisenoSitio = apps.get_model('administracion', 'DisenoSitio')

    productos = Producto.objects.filter(esta_activo=True)
    diseno = DisenoSitio.cargar()

    return render(request, 'tienda_home.html', {
        'productos': productos,
        'diseno': diseno,
    })

# ==========================================
# 2. INICIO DE SESIÓN (LOGIN)
# ==========================================
def login_view(request):
    if request.method == 'POST':
        correo_ingresado = request.POST.get('username')
        clave_ingresada = request.POST.get('password')

        usuario_encontrado = User.objects.filter(email=correo_ingresado).first()

        if usuario_encontrado is not None:
            user = authenticate(request, username=usuario_encontrado.username, password=clave_ingresada)
            if user is not None:
                auth_login(request, user)
                return redirect_por_rol(user)
            else:
                return render(request, 'registro.html', {'error': 'Contraseña incorrecta.'})
        else:
            return render(request, 'registro.html', {'error': 'No existe la cuenta.'})

    return render(request, 'registro.html')


# ==========================================
# 3. REDIRECCIÓN DINÁMICA POR ROL
# ==========================================
def redirect_por_rol(user):
    rol = user.perfil.rol

    if rol == 'PROVEEDOR':
        return redirect('usuarios:dashboard')
    elif rol == 'ADMIN':
        return redirect('administracion:dashboard')
    else:  # CLIENTE
        return redirect('usuarios:tienda_home')


# ==========================================
# 4. REGISTRO DE USUARIOS NUEVOS
# ==========================================
def registro(request):
    if request.method == 'POST':
        usuario = request.POST.get('username')
        correo = request.POST.get('email')
        clave = request.POST.get('password')
        tipo_cuenta = request.POST.get('tipo_cuenta', 'CLIENTE')  # 'CLIENTE' o 'PROVEEDOR'

        if User.objects.filter(username=usuario).exists() or User.objects.filter(email=correo).exists():
            return render(request, 'registro.html', {'error': 'El usuario o correo ya existen.'})

        nuevo_usuario = User.objects.create_user(username=usuario, email=correo, password=clave)

        # La señal post_save ya creó el Perfil con rol='CLIENTE' por defecto.
        # Aquí lo ajustamos según lo que eligió en el formulario.
        perfil_obj = nuevo_usuario.perfil
        perfil_obj.rol = tipo_cuenta
        if tipo_cuenta == 'PROVEEDOR':
            perfil_obj.aprobado = False
        perfil_obj.save()

        auth_login(request, nuevo_usuario)

        if tipo_cuenta == 'PROVEEDOR':
            messages.info(request, "Tu cuenta de proveedor fue creada y está pendiente de aprobación por un administrador.")

        return redirect('usuarios:tienda_home')

    return render(request, 'registro.html')


# ==========================================
# 5. PERFIL DE USUARIO
# ==========================================
@login_required(login_url='usuarios:login')
def perfil(request):
    return render(request, 'perfil.html')


# ==========================================
# 6. DASHBOARD / PANEL DEL PROVEEDOR
# ==========================================
@login_required(login_url='usuarios:login')
def dashboard(request):
    if request.user.perfil.rol != 'PROVEEDOR':
        return redirect('usuarios:tienda_home')

    return render(request, 'dashboard_proveedor.html')