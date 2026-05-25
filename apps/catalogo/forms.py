from django import forms
from .models import Libro, Ejemplar, Categoria, Capitulo


BASE_INPUT = (
    "w-full px-4 py-2.5 rounded-xl border-2 border-slate-200 bg-white "
    "shadow-sm focus:border-marca-500 focus:ring-0 focus:shadow-md "
    "transition-all placeholder:text-slate-400"
)
BASE_SELECT = BASE_INPUT + " appearance-none"
BASE_TEXTAREA = BASE_INPUT


class LibroForm(forms.ModelForm):
    class Meta:
        model = Libro
        fields = [
            "titulo", "autor", "anio", "editorial",
            "isbn", "numero_paginas", "categoria",
        ]
        widgets = {
            "titulo": forms.TextInput(attrs={"class": BASE_INPUT, "placeholder": "Ej: Macroeconomía"}),
            "autor": forms.TextInput(attrs={"class": BASE_INPUT, "placeholder": "Ej: N. Gregory Mankiw"}),
            "anio": forms.NumberInput(attrs={"class": BASE_INPUT, "placeholder": "Ej: 2020", "min": 1500, "max": 2100}),
            "editorial": forms.TextInput(attrs={"class": BASE_INPUT, "placeholder": "Ej: Pearson"}),
            "isbn": forms.TextInput(attrs={"class": BASE_INPUT, "placeholder": "Ej: 978-607-32-4566-5"}),
            "numero_paginas": forms.NumberInput(attrs={"class": BASE_INPUT, "placeholder": "Ej: 480", "min": 1}),
            "categoria": forms.Select(attrs={"class": BASE_SELECT}),
        }


class EjemplarForm(forms.ModelForm):
    class Meta:
        model = Ejemplar
        fields = ["libro", "codigo", "clasificacion", "ubicacion", "estado", "condicion"]
        widgets = {
            "libro": forms.Select(attrs={"class": BASE_SELECT}),
            "codigo": forms.TextInput(attrs={"class": BASE_INPUT, "placeholder": "Ej: L-ECON-0001"}),
            "clasificacion": forms.TextInput(attrs={"class": BASE_INPUT, "placeholder": "Ej: 338.5 M59"}),
            "ubicacion": forms.TextInput(attrs={"class": BASE_INPUT, "placeholder": "Ej: Estante A-3"}),
            "estado": forms.Select(attrs={"class": BASE_SELECT}),
            "condicion": forms.Select(attrs={"class": BASE_SELECT}),
        }


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ["nombre", "codigo_corto"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": BASE_INPUT, "placeholder": "Ej: Economía"}),
            "codigo_corto": forms.TextInput(attrs={"class": BASE_INPUT, "placeholder": "Ej: ECON"}),
        }


class CapituloForm(forms.ModelForm):
    class Meta:
        model = Capitulo
        fields = ["orden", "titulo"]
        widgets = {
            "orden": forms.NumberInput(attrs={"class": BASE_INPUT, "placeholder": "Ej: 1", "min": 1}),
            "titulo": forms.TextInput(attrs={"class": BASE_INPUT, "placeholder": "Ej: Introducción a la Macroeconomía"}),
        }
