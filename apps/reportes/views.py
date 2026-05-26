import csv
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Count, ExpressionWrapper, F, Q, Sum
from django.db.models.fields import DurationField
from django.db.models.functions import TruncDate
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone

from apps.catalogo.models import Categoria, Ejemplar, Libro
from apps.prestamos.models import Prestamo
from apps.usuarios.models import UsuarioBiblioteca


# ============================================================
#  HOME / DASHBOARD
# ============================================================

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


# ============================================================
#  HELPERS
# ============================================================

def _parse_rango(request, dias_default=30):
    """Devuelve (desde, hasta) como datetime.date a partir de request.GET."""
    hoy = timezone.now().date()
    raw_desde = request.GET.get("desde") or ""
    raw_hasta = request.GET.get("hasta") or ""

    try:
        desde = timezone.datetime.strptime(raw_desde, "%Y-%m-%d").date() if raw_desde else (hoy - timedelta(days=dias_default))
    except ValueError:
        desde = hoy - timedelta(days=dias_default)
    try:
        hasta = timezone.datetime.strptime(raw_hasta, "%Y-%m-%d").date() if raw_hasta else hoy
    except ValueError:
        hasta = hoy

    if desde > hasta:
        desde, hasta = hasta, desde
    return desde, hasta


def _csv_response(filename, header, rows):
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    response.write("﻿")  # BOM para Excel
    writer = csv.writer(response, delimiter=";")
    writer.writerow(header)
    for r in rows:
        writer.writerow(r)
    return response


# ============================================================
#  ÍNDICE DE REPORTES
# ============================================================

@login_required
def indice(request):
    hoy = timezone.now().date()
    return render(request, "reportes/indice.html", {
        "kpis": {
            "total_libros": Libro.objects.count(),
            "total_ejemplares": Ejemplar.objects.count(),
            "prestamos_activos": Prestamo.objects.filter(estado=Prestamo.Estado.ACTIVO).count(),
            "vencidos": Prestamo.objects.filter(
                estado=Prestamo.Estado.ACTIVO, fecha_devolucion_esperada__lt=hoy
            ).count(),
        },
    })


# ============================================================
#  1. LIBROS MÁS PRESTADOS
# ============================================================

@login_required
def libros_mas_prestados(request):
    desde, hasta = _parse_rango(request, dias_default=90)

    libros = (
        Libro.objects.annotate(
            n_prestamos=Count(
                "ejemplares__prestamos",
                filter=Q(
                    ejemplares__prestamos__fecha_prestamo__date__gte=desde,
                    ejemplares__prestamos__fecha_prestamo__date__lte=hasta,
                ),
                distinct=True,
            ),
            n_ejemplares=Count("ejemplares", distinct=True),
        )
        .filter(n_prestamos__gt=0)
        .select_related("categoria")
        .order_by("-n_prestamos", "titulo")[:50]
    )

    if request.GET.get("export") == "csv":
        rows = [
            (l.titulo, l.autor, l.categoria.nombre, l.n_ejemplares, l.n_prestamos)
            for l in libros
        ]
        return _csv_response(
            f"libros_mas_prestados_{desde}_{hasta}.csv",
            ["Título", "Autor", "Categoría", "Ejemplares", "Préstamos"],
            rows,
        )

    return render(request, "reportes/libros_mas_prestados.html", {
        "libros": libros,
        "desde": desde,
        "hasta": hasta,
        "max_prestamos": libros[0].n_prestamos if libros else 0,
    })


# ============================================================
#  2. USUARIOS MÁS FRECUENTES
# ============================================================

@login_required
def usuarios_frecuentes(request):
    desde, hasta = _parse_rango(request, dias_default=90)

    usuarios = (
        UsuarioBiblioteca.objects.annotate(
            n_prestamos=Count(
                "prestamos",
                filter=Q(
                    prestamos__fecha_prestamo__date__gte=desde,
                    prestamos__fecha_prestamo__date__lte=hasta,
                ),
                distinct=True,
            ),
            n_activos=Count(
                "prestamos",
                filter=Q(prestamos__estado=Prestamo.Estado.ACTIVO),
                distinct=True,
            ),
        )
        .filter(n_prestamos__gt=0)
        .order_by("-n_prestamos", "apellidos")[:50]
    )

    if request.GET.get("export") == "csv":
        rows = [
            (
                u.codigo_universitario, u.apellidos, u.nombres,
                u.get_tipo_display(), u.escuela,
                u.n_prestamos, u.n_activos,
            )
            for u in usuarios
        ]
        return _csv_response(
            f"usuarios_frecuentes_{desde}_{hasta}.csv",
            ["Código", "Apellidos", "Nombres", "Tipo", "Escuela", "Préstamos en rango", "Activos"],
            rows,
        )

    return render(request, "reportes/usuarios_frecuentes.html", {
        "usuarios": usuarios,
        "desde": desde,
        "hasta": hasta,
        "max_prestamos": usuarios[0].n_prestamos if usuarios else 0,
    })


# ============================================================
#  3. ESTADO DEL INVENTARIO
# ============================================================

@login_required
def inventario(request):
    total_ej = Ejemplar.objects.count() or 1  # evitar div por cero

    # Filtros activos (drill-down dentro de la misma página)
    f_estado = request.GET.get("estado") or ""
    f_condicion = request.GET.get("condicion") or ""
    f_categoria = request.GET.get("categoria") or ""

    por_estado_qs = (
        Ejemplar.objects.values("estado")
        .annotate(n=Count("id"))
        .order_by("-n")
    )
    estado_labels = dict(Ejemplar.Estado.choices)
    por_estado = [
        {
            "codigo": row["estado"],
            "label": estado_labels.get(row["estado"], row["estado"]),
            "n": row["n"],
            "pct": round(row["n"] / total_ej * 100, 1),
        }
        for row in por_estado_qs
    ]

    por_condicion_qs = (
        Ejemplar.objects.values("condicion")
        .annotate(n=Count("id"))
        .order_by("-n")
    )
    cond_labels = dict(Ejemplar.Condicion.choices)
    por_condicion = [
        {
            "codigo": row["condicion"],
            "label": cond_labels.get(row["condicion"], row["condicion"]),
            "n": row["n"],
            "pct": round(row["n"] / total_ej * 100, 1),
        }
        for row in por_condicion_qs
    ]

    por_categoria = (
        Categoria.objects.annotate(
            n_libros=Count("libros", distinct=True),
            n_ejemplares=Count("libros__ejemplares", distinct=True),
            n_disponibles=Count(
                "libros__ejemplares",
                filter=Q(libros__ejemplares__estado=Ejemplar.Estado.DISPONIBLE),
                distinct=True,
            ),
            n_prestados=Count(
                "libros__ejemplares",
                filter=Q(libros__ejemplares__estado=Ejemplar.Estado.PRESTADO),
                distinct=True,
            ),
        )
        .order_by("-n_ejemplares")
    )

    libros_sin_ejemplares = (
        Libro.objects.annotate(n=Count("ejemplares"))
        .filter(n=0)
        .select_related("categoria")
        .order_by("titulo")[:30]
    )

    # Lista filtrada inline (drill-down)
    detalle_ejemplares = None
    filtro_activo = bool(f_estado or f_condicion or f_categoria)
    categoria_seleccionada = None
    if filtro_activo:
        qs = Ejemplar.objects.select_related("libro", "libro__categoria").order_by("codigo")
        if f_estado:
            qs = qs.filter(estado=f_estado)
        if f_condicion:
            qs = qs.filter(condicion=f_condicion)
        if f_categoria:
            qs = qs.filter(libro__categoria_id=f_categoria)
            categoria_seleccionada = Categoria.objects.filter(pk=f_categoria).first()
        detalle_ejemplares = qs[:100]
        detalle_total = qs.count()
    else:
        detalle_total = 0

    if request.GET.get("export") == "csv":
        rows = [
            (c.nombre, c.codigo_corto, c.n_libros, c.n_ejemplares, c.n_disponibles, c.n_prestados)
            for c in por_categoria
        ]
        return _csv_response(
            f"inventario_{timezone.now().date()}.csv",
            ["Categoría", "Código", "Libros", "Ejemplares", "Disponibles", "Prestados"],
            rows,
        )

    return render(request, "reportes/inventario.html", {
        "total_ejemplares": Ejemplar.objects.count(),
        "total_libros": Libro.objects.count(),
        "por_estado": por_estado,
        "por_condicion": por_condicion,
        "por_categoria": por_categoria,
        "libros_sin_ejemplares": libros_sin_ejemplares,
        "n_sin_ejemplares": Libro.objects.annotate(n=Count("ejemplares")).filter(n=0).count(),
        # Drill-down inline
        "f_estado": f_estado,
        "f_condicion": f_condicion,
        "f_categoria": f_categoria,
        "filtro_activo": filtro_activo,
        "categoria_seleccionada": categoria_seleccionada,
        "detalle_ejemplares": detalle_ejemplares,
        "detalle_total": detalle_total,
        "estado_label": estado_labels.get(f_estado, ""),
        "condicion_label": cond_labels.get(f_condicion, ""),
    })


# ============================================================
#  4. PRÉSTAMOS POR PERÍODO
# ============================================================

@login_required
def prestamos_periodo(request):
    desde, hasta = _parse_rango(request, dias_default=30)

    base = Prestamo.objects.filter(
        fecha_prestamo__date__gte=desde,
        fecha_prestamo__date__lte=hasta,
    )

    total = base.count()
    devueltos = base.filter(estado=Prestamo.Estado.DEVUELTO).count()
    activos = base.filter(estado=Prestamo.Estado.ACTIVO).count()

    por_dia_qs = (
        base.annotate(dia=TruncDate("fecha_prestamo"))
        .values("dia")
        .annotate(n=Count("id"))
        .order_by("dia")
    )
    por_dia = list(por_dia_qs)
    max_dia = max((r["n"] for r in por_dia), default=0)

    por_categoria = (
        Categoria.objects.annotate(
            n=Count(
                "libros__ejemplares__prestamos",
                filter=Q(
                    libros__ejemplares__prestamos__fecha_prestamo__date__gte=desde,
                    libros__ejemplares__prestamos__fecha_prestamo__date__lte=hasta,
                ),
                distinct=True,
            )
        )
        .filter(n__gt=0)
        .order_by("-n")
    )

    if request.GET.get("export") == "csv":
        rows = []
        for p in base.select_related("ejemplar__libro", "usuario").order_by("fecha_prestamo"):
            rows.append((
                p.fecha_prestamo.strftime("%Y-%m-%d %H:%M"),
                p.ejemplar.codigo,
                p.ejemplar.libro.titulo,
                p.usuario.codigo_universitario,
                p.usuario.nombre_completo,
                p.fecha_devolucion_esperada.strftime("%Y-%m-%d"),
                p.fecha_devolucion_real.strftime("%Y-%m-%d %H:%M") if p.fecha_devolucion_real else "",
                p.get_estado_display(),
            ))
        return _csv_response(
            f"prestamos_{desde}_{hasta}.csv",
            ["Fecha", "Código ejemplar", "Título", "Código persona", "Persona",
             "Devolución esperada", "Devolución real", "Estado"],
            rows,
        )

    return render(request, "reportes/prestamos_periodo.html", {
        "desde": desde,
        "hasta": hasta,
        "total": total,
        "devueltos": devueltos,
        "activos": activos,
        "por_dia": por_dia,
        "max_dia": max_dia,
        "por_categoria": por_categoria,
    })


# ============================================================
#  5. NO DEVUELTOS / VENCIDOS
# ============================================================

@login_required
def no_devueltos(request):
    hoy = timezone.now().date()

    base = (
        Prestamo.objects.filter(
            estado=Prestamo.Estado.ACTIVO,
            fecha_devolucion_esperada__lt=hoy,
        )
        .select_related("ejemplar__libro", "ejemplar__libro__categoria", "usuario")
        .annotate(retraso=hoy - F("fecha_devolucion_esperada"))
        .order_by("fecha_devolucion_esperada")
    )

    if request.GET.get("export") == "csv":
        rows = []
        for p in base:
            dias = (hoy - p.fecha_devolucion_esperada).days
            rows.append((
                p.ejemplar.codigo,
                p.ejemplar.libro.titulo,
                p.usuario.codigo_universitario,
                p.usuario.nombre_completo,
                p.usuario.telefono,
                p.usuario.correo,
                p.fecha_prestamo.strftime("%Y-%m-%d"),
                p.fecha_devolucion_esperada.strftime("%Y-%m-%d"),
                dias,
            ))
        return _csv_response(
            f"libros_no_devueltos_{hoy}.csv",
            ["Código ejemplar", "Título", "Código persona", "Persona",
             "Teléfono", "Correo", "Fecha préstamo", "Devolución esperada", "Días de retraso"],
            rows,
        )

    return render(request, "reportes/no_devueltos.html", {
        "prestamos": base,
        "hoy": hoy,
        "total": base.count(),
    })


# ============================================================
#  6. HISTORIAL DE ENTREGAS EN DESFASE
# ============================================================

@login_required
def entregas_desfase(request):
    desde, hasta = _parse_rango(request, dias_default=90)
    hoy = timezone.now().date()
    filtro = request.GET.get("filtro", "todos")

    devueltos_tarde = Q(
        estado=Prestamo.Estado.DEVUELTO,
        fecha_devolucion_real__date__gt=F("fecha_devolucion_esperada"),
        fecha_prestamo__date__gte=desde,
        fecha_prestamo__date__lte=hasta,
    )
    activos_vencidos = Q(
        estado=Prestamo.Estado.ACTIVO,
        fecha_devolucion_esperada__lt=hoy,
        fecha_prestamo__date__gte=desde,
        fecha_prestamo__date__lte=hasta,
    )

    if filtro == "devueltos":
        q = devueltos_tarde
    elif filtro == "pendientes":
        q = activos_vencidos
    else:
        q = devueltos_tarde | activos_vencidos

    base = (
        Prestamo.objects.filter(q)
        .select_related("ejemplar__libro", "ejemplar__libro__categoria", "usuario")
        .order_by("-fecha_prestamo")
    )

    total = base.count()
    n_devueltos_tarde = Prestamo.objects.filter(devueltos_tarde).count()
    n_pendientes = Prestamo.objects.filter(activos_vencidos).count()

    def _dias_desfase(p):
        if p.estado == Prestamo.Estado.DEVUELTO and p.fecha_devolucion_real:
            return (p.fecha_devolucion_real.date() - p.fecha_devolucion_esperada).days
        if p.estado == Prestamo.Estado.ACTIVO:
            return (hoy - p.fecha_devolucion_esperada).days
        return 0

    prestamos_con_desfase = []
    for p in base:
        p.dias_desfase = _dias_desfase(p)
        prestamos_con_desfase.append(p)

    if request.GET.get("export") == "csv":
        rows = []
        for p in prestamos_con_desfase:
            rows.append((
                p.ejemplar.codigo,
                p.ejemplar.libro.titulo,
                p.usuario.codigo_universitario,
                p.usuario.nombre_completo,
                p.usuario.escuela,
                p.fecha_prestamo.strftime("%Y-%m-%d"),
                p.fecha_devolucion_esperada.strftime("%Y-%m-%d"),
                p.fecha_devolucion_real.strftime("%Y-%m-%d %H:%M") if p.fecha_devolucion_real else "Pendiente",
                p.dias_desfase,
                p.get_estado_display(),
            ))
        return _csv_response(
            f"entregas_desfase_{desde}_{hasta}.csv",
            ["Código ejemplar", "Título", "Código persona", "Persona", "Escuela",
             "Fecha préstamo", "Devolución esperada", "Devolución real",
             "Días de desfase", "Estado"],
            rows,
        )

    return render(request, "reportes/entregas_desfase.html", {
        "prestamos": prestamos_con_desfase,
        "desde": desde,
        "hasta": hasta,
        "total": total,
        "n_devueltos_tarde": n_devueltos_tarde,
        "n_pendientes": n_pendientes,
        "filtro": filtro,
        "hoy": hoy,
    })
