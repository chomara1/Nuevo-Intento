import re
import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.apps import apps
from django.db import transaction
from .models import Carrito, ItemCarrito


def _cantidad_valida(valor_crudo):
    try:
        cantidad = int(valor_crudo)
    except (TypeError, ValueError):
        cantidad = 1
    if cantidad < 1:
        cantidad = 1
    return cantidad


# --- Patrones de validación para los datos de envío ---
PATRON_NOMBRE = re.compile(r'^[A-Za-zÀ-ÿ\s]{3,60}$')
PATRON_TELEFONO = re.compile(r'^3[0-9]{9}$')
PATRON_CORREO = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
PATRON_DIRECCION = re.compile(r'^(?=.*[A-Za-zÀ-ÿ])(?=.*[0-9]).{6,120}$')
PATRON_CIUDAD_DEPTO = re.compile(r'^[A-Za-zÀ-ÿ\s]{3,40}$')
METODOS_PAGO_VALIDOS = {'nequi', 'tarjeta', 'pse', 'mercadopago', 'contraentrega'}


def _validar_datos_envio(nombre, telefono, correo, direccion, departamento, ciudad, metodo_pago):
    """Devuelve una lista de errores. Lista vacía = todo válido."""
    errores = []

    if not PATRON_NOMBRE.match(nombre):
        errores.append('El nombre debe tener solo letras y al menos 3 caracteres.')

    if not PATRON_TELEFONO.match(telefono):
        errores.append('El teléfono debe ser un número celular colombiano válido (10 dígitos, inicia en 3).')

    if not PATRON_CORREO.match(correo):
        errores.append('El correo electrónico no es válido.')

    if not PATRON_DIRECCION.match(direccion):
        errores.append('La dirección debe incluir letras y números, con al menos 6 caracteres.')

    if not PATRON_CIUDAD_DEPTO.match(departamento):
        errores.append('El departamento debe tener solo letras y al menos 3 caracteres.')

    if not PATRON_CIUDAD_DEPTO.match(ciudad):
        errores.append('La ciudad debe tener solo letras y al menos 3 caracteres.')

    if metodo_pago not in METODOS_PAGO_VALIDOS:
        errores.append('Selecciona un método de pago válido.')

    return errores


@login_required
def ver_carrito(request):
    carrito, _ = Carrito.objects.get_or_create(cliente=request.user)
    return render(request, 'carrito.html', {'carrito': carrito})


@login_required
def agregar_al_carrito(request, producto_id):
    from django.http import JsonResponse

    Producto = apps.get_model('inventario', 'Producto')

    producto = get_object_or_404(Producto, id=producto_id)
    carrito, _ = Carrito.objects.get_or_create(cliente=request.user)

    cantidad = _cantidad_valida(request.GET.get('cantidad', 1))

    item, creado = ItemCarrito.objects.get_or_create(carrito=carrito, producto=producto)
    if creado:
        item.cantidad = cantidad
    else:
        item.cantidad += cantidad
    item.save()

    total_items = carrito.items.count()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'mensaje': f'{producto.nombre} añadido al carrito.',
            'total_items': total_items,
        })

    messages.success(request, f'{producto.nombre} añadido al carrito.')
    return redirect(request.META.get('HTTP_REFERER', 'usuarios:tienda_home'))


@login_required
def comprar_ahora(request, producto_id):
    Producto = apps.get_model('inventario', 'Producto')
    producto = get_object_or_404(Producto, id=producto_id)

    cantidad = _cantidad_valida(request.GET.get('cantidad', 1))

    request.session['compra_directa'] = {
        'producto_id': producto.id,
        'cantidad': cantidad,
    }
    return redirect('carrito:checkout')


@login_required
def quitar_item(request, item_id):
    item = get_object_or_404(ItemCarrito, id=item_id, carrito__cliente=request.user)
    item.delete()
    return redirect('carrito:ver_carrito')


@login_required
def checkout(request):
    compra_directa = request.session.get('compra_directa')

    if compra_directa:
        Producto = apps.get_model('inventario', 'Producto')
        producto = get_object_or_404(Producto, id=compra_directa['producto_id'])
        cantidad = compra_directa['cantidad']
        items = [{
            'producto': producto,
            'cantidad': cantidad,
            'subtotal': producto.precio * cantidad,
        }]
        total = producto.precio * cantidad
    else:
        carrito, _ = Carrito.objects.get_or_create(cliente=request.user)
        items = carrito.items.all()

        if not items:
            messages.warning(request, 'Tu carrito está vacío.')
            return redirect('carrito:ver_carrito')

        total = carrito.total()

    return render(request, 'checkout.html', {
        'items': items,
        'total': total,
        'compra_directa': bool(compra_directa),
    })


@login_required
def confirmar_pago(request):
    if request.method != 'POST':
        return redirect('carrito:checkout')

    Producto = apps.get_model('inventario', 'Producto')
    compra_directa = request.session.get('compra_directa')

    if compra_directa:
        producto = get_object_or_404(Producto, id=compra_directa['producto_id'])
        items = [{'producto': producto, 'cantidad': compra_directa['cantidad']}]
    else:
        carrito, _ = Carrito.objects.get_or_create(cliente=request.user)
        items = carrito.items.all()

        if not items:
            messages.warning(request, 'Tu carrito está vacío.')
            return redirect('carrito:ver_carrito')

    # Datos capturados en el formulario de checkout
    nombre = request.POST.get('nombre', '').strip()
    telefono = request.POST.get('telefono', '').strip()
    correo = request.POST.get('correo', '').strip()
    direccion = request.POST.get('direccion', '').strip()
    departamento = request.POST.get('departamento', '').strip()
    ciudad = request.POST.get('ciudad', '').strip()
    metodo_pago = request.POST.get('metodo_pago', '').strip()

    if not all([nombre, telefono, correo, direccion, departamento, ciudad, metodo_pago]):
        messages.error(request, 'Por favor completa todos los datos, incluyendo el método de pago.')
        return redirect('carrito:checkout')

    errores = _validar_datos_envio(nombre, telefono, correo, direccion, departamento, ciudad, metodo_pago)
    if errores:
        for error in errores:
            messages.error(request, error)
        return redirect('carrito:checkout')

    Envio = apps.get_model('rastreo', 'Envio')
    HistorialEstado = apps.get_model('rastreo', 'HistorialEstado')

    # ============================================================
    # Validamos stock y descontamos inventario de forma segura.
    # select_for_update() bloquea las filas de Producto involucradas
    # mientras dura la transacción, para que si dos personas compran
    # el mismo producto al mismo tiempo no se descuente stock de más
    # ni se venda algo que ya no hay.
    # ============================================================
    with transaction.atomic():
        productos_y_cantidades = []
        errores_stock = []

        for item in items:
            # item puede ser un dict (compra directa) o un ItemCarrito (carrito normal)
            producto_id_item = item['producto'].id if isinstance(item, dict) else item.producto_id
            cantidad_item = item['cantidad'] if isinstance(item, dict) else item.cantidad

            producto_bloqueado = Producto.objects.select_for_update().get(id=producto_id_item)

            if not producto_bloqueado.esta_activo:
                errores_stock.append(f"'{producto_bloqueado.nombre}' ya no está disponible.")
            elif producto_bloqueado.cantidad_disponible < cantidad_item:
                errores_stock.append(
                    f"Solo quedan {producto_bloqueado.cantidad_disponible} unidad(es) de "
                    f"'{producto_bloqueado.nombre}' (pediste {cantidad_item})."
                )

            productos_y_cantidades.append((producto_bloqueado, cantidad_item))

        if errores_stock:
            for error in errores_stock:
                messages.error(request, error)
            return redirect('carrito:checkout')

        envios_creados = []
        for producto_bloqueado, cantidad_item in productos_y_cantidades:
            # Descontamos el stock del proveedor
            producto_bloqueado.cantidad_disponible -= cantidad_item
            producto_bloqueado.save(update_fields=['cantidad_disponible'])

            numero_guia = str(uuid.uuid4())[:8].upper()
            envio = Envio.objects.create(
                cliente=request.user,
                producto=producto_bloqueado,
                numero_guia=numero_guia,
                cantidad=cantidad_item,
                precio_unitario=producto_bloqueado.precio,
                nombre_destinatario=nombre,
                telefono=telefono,
                correo=correo,
                direccion=direccion,
                departamento=departamento,
                ciudad=ciudad,
                metodo_pago=metodo_pago,
            )
            HistorialEstado.objects.create(envio=envio, estado='preparando', comentario='Pago confirmado (simulado)')
            envios_creados.append(envio)

        if compra_directa:
            del request.session['compra_directa']
        else:
            items.delete()  # vacía el carrito

    messages.success(request, f'¡Pago exitoso! Se generaron {len(envios_creados)} envío(s).')
    return redirect('rastreo:mis_envios')