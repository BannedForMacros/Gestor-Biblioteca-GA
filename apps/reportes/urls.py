from django.urls import path
from . import views

app_name = "reportes"

urlpatterns = [
    path("", views.indice, name="indice"),
    path("libros-mas-prestados/", views.libros_mas_prestados, name="libros_mas_prestados"),
    path("usuarios-frecuentes/", views.usuarios_frecuentes, name="usuarios_frecuentes"),
    path("inventario/", views.inventario, name="inventario"),
    path("prestamos-periodo/", views.prestamos_periodo, name="prestamos_periodo"),
    path("no-devueltos/", views.no_devueltos, name="no_devueltos"),
]
