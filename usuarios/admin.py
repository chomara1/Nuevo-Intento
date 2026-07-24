from django.contrib import admin
from .models import Perfil
 
 
@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'rol', 'aprobado', 'telefono', 'ciudad')
    list_filter = ('rol', 'aprobado')
    list_editable = ('aprobado',)  
    search_fields = ('usuario__username', 'usuario__email')
    autocomplete_fields = ['usuario']