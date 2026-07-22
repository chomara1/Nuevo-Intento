from django.contrib import admin
from .models import DisenoSitio


@admin.register(DisenoSitio)
class DisenoSitioAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Slide 1', {'fields': ('slide1_titulo', 'slide1_texto', 'slide1_color_a', 'slide1_color_b')}),
        ('Slide 2', {'fields': ('slide2_titulo', 'slide2_texto', 'slide2_color_a', 'slide2_color_b')}),
        ('Slide 3', {'fields': ('slide3_titulo', 'slide3_texto', 'slide3_color_a', 'slide3_color_b')}),
    )

    def has_add_permission(self, request):
        # Ya existe el registro pk=1 desde el primer .cargar(); no se permite crear otro
        return not DisenoSitio.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False