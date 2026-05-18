from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.urls import reverse

from .forms import ImportarExcelForm
from .parsers import importar_excel, CONFIG_ESCUELAS


@login_required
def subir_archivo(request):
    """Pantalla 1: formulario de carga de Excel."""
    if request.method == "POST":
        form = ImportarExcelForm(request.POST, request.FILES)
        if form.is_valid():
            archivo = form.cleaned_data["archivo"]
            categoria_codigo = form.cleaned_data["categoria"]
            try:
                resultado = importar_excel(archivo, categoria_codigo)
            except Exception as e:
                return render(request, "importacion/error.html", {
                    "mensaje_error": str(e),
                    "tipo_error": type(e).__name__,
                })

            request.session["ultimo_resultado_importacion"] = {
                "categoria_nombre": CONFIG_ESCUELAS[categoria_codigo]["nombre"],
                "categoria_codigo": categoria_codigo,
                "archivo_nombre": archivo.name,
                "libros_creados": resultado.libros_creados,
                "libros_existentes": resultado.libros_existentes,
                "ejemplares_creados": resultado.ejemplares_creados,
                "ejemplares_existentes": resultado.ejemplares_existentes,
                "capitulos_creados": resultado.capitulos_creados,
                "filas_omitidas": resultado.filas_omitidas,
                "advertencias": resultado.advertencias,
            }
            return redirect(reverse("importacion:resultado"))
    else:
        form = ImportarExcelForm()

    categorias_info = [
        {"codigo": cod, "nombre": cfg["nombre"]}
        for cod, cfg in CONFIG_ESCUELAS.items()
    ]
    return render(request, "importacion/subir.html", {
        "form": form,
        "categorias_info": categorias_info,
    })


@login_required
def resultado(request):
    """Pantalla 2: muestra el resumen de la última importación."""
    datos = request.session.get("ultimo_resultado_importacion")
    if not datos:
        return redirect(reverse("importacion:subir"))
    return render(request, "importacion/resultado.html", {"r": datos})
