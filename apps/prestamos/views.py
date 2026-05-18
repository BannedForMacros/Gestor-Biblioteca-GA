from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponseBadRequest
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.catalogo.models import Ejemplar
from apps.usuarios.models import UsuarioBiblioteca
from .models import Prestamo


@login_required
def nuevo(request):
    """Pantalla principal: 3 pasos para registrar un préstamo."""
    return render(request, "prestamos/nuevo.html", {
        "fecha_devolucion_default": (timezone.now().date() + timedelta(days=7)).isoformat(),
    })


@login_required
def buscar_ejemplar(request):
    """HTMX: busca un ejemplar por código exacto o por título/autor."""
    consulta = (request.GET.get("q") or "").strip()
    if not consulta:
        return render(request, "prestamos/partials/ejemplar_vacio.html")

    ejemplar = Ejemplar.objects.select_related("libro", "libro__categoria").filter(
        codigo__iexact=consulta
    ).first()
    if ejemplar:
        return _render_ejemplar(request, ejemplar)

    qs = Ejemplar.objects.select_related("libro", "libro__categoria").filter(
        Q(libro__titulo__icontains=consulta) | Q(libro__autor__icontains=consulta)
        | Q(codigo__icontains=consulta)
    )[:20]

    if not qs.exists():
        return render(request, "prestamos/partials/ejemplar_no_encontrado.html", {
            "consulta": consulta,
        })

    return render(request, "prestamos/partials/ejemplar_sugerencias.html", {
        "ejemplares": qs,
        "consulta": consulta,
    })


def _render_ejemplar(request, ejemplar):
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
def buscar_usuario(request):
    """HTMX: busca un usuario por código universitario o nombre."""
    consulta = (request.GET.get("q") or "").strip()
    if not consulta:
        return render(request, "prestamos/partials/usuario_vacio.html")

    usuario = UsuarioBiblioteca.objects.filter(
        codigo_universitario__iexact=consulta
    ).first()
    if usuario:
        return render(request, "prestamos/partials/usuario_seleccionado.html", {
            "usuario": usuario,
            "puede_pedir": usuario.activo,
        })

    qs = UsuarioBiblioteca.objects.filter(
        Q(nombres__icontains=consulta)
        | Q(apellidos__icontains=consulta)
        | Q(codigo_universitario__icontains=consulta)
    )[:15]

    if not qs.exists():
        return render(request, "prestamos/partials/usuario_no_encontrado.html", {
            "consulta": consulta,
        })

    return render(request, "prestamos/partials/usuario_sugerencias.html", {
        "usuarios": qs,
        "consulta": consulta,
    })


@login_required
@require_POST
def confirmar(request):
    """Crea el préstamo. Espera ejemplar_id, usuario_id, fecha_devolucion, observaciones."""
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
    """Recibo de un préstamo recién creado o consultado."""
    prestamo = get_object_or_404(
        Prestamo.objects.select_related(
            "ejemplar", "ejemplar__libro", "ejemplar__libro__categoria", "usuario"
        ),
        pk=prestamo_id,
    )
    return render(request, "prestamos/recibo.html", {"prestamo": prestamo})
