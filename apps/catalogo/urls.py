from django.urls import path
from . import views

app_name = "catalogo"

urlpatterns = [
    # ---- Libros ----
    path("libros/", views.libros_lista, name="libros_lista"),
    path("libros/nuevo/", views.libro_form, name="libro_nuevo"),
    path("libros/<int:pk>/", views.libro_detalle, name="libro_detalle"),
    path("libros/<int:pk>/editar/", views.libro_form, name="libro_editar"),
    path("libros/<int:pk>/eliminar/", views.libro_eliminar, name="libro_eliminar"),

    # ---- Ejemplares ----
    path("ejemplares/", views.ejemplares_lista, name="ejemplares_lista"),
    path("ejemplares/nuevo/", views.ejemplar_form, name="ejemplar_nuevo"),
    path("ejemplares/<int:pk>/editar/", views.ejemplar_form, name="ejemplar_editar"),
    path("ejemplares/<int:pk>/eliminar/", views.ejemplar_eliminar, name="ejemplar_eliminar"),

    # ---- Categorías ----
    path("categorias/", views.categorias_lista, name="categorias_lista"),
    path("categorias/nuevo/", views.categoria_form, name="categoria_nueva"),
    path("categorias/<int:pk>/editar/", views.categoria_form, name="categoria_editar"),
    path("categorias/<int:pk>/eliminar/", views.categoria_eliminar, name="categoria_eliminar"),
]
