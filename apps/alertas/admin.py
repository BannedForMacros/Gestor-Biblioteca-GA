from django.contrib import admin

from .models import Alerta


@admin.register(Alerta)
class AlertaAdmin(admin.ModelAdmin):
    list_display = ("titulo", "tipo", "nivel", "leida", "creada_en", "prestamo")
    list_filter = ("leida", "tipo", "nivel", "creada_en")
    search_fields = (
        "titulo", "mensaje",
        "prestamo__ejemplar__codigo",
        "prestamo__usuario__codigo_universitario",
        "prestamo__usuario__apellidos",
    )
    ordering = ("leida", "-creada_en")
    readonly_fields = ("creada_en", "actualizada_en", "leida_en")
    list_select_related = ("prestamo",)
