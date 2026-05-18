from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import render
from django.utils import timezone

from apps.catalogo.models import Categoria, Libro, Ejemplar
from apps.usuarios.models import UsuarioBiblioteca
from apps.prestamos.models import Prestamo


@login_required
def dashboard(request):
    hoy = timezone.now().date()

    total_libros = Libro.objects.count()
    total_ejemplares = Ejemplar.objects.count()
    disponibles = Ejemplar.objects.filter(estado=Ejemplar.Estado.DISPONIBLE).count()
    prestados = Ejemplar.objects.filter(estado=Ejemplar.Estado.PRESTADO).count()

    prestamos_activos = Prestamo.objects.filter(estado=Prestamo.Estado.ACTIVO).count()
    prestamos_vencidos = Prestamo.objects.filter(
        estado=Prestamo.Estado.ACTIVO,
        fecha_devolucion_esperada__lt=hoy,
    ).count()
    prestamos_hoy = Prestamo.objects.filter(fecha_prestamo__date=hoy).count()

    porcentaje_disponible = (disponibles / total_ejemplares * 100) if total_ejemplares else 0

    prestamos_recientes = Prestamo.objects.select_related(
        "ejemplar__libro", "ejemplar__libro__categoria", "usuario"
    ).order_by("-fecha_prestamo")[:6]

    libros_por_categoria = (
        Categoria.objects.annotate(
            n_libros=Count("libros", distinct=True),
            n_ejemplares=Count("libros__ejemplares", distinct=True),
            n_disponibles=Count(
                "libros__ejemplares",
                filter=Q(libros__ejemplares__estado=Ejemplar.Estado.DISPONIBLE),
                distinct=True,
            ),
        )
        .order_by("-n_libros")
    )

    total_personas = UsuarioBiblioteca.objects.count()

    return render(request, "home.html", {
        "stats": {
            "total_libros": total_libros,
            "total_ejemplares": total_ejemplares,
            "disponibles": disponibles,
            "prestados": prestados,
            "prestamos_activos": prestamos_activos,
            "prestamos_vencidos": prestamos_vencidos,
            "prestamos_hoy": prestamos_hoy,
            "porcentaje_disponible": round(porcentaje_disponible, 1),
            "total_personas": total_personas,
        },
        "prestamos_recientes": prestamos_recientes,
        "categorias": libros_por_categoria,
    })
