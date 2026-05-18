from django.contrib import admin
from .models import Categoria, Libro, Ejemplar, Capitulo


class EjemplarInline(admin.TabularInline):
    model = Ejemplar
    extra = 0
    fields = ("codigo", "clasificacion", "ubicacion", "estado", "condicion")


class CapituloInline(admin.TabularInline):
    model = Capitulo
    extra = 0
    fields = ("orden", "titulo")


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "codigo_corto")
    search_fields = ("nombre", "codigo_corto")


@admin.register(Libro)
class LibroAdmin(admin.ModelAdmin):
    list_display = ("titulo", "autor", "anio", "categoria", "isbn")
    list_filter = ("categoria", "anio")
    search_fields = ("titulo", "autor", "isbn")
    inlines = [EjemplarInline, CapituloInline]
    list_per_page = 50


@admin.register(Ejemplar)
class EjemplarAdmin(admin.ModelAdmin):
    list_display = ("codigo", "libro", "estado", "condicion", "ubicacion")
    list_filter = ("estado", "condicion", "libro__categoria")
    search_fields = ("codigo", "libro__titulo", "clasificacion")
    list_per_page = 50
    autocomplete_fields = ["libro"]
