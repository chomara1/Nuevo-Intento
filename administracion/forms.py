from django import forms
from .models import DisenoSitio


class DisenoSitioForm(forms.ModelForm):
    class Meta:
        model = DisenoSitio
        fields = [
            'slide1_titulo', 'slide1_texto', 'slide1_color_a', 'slide1_color_b',
            'slide2_titulo', 'slide2_texto', 'slide2_color_a', 'slide2_color_b',
            'slide3_titulo', 'slide3_texto', 'slide3_color_a', 'slide3_color_b',
        ]
        widgets = {
            'slide1_texto': forms.Textarea(attrs={'rows': 2}),
            'slide2_texto': forms.Textarea(attrs={'rows': 2}),
            'slide3_texto': forms.Textarea(attrs={'rows': 2}),
            'slide1_color_a': forms.TextInput(attrs={'type': 'color'}),
            'slide1_color_b': forms.TextInput(attrs={'type': 'color'}),
            'slide2_color_a': forms.TextInput(attrs={'type': 'color'}),
            'slide2_color_b': forms.TextInput(attrs={'type': 'color'}),
            'slide3_color_a': forms.TextInput(attrs={'type': 'color'}),
            'slide3_color_b': forms.TextInput(attrs={'type': 'color'}),
        }
        labels = {
            'slide1_titulo': 'Título — Slide 1',
            'slide1_texto': 'Texto — Slide 1',
            'slide1_color_a': 'Color inicial degradado',
            'slide1_color_b': 'Color final degradado',
            'slide2_titulo': 'Título — Slide 2',
            'slide2_texto': 'Texto — Slide 2',
            'slide2_color_a': 'Color inicial degradado',
            'slide2_color_b': 'Color final degradado',
            'slide3_titulo': 'Título — Slide 3',
            'slide3_texto': 'Texto — Slide 3',
            'slide3_color_a': 'Color inicial degradado',
            'slide3_color_b': 'Color final degradado',
        }