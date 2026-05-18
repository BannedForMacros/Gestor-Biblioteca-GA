from django import forms

from .parsers import CONFIG_ESCUELAS


CATEGORIA_CHOICES = [
    (codigo, cfg["nombre"]) for codigo, cfg in CONFIG_ESCUELAS.items()
]


class ImportarExcelForm(forms.Form):
    categoria = forms.ChoiceField(
        choices=CATEGORIA_CHOICES,
        widget=forms.RadioSelect,
        label="¿A qué escuela pertenece el archivo?",
        error_messages={"required": "Por favor, seleccione una escuela."},
    )
    archivo = forms.FileField(
        label="Archivo Excel (.xlsx)",
        error_messages={"required": "Debe seleccionar un archivo Excel para continuar."},
    )

    def clean_archivo(self):
        archivo = self.cleaned_data["archivo"]
        nombre = archivo.name.lower()
        if not nombre.endswith(".xlsx"):
            raise forms.ValidationError(
                "El archivo debe ser de tipo Excel (.xlsx). "
                "Otros formatos no son compatibles."
            )
        if archivo.size > 50 * 1024 * 1024:
            raise forms.ValidationError(
                "El archivo es muy grande (máximo permitido: 50 MB)."
            )
        return archivo
