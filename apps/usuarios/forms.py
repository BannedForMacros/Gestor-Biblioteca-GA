from django import forms
from .models import UsuarioBiblioteca


BASE_INPUT = (
    "w-full px-4 py-2.5 rounded-xl border-2 border-slate-200 bg-white "
    "shadow-sm focus:border-marca-500 focus:ring-0 focus:shadow-md "
    "transition-all placeholder:text-slate-400"
)
BASE_SELECT = BASE_INPUT + " appearance-none"


class UsuarioBibliotecaForm(forms.ModelForm):
    class Meta:
        model = UsuarioBiblioteca
        fields = [
            "codigo_universitario", "nombres", "apellidos",
            "tipo", "escuela", "correo", "telefono", "activo",
        ]
        widgets = {
            "codigo_universitario": forms.TextInput(attrs={"class": BASE_INPUT, "placeholder": "Ej: 2020138271"}),
            "nombres": forms.TextInput(attrs={"class": BASE_INPUT, "placeholder": "Ej: Cesar Junior"}),
            "apellidos": forms.TextInput(attrs={"class": BASE_INPUT, "placeholder": "Ej: Ramos Mac"}),
            "tipo": forms.Select(attrs={"class": BASE_SELECT}),
            "escuela": forms.TextInput(attrs={"class": BASE_INPUT, "placeholder": "Ej: Economía"}),
            "correo": forms.EmailInput(attrs={"class": BASE_INPUT, "placeholder": "ejemplo@unprg.edu.pe"}),
            "telefono": forms.TextInput(attrs={"class": BASE_INPUT, "placeholder": "Ej: 987654321"}),
        }
