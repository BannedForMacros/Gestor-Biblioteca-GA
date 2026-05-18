from django.urls import path
from . import views

app_name = "importacion"

urlpatterns = [
    path("", views.subir_archivo, name="subir"),
    path("resultado/", views.resultado, name="resultado"),
]
