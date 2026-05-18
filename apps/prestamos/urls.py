from django.urls import path
from . import views

app_name = "prestamos"

urlpatterns = [
    path("", views.prestamos_lista, name="lista"),
    path("nuevo/", views.nuevo, name="nuevo"),
    path("<int:prestamo_id>/devolver/", views.devolver, name="devolver"),

    # Combobox de ejemplar
    path("ej/opciones/", views.opciones_ejemplar, name="opciones_ejemplar"),
    path("ej/seleccionar/", views.seleccionar_ejemplar, name="seleccionar_ejemplar"),
    path("ej/reset/", views.reset_ejemplar, name="reset_ejemplar"),

    # Combobox de usuario
    path("us/opciones/", views.opciones_usuario, name="opciones_usuario"),
    path("us/seleccionar/", views.seleccionar_usuario, name="seleccionar_usuario"),
    path("us/reset/", views.reset_usuario, name="reset_usuario"),

    # Confirmar préstamo
    path("confirmar/", views.confirmar, name="confirmar"),
    path("recibo/<int:prestamo_id>/", views.recibo, name="recibo"),
]
