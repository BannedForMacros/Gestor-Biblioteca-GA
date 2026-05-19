from datetime import timedelta

from django import forms
from django.utils import timezone

from .models import Sancion, UsuarioBiblioteca


BASE_INPUT = (
    "w-full px-4 py-2.5 rounded-xl border-2 border-slate-200 bg-white "
    "shadow-sm focus:border-marca-500 focus:ring-0 focus:shadow-md "
    "transition-all placeholder:text-slate-400"
)
BASE_SELECT = BASE_INPUT + " appearance-none"
BASE_TEXTAREA = BASE_INPUT


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


class SancionForm(forms.ModelForm):
    dias_bloqueo = forms.IntegerField(
        required=False, min_value=1, max_value=365, initial=7,
        label="Días de bloqueo",
        help_text="Solo para bloqueo temporal.",
        widget=forms.NumberInput(attrs={"class": BASE_INPUT, "placeholder": "7"}),
    )

    class Meta:
        model = Sancion
        fields = ["motivo", "tipo", "descripcion"]
        widgets = {
            "motivo": forms.Select(attrs={"class": BASE_SELECT}),
            "tipo": forms.Select(attrs={"class": BASE_SELECT}),
            "descripcion": forms.Textarea(attrs={
                "class": BASE_TEXTAREA, "rows": 3,
                "placeholder": "Ej: Devolvió el libro 5 días tarde y con páginas dobladas.",
            }),
        }

    def clean(self):
        cleaned = super().clean()
        tipo = cleaned.get("tipo")
        dias = cleaned.get("dias_bloqueo")
        if tipo == Sancion.Tipo.BLOQUEO_TEMPORAL and not dias:
            self.add_error("dias_bloqueo", "Indique cuántos días debe durar el bloqueo.")
        return cleaned

    def save(self, commit=True, usuario=None, prestamo=None, creada_por=None):
        instance = super().save(commit=False)
        if usuario is not None:
            instance.usuario = usuario
        if prestamo is not None:
            instance.prestamo = prestamo
        if creada_por is not None and getattr(creada_por, "is_authenticated", False):
            instance.creada_por = creada_por

        if instance.tipo == Sancion.Tipo.BLOQUEO_TEMPORAL:
            dias = self.cleaned_data.get("dias_bloqueo") or 7
            instance.fecha_fin = timezone.now().date() + timedelta(days=dias)
        else:
            instance.fecha_fin = None

        if commit:
            instance.save()
        return instance
