from django.urls import path

from . import views

app_name = "alertas"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("marcar/<int:pk>/", views.marcar_leida, name="marcar_leida"),
    path("marcar-todas/", views.marcar_todas_leidas, name="marcar_todas"),
    path("regenerar/", views.regenerar, name="regenerar"),
]
