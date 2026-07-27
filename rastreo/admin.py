from django.contrib import admin
from .models import Envio, HistorialEstado, EmpresaEnvio


class HistorialInline(admin.TabularInline):
    model = HistorialEstado
    extra = 1


@admin.register(Envio)
class EnvioAdmin(admin.ModelAdmin):
    list_display = ('numero_guia', 'cliente', 'producto', 'estado_actual', 'empresa_envio', 'fecha_creacion')
    inlines = [HistorialInline]


@admin.register(EmpresaEnvio)
class EmpresaEnvioAdmin(admin.ModelAdmin):
    list_display = ('nombre_empresa', 'contacto', 'correo')