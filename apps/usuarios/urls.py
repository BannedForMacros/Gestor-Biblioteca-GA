from django.urls import path
from . import views

app_name = "usuarios"

urlpatterns = [
    path("", views.personas_lista, name="personas_lista"),
    path("nuevo/", views.persona_form, name="persona_nueva"),
    path("sanciones/", views.sanciones_lista, name="sanciones_lista"),

    path("<int:pk>/", views.persona_detalle, name="persona_detalle"),
    path("<int:pk>/editar/", views.persona_form, name="persona_editar"),
    path("<int:pk>/toggle/", views.persona_toggle, name="persona_toggle"),
    path("<int:pk>/eliminar/", views.persona_eliminar, name="persona_eliminar"),

    # Sanciones
    path("<int:persona_id>/sancion/aplicar/", views.sancion_aplicar, name="sancion_aplicar"),
    path("sancion/<int:pk>/levantar/", views.sancion_levantar, name="sancion_levantar"),
]
