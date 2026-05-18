from django.urls import path
from . import views

app_name = "prestamos"

urlpatterns = [
    path("nuevo/", views.nuevo, name="nuevo"),
    path("buscar-ejemplar/", views.buscar_ejemplar, name="buscar_ejemplar"),
    path("buscar-usuario/", views.buscar_usuario, name="buscar_usuario"),
    path("confirmar/", views.confirmar, name="confirmar"),
    path("recibo/<int:prestamo_id>/", views.recibo, name="recibo"),
]
