from django.contrib import admin
from .models import Envio, HistorialEstado

class HistorialInline(admin.TabularInline):
    model = HistorialEstado
    extra = 1

@admin.register(Envio)
class EnvioAdmin(admin.ModelAdmin):
    list_display = ('numero_guia', 'cliente', 'producto', 'estado_actual', 'fecha_creacion')
    inlines = [HistorialInline]