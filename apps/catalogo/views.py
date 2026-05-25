from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, ProtectedError, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .forms import CapituloForm, CategoriaForm, EjemplarForm, LibroForm
from .models import Capitulo, Categoria, Ejemplar, Libro


# ============================================================
#  LIBROS
# ============================================================

@login_required
def libros_lista(request):
    q = (request.GET.get("q") or "").strip()
    categoria_id = request.GET.get("categoria") or ""

    libros = (
        Libro.objects.select_related("categoria")
        .annotate(
            n_ejemplares=Count("ejemplares", distinct=True),
            n_disponibles=Count(
                "ejemplares",
                filter=Q(ejemplares__estado=Ejemplar.Estado.DISPONIBLE),
                distinct=True,
            ),
        )
        .order_by("titulo")
    )

    if q:
        libros = libros.filter(
            Q(titulo__icontains=q) | Q(autor__icontains=q) | Q(isbn__icontains=q)
        )
    if categoria_id:
        libros = libros.filter(categoria_id=categoria_id)

    paginator = Paginator(libros, 20)
    page = paginator.get_page(request.GET.get("page"))

    return render(request, "catalogo/libros_lista.html", {
        "page": page,
        "q": q,
        "categoria_id": categoria_id,
        "categorias": Categoria.objects.all(),
        "total": paginator.count,
    })


@login_required
def libro_detalle(request, pk):
    libro = get_object_or_404(
        Libro.objects.select_related("categoria").prefetch_related("ejemplares", "capitulos"),
        pk=pk,
    )
    return render(request, "catalogo/libro_detalle.html", {"libro": libro})


@login_required
def libro_form(request, pk=None):
    libro = get_object_or_404(Libro, pk=pk) if pk else None
    if request.method == "POST":
        form = LibroForm(request.POST, instance=libro)
        if form.is_valid():
            obj = form.save()
            messages.success(
                request,
                f"Libro «{obj.titulo}» {'actualizado' if libro else 'creado'} correctamente.",
            )
            return redirect("catalogo:libro_detalle", pk=obj.pk)
    else:
        form = LibroForm(instance=libro)

    return render(request, "catalogo/libro_form.html", {
        "form": form,
        "libro": libro,
        "es_edicion": libro is not None,
    })


@login_required
@require_POST
def libro_eliminar(request, pk):
    libro = get_object_or_404(Libro, pk=pk)
    titulo = libro.titulo
    try:
        libro.delete()
        messages.success(request, f"Libro «{titulo}» eliminado.")
    except ProtectedError:
        messages.error(request, "No se puede eliminar: el libro tiene ejemplares o préstamos asociados.")
        return redirect("catalogo:libro_detalle", pk=pk)
    return redirect("catalogo:libros_lista")


# ============================================================
#  EJEMPLARES
# ============================================================

@login_required
def ejemplares_lista(request):
    q = (request.GET.get("q") or "").strip()
    estado = request.GET.get("estado") or ""
    condicion = request.GET.get("condicion") or ""
    libro_id = request.GET.get("libro") or ""
    categoria_id = request.GET.get("categoria") or ""

    ejemplares = Ejemplar.objects.select_related("libro", "libro__categoria").order_by("codigo")

    if q:
        ejemplares = ejemplares.filter(
            Q(codigo__icontains=q)
            | Q(libro__titulo__icontains=q)
            | Q(clasificacion__icontains=q)
            | Q(ubicacion__icontains=q)
        )
    if estado:
        ejemplares = ejemplares.filter(estado=estado)
    if condicion:
        ejemplares = ejemplares.filter(condicion=condicion)
    if libro_id:
        ejemplares = ejemplares.filter(libro_id=libro_id)
    if categoria_id:
        ejemplares = ejemplares.filter(libro__categoria_id=categoria_id)

    paginator = Paginator(ejemplares, 25)
    page = paginator.get_page(request.GET.get("page"))

    return render(request, "catalogo/ejemplares_lista.html", {
        "page": page,
        "q": q,
        "estado": estado,
        "condicion": condicion,
        "libro_id": libro_id,
        "categoria_id": categoria_id,
        "estados": Ejemplar.Estado.choices,
        "condiciones": Ejemplar.Condicion.choices,
        "categorias": Categoria.objects.order_by("nombre"),
        "total": paginator.count,
    })


@login_required
def ejemplar_form(request, pk=None):
    ejemplar = get_object_or_404(Ejemplar, pk=pk) if pk else None
    libro_preseleccionado = request.GET.get("libro")
    initial = {}
    if libro_preseleccionado and not ejemplar:
        initial["libro"] = libro_preseleccionado

    if request.method == "POST":
        form = EjemplarForm(request.POST, instance=ejemplar)
        if form.is_valid():
            obj = form.save()
            messages.success(
                request,
                f"Ejemplar «{obj.codigo}» {'actualizado' if ejemplar else 'creado'} correctamente.",
            )
            next_url = request.POST.get("next")
            if next_url:
                return redirect(next_url)
            return redirect("catalogo:libro_detalle", pk=obj.libro_id)
    else:
        form = EjemplarForm(instance=ejemplar, initial=initial)

    return render(request, "catalogo/ejemplar_form.html", {
        "form": form,
        "ejemplar": ejemplar,
        "es_edicion": ejemplar is not None,
    })


@login_required
@require_POST
def ejemplar_eliminar(request, pk):
    ejemplar = get_object_or_404(Ejemplar, pk=pk)
    codigo = ejemplar.codigo
    libro_id = ejemplar.libro_id
    try:
        ejemplar.delete()
        messages.success(request, f"Ejemplar «{codigo}» eliminado.")
    except ProtectedError:
        messages.error(request, "No se puede eliminar: el ejemplar tiene préstamos asociados.")
    next_url = request.POST.get("next")
    if next_url:
        return redirect(next_url)
    return redirect("catalogo:libro_detalle", pk=libro_id)


# ============================================================
#  CATEGORÍAS
# ============================================================

@login_required
def categorias_lista(request):
    categorias = Categoria.objects.annotate(
        n_libros=Count("libros", distinct=True),
        n_ejemplares=Count("libros__ejemplares", distinct=True),
    ).order_by("nombre")
    return render(request, "catalogo/categorias_lista.html", {
        "categorias": categorias,
    })


@login_required
def categoria_form(request, pk=None):
    categoria = get_object_or_404(Categoria, pk=pk) if pk else None
    if request.method == "POST":
        form = CategoriaForm(request.POST, instance=categoria)
        if form.is_valid():
            obj = form.save()
            messages.success(
                request,
                f"Categoría «{obj.nombre}» {'actualizada' if categoria else 'creada'} correctamente.",
            )
            return redirect("catalogo:categorias_lista")
    else:
        form = CategoriaForm(instance=categoria)

    return render(request, "catalogo/categoria_form.html", {
        "form": form,
        "categoria": categoria,
        "es_edicion": categoria is not None,
    })


@login_required
@require_POST
def categoria_eliminar(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    nombre = categoria.nombre
    try:
        categoria.delete()
        messages.success(request, f"Categoría «{nombre}» eliminada.")
    except ProtectedError:
        messages.error(request, "No se puede eliminar: la categoría tiene libros asociados.")
    return redirect("catalogo:categorias_lista")


# ============================================================
#  CAPÍTULOS
# ============================================================

@login_required
def capitulo_form(request, libro_pk, pk=None):
    libro = get_object_or_404(Libro, pk=libro_pk)
    capitulo = get_object_or_404(Capitulo, pk=pk, libro=libro) if pk else None

    if request.method == "POST":
        form = CapituloForm(request.POST, instance=capitulo)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.libro = libro
            obj.save()
            messages.success(
                request,
                f"Capítulo «{obj.titulo[:60]}» {'actualizado' if capitulo else 'agregado'} correctamente.",
            )
            return redirect("catalogo:libro_detalle", pk=libro.pk)
    else:
        initial = {}
        if not capitulo:
            max_orden = libro.capitulos.order_by("-orden").values_list("orden", flat=True).first()
            initial["orden"] = (max_orden or 0) + 1
        form = CapituloForm(instance=capitulo, initial=initial)

    return render(request, "catalogo/capitulo_form.html", {
        "form": form,
        "libro": libro,
        "capitulo": capitulo,
        "es_edicion": capitulo is not None,
    })


@login_required
@require_POST
def capitulo_eliminar(request, libro_pk, pk):
    capitulo = get_object_or_404(Capitulo, pk=pk, libro_id=libro_pk)
    titulo = capitulo.titulo
    capitulo.delete()
    messages.success(request, f"Capítulo «{titulo[:60]}» eliminado.")
    return redirect("catalogo:libro_detalle", pk=libro_pk)
