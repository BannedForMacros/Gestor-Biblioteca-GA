from django.contrib import admin
from .models import UsuarioBiblioteca


@admin.register(UsuarioBiblioteca)
class UsuarioBibliotecaAdmin(admin.ModelAdmin):
    list_display = ("codigo_universitario", "apellidos", "nombres", "tipo", "escuela", "activo")
    list_filter = ("tipo", "escuela", "activo")
    search_fields = ("codigo_universitario", "nombres", "apellidos", "correo")
    list_per_page = 50
