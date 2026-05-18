from django.urls import path
from . import views

app_name = "usuarios"

urlpatterns = [
    path("", views.personas_lista, name="personas_lista"),
    path("nuevo/", views.persona_form, name="persona_nueva"),
    path("<int:pk>/", views.persona_detalle, name="persona_detalle"),
    path("<int:pk>/editar/", views.persona_form, name="persona_editar"),
    path("<int:pk>/toggle/", views.persona_toggle, name="persona_toggle"),
    path("<int:pk>/eliminar/", views.persona_eliminar, name="persona_eliminar"),
]
