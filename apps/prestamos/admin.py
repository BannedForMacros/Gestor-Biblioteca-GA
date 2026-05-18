from django.contrib import admin
from .models import Prestamo


@admin.register(Prestamo)
class PrestamoAdmin(admin.ModelAdmin):
    list_display = (
        "ejemplar", "usuario", "fecha_prestamo",
        "fecha_devolucion_esperada", "estado",
    )
    list_filter = ("estado", "fecha_prestamo")
    search_fields = (
        "ejemplar__codigo", "ejemplar__libro__titulo",
        "usuario__codigo_universitario", "usuario__apellidos",
    )
    autocomplete_fields = ["ejemplar", "usuario"]
    date_hierarchy = "fecha_prestamo"
    list_per_page = 50
