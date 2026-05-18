from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponseBadRequest, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST, require_GET

from apps.catalogo.models import Ejemplar
from apps.usuarios.models import UsuarioBiblioteca
from .models import Prestamo


@login_required
def prestamos_lista(request):
    q = (request.GET.get("q") or "").strip()
    estado = request.GET.get("estado") or "ACTIVO"
    hoy = timezone.now().date()

    prestamos = (
        Prestamo.objects.select_related(
            "ejemplar__libro", "ejemplar__libro__categoria", "usuario", "registrado_por"
        ).order_by("-fecha_prestamo")
    )

    if estado == "VENCIDO":
        prestamos = prestamos.filter(estado=Prestamo.Estado.ACTIVO, fecha_devolucion_esperada__lt=hoy)
    elif estado in {"ACTIVO", "DEVUELTO"}:
        prestamos = prestamos.filter(estado=estado)
    # estado "" -> todos

    if q:
        prestamos = prestamos.filter(
            Q(ejemplar__codigo__icontains=q)
            | Q(ejemplar__libro__titulo__icontains=q)
            | Q(usuario__nombres__icontains=q)
            | Q(usuario__apellidos__icontains=q)
            | Q(usuario__codigo_universitario__icontains=q)
        )

    paginator = Paginator(prestamos, 20)
    page = paginator.get_page(request.GET.get("page"))

    # Stats para los chips
    stats = {
        "activos": Prestamo.objects.filter(estado=Prestamo.Estado.ACTIVO).count(),
        "vencidos": Prestamo.objects.filter(
            estado=Prestamo.Estado.ACTIVO, fecha_devolucion_esperada__lt=hoy
        ).count(),
        "devueltos": Prestamo.objects.filter(estado=Prestamo.Estado.DEVUELTO).count(),
        "total": Prestamo.objects.count(),
    }

    return render(request, "prestamos/lista.html", {
        "page": page,
        "q": q,
        "estado": estado,
        "stats": stats,
        "hoy": hoy,
    })


@login_required
@require_POST
def devolver(request, prestamo_id):
    prestamo = get_object_or_404(
        Prestamo.objects.select_related("ejemplar"), pk=prestamo_id
    )
    if prestamo.estado != Prestamo.Estado.ACTIVO:
        messages.error(request, "Este préstamo ya no está activo.")
        return redirect("prestamos:lista")

    with transaction.atomic():
        prestamo.estado = Prestamo.Estado.DEVUELTO
        prestamo.fecha_devolucion_real = timezone.now()
        prestamo.save(update_fields=["estado", "fecha_devolucion_real"])
        prestamo.ejemplar.estado = Ejemplar.Estado.DISPONIBLE
        prestamo.ejemplar.save(update_fields=["estado"])

    messages.success(
        request,
        f"Devolución registrada: «{prestamo.ejemplar.libro.titulo}» de {prestamo.usuario.nombre_completo}.",
    )
    next_url = request.POST.get("next") or "prestamos:lista"
    if next_url.startswith("/"):
        return redirect(next_url)
    return redirect(next_url)


@login_required
def nuevo(request):
    """Pantalla principal: 3 pasos para registrar un préstamo."""
    return render(request, "prestamos/nuevo.html", {
        "fecha_devolucion_default": (timezone.now().date() + timedelta(days=7)).isoformat(),
    })


# ============================================================
#  Combobox de ejemplares
# ============================================================

@login_required
@require_GET
def opciones_ejemplar(request):
    """HTMX: lista de opciones para el combobox.
    Si q está vacío -> últimos 10 disponibles agregados.
    Si q exacto match de código -> dispara autoselección.
    Si q parcial -> filtra hasta 15 resultados.
    """
    consulta = (request.GET.get("q") or "").strip()

    if not consulta:
        ejemplares = Ejemplar.objects.select_related(
            "libro", "libro__categoria"
        ).filter(estado=Ejemplar.Estado.DISPONIBLE).order_by("-creado_en")[:10]
        return render(request, "prestamos/partials/combobox_opciones_ejemplar.html", {
            "ejemplares": ejemplares,
            "consulta": "",
            "es_default": True,
        })

    match_exacto = Ejemplar.objects.select_related(
        "libro", "libro__categoria"
    ).filter(codigo__iexact=consulta).first()
    if match_exacto:
        return render(request, "prestamos/partials/combobox_autoseleccion_ejemplar.html", {
            "ejemplar_id": match_exacto.id,
        })

    ejemplares = Ejemplar.objects.select_related(
        "libro", "libro__categoria"
    ).filter(
        Q(codigo__icontains=consulta)
        | Q(libro__titulo__icontains=consulta)
        | Q(libro__autor__icontains=consulta)
    )[:15]

    return render(request, "prestamos/partials/combobox_opciones_ejemplar.html", {
        "ejemplares": ejemplares,
        "consulta": consulta,
        "es_default": False,
    })


@login_required
@require_GET
def seleccionar_ejemplar(request):
    """HTMX: el usuario eligió un ejemplar. Devuelve la tarjeta de seleccionado."""
    ejemplar_id = request.GET.get("id")
    ejemplar = get_object_or_404(
        Ejemplar.objects.select_related("libro", "libro__categoria"),
        pk=ejemplar_id,
    )
    prestamo_activo = None
    if ejemplar.estado == Ejemplar.Estado.PRESTADO:
        prestamo_activo = ejemplar.prestamos.filter(
            estado=Prestamo.Estado.ACTIVO
        ).select_related("usuario").first()

    return render(request, "prestamos/partials/ejemplar_seleccionado.html", {
        "ejemplar": ejemplar,
        "prestamo_activo": prestamo_activo,
        "disponible": ejemplar.estado == Ejemplar.Estado.DISPONIBLE,
    })


@login_required
@require_GET
def reset_ejemplar(request):
    """HTMX: el usuario quitó el ejemplar seleccionado, regresa el combobox vacío."""
    return render(request, "prestamos/partials/combobox_ejemplar.html")


# ============================================================
#  Combobox de usuarios
# ============================================================

@login_required
@require_GET
def opciones_usuario(request):
    """HTMX: lista de opciones para el combobox de usuario."""
    consulta = (request.GET.get("q") or "").strip()

    if not consulta:
        usuarios = UsuarioBiblioteca.objects.filter(activo=True).order_by("-creado_en")[:10]
        return render(request, "prestamos/partials/combobox_opciones_usuario.html", {
            "usuarios": usuarios,
            "consulta": "",
            "es_default": True,
        })

    match_exacto = UsuarioBiblioteca.objects.filter(
        codigo_universitario__iexact=consulta
    ).first()
    if match_exacto:
        return render(request, "prestamos/partials/combobox_autoseleccion_usuario.html", {
            "usuario_id": match_exacto.id,
        })

    usuarios = UsuarioBiblioteca.objects.filter(
        Q(codigo_universitario__icontains=consulta)
        | Q(nombres__icontains=consulta)
        | Q(apellidos__icontains=consulta)
    )[:15]

    return render(request, "prestamos/partials/combobox_opciones_usuario.html", {
        "usuarios": usuarios,
        "consulta": consulta,
        "es_default": False,
    })


@login_required
@require_GET
def seleccionar_usuario(request):
    """HTMX: el usuario eligió a una persona."""
    usuario_id = request.GET.get("id")
    usuario = get_object_or_404(UsuarioBiblioteca, pk=usuario_id)
    return render(request, "prestamos/partials/usuario_seleccionado.html", {
        "usuario": usuario,
        "puede_pedir": usuario.activo,
    })


@login_required
@require_GET
def reset_usuario(request):
    """HTMX: el usuario quitó el usuario seleccionado."""
    return render(request, "prestamos/partials/combobox_usuario.html")


# ============================================================
#  Confirmación y recibo
# ============================================================

@login_required
@require_POST
def confirmar(request):
    """Crea el préstamo."""
    ejemplar_id = request.POST.get("ejemplar_id")
    usuario_id = request.POST.get("usuario_id")
    fecha_devolucion = request.POST.get("fecha_devolucion")
    observaciones = (request.POST.get("observaciones") or "").strip()

    if not ejemplar_id or not usuario_id or not fecha_devolucion:
        return HttpResponseBadRequest("Datos incompletos.")

    try:
        with transaction.atomic():
            ejemplar = Ejemplar.objects.select_for_update().select_related("libro").get(pk=ejemplar_id)
            usuario = UsuarioBiblioteca.objects.get(pk=usuario_id)

            if ejemplar.estado != Ejemplar.Estado.DISPONIBLE:
                return render(request, "prestamos/error.html", {
                    "titulo": "El libro ya no está disponible",
                    "mensaje": (
                        f"El ejemplar '{ejemplar.codigo}' no está disponible para préstamo. "
                        f"Estado actual: {ejemplar.get_estado_display()}."
                    ),
                })

            if not usuario.activo:
                return render(request, "prestamos/error.html", {
                    "titulo": "La persona está inactiva",
                    "mensaje": (
                        f"{usuario.nombre_completo} figura como inactivo en el sistema. "
                        f"Active su registro antes de hacerle un préstamo."
                    ),
                })

            prestamo = Prestamo.objects.create(
                ejemplar=ejemplar,
                usuario=usuario,
                fecha_devolucion_esperada=fecha_devolucion,
                observaciones=observaciones,
                registrado_por=request.user,
            )

            ejemplar.estado = Ejemplar.Estado.PRESTADO
            ejemplar.save(update_fields=["estado"])

    except Ejemplar.DoesNotExist:
        return HttpResponseBadRequest("Ejemplar inexistente.")
    except UsuarioBiblioteca.DoesNotExist:
        return HttpResponseBadRequest("Usuario inexistente.")

    return redirect("prestamos:recibo", prestamo_id=prestamo.id)


@login_required
def recibo(request, prestamo_id):
    prestamo = get_object_or_404(
        Prestamo.objects.select_related(
            "ejemplar", "ejemplar__libro", "ejemplar__libro__categoria", "usuario"
        ),
        pk=prestamo_id,
    )
    return render(request, "prestamos/recibo.html", {"prestamo": prestamo})
