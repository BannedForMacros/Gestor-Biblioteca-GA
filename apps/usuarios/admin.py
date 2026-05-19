from django.contrib import admin

from .models import Sancion, UsuarioBiblioteca


@admin.register(UsuarioBiblioteca)
class UsuarioBibliotecaAdmin(admin.ModelAdmin):
    list_display = ("codigo_universitario", "apellidos", "nombres", "tipo", "escuela", "activo")
    list_filter = ("tipo", "escuela", "activo")
    search_fields = ("codigo_universitario", "nombres", "apellidos", "correo")
    list_per_page = 50


@admin.register(Sancion)
class SancionAdmin(admin.ModelAdmin):
    list_display = (
        "usuario", "motivo", "tipo", "fecha_inicio", "fecha_fin",
        "activa", "creada_en",
    )
    list_filter = ("activa", "tipo", "motivo", "fecha_inicio")
    search_fields = (
        "usuario__codigo_universitario",
        "usuario__nombres",
        "usuario__apellidos",
        "descripcion",
    )
    readonly_fields = ("creada_en", "levantada_en")
    autocomplete_fields = ("usuario", "prestamo")
    list_select_related = ("usuario",)
