from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Case, Count, IntegerField, ProtectedError, Q, When
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.prestamos.models import Prestamo

from .forms import SancionForm, UsuarioBibliotecaForm
from .models import Sancion, UsuarioBiblioteca


@login_required
def personas_lista(request):
    q = (request.GET.get("q") or "").strip()
    tipo = request.GET.get("tipo") or ""
    activo = request.GET.get("activo") or ""
    estado = request.GET.get("estado") or ""  # "bloqueado"

    hoy = timezone.now().date()
    personas = UsuarioBiblioteca.objects.annotate(
        n_prestamos=Count("prestamos", distinct=True),
        n_sanciones_activas=Count(
            "sanciones",
            filter=Q(sanciones__activa=True) & (
                Q(sanciones__tipo=Sancion.Tipo.BLOQUEO_INDEFINIDO)
                | Q(sanciones__tipo=Sancion.Tipo.BLOQUEO_TEMPORAL,
                    sanciones__fecha_fin__gte=hoy)
            ),
            distinct=True,
        ),
    ).order_by("apellidos", "nombres")

    if q:
        personas = personas.filter(
            Q(codigo_universitario__icontains=q)
            | Q(nombres__icontains=q)
            | Q(apellidos__icontains=q)
            | Q(correo__icontains=q)
        )
    if tipo:
        personas = personas.filter(tipo=tipo)
    if activo == "1":
        personas = personas.filter(activo=True)
    elif activo == "0":
        personas = personas.filter(activo=False)
    if estado == "bloqueado":
        personas = personas.filter(n_sanciones_activas__gt=0)

    paginator = Paginator(personas, 25)
    page = paginator.get_page(request.GET.get("page"))

    return render(request, "usuarios/personas_lista.html", {
        "page": page,
        "q": q,
        "tipo": tipo,
        "activo": activo,
        "estado": estado,
        "tipos": UsuarioBiblioteca.Tipo.choices,
        "total": paginator.count,
    })


@login_required
def persona_detalle(request, pk):
    persona = get_object_or_404(UsuarioBiblioteca, pk=pk)
    prestamos = persona.prestamos.select_related(
        "ejemplar__libro", "ejemplar__libro__categoria"
    ).order_by("-fecha_prestamo")[:20]

    sancion_bloqueante = persona.sancion_bloqueante()
    sanciones = persona.sanciones.select_related(
        "prestamo__ejemplar__libro", "creada_por", "levantada_por"
    ).order_by("-fecha_inicio")[:30]

    return render(request, "usuarios/persona_detalle.html", {
        "persona": persona,
        "prestamos": prestamos,
        "sancion_bloqueante": sancion_bloqueante,
        "sanciones": sanciones,
    })


@login_required
def persona_form(request, pk=None):
    persona = get_object_or_404(UsuarioBiblioteca, pk=pk) if pk else None
    if request.method == "POST":
        form = UsuarioBibliotecaForm(request.POST, instance=persona)
        if form.is_valid():
            obj = form.save()
            messages.success(
                request,
                f"Persona «{obj.nombre_completo}» {'actualizada' if persona else 'registrada'} correctamente.",
            )
            return redirect("usuarios:persona_detalle", pk=obj.pk)
    else:
        form = UsuarioBibliotecaForm(instance=persona)

    return render(request, "usuarios/persona_form.html", {
        "form": form,
        "persona": persona,
        "es_edicion": persona is not None,
    })


@login_required
@require_POST
def persona_toggle(request, pk):
    persona = get_object_or_404(UsuarioBiblioteca, pk=pk)
    persona.activo = not persona.activo
    persona.save(update_fields=["activo"])
    estado = "activada" if persona.activo else "desactivada"
    messages.success(request, f"Persona «{persona.nombre_completo}» {estado}.")
    return redirect("usuarios:persona_detalle", pk=pk)


@login_required
@require_POST
def persona_eliminar(request, pk):
    persona = get_object_or_404(UsuarioBiblioteca, pk=pk)
    nombre = persona.nombre_completo
    try:
        persona.delete()
        messages.success(request, f"Persona «{nombre}» eliminada.")
    except ProtectedError:
        messages.error(request, "No se puede eliminar: la persona tiene préstamos asociados. Use desactivar.")
        return redirect("usuarios:persona_detalle", pk=pk)
    return redirect("usuarios:personas_lista")


# ============================================================
#  SANCIONES
# ============================================================

@login_required
def sancion_aplicar(request, persona_id):
    persona = get_object_or_404(UsuarioBiblioteca, pk=persona_id)
    prestamo_inicial = None
    prestamo_id = request.GET.get("prestamo") or request.POST.get("prestamo")
    if prestamo_id:
        prestamo_inicial = Prestamo.objects.filter(pk=prestamo_id, usuario=persona).first()

    if request.method == "POST":
        form = SancionForm(request.POST)
        if form.is_valid():
            form.save(
                usuario=persona,
                prestamo=prestamo_inicial,
                creada_por=request.user,
            )
            messages.success(
                request,
                f"Sanción aplicada a {persona.nombre_completo}.",
            )
            return redirect("usuarios:persona_detalle", pk=persona.id)
    else:
        initial = {}
        if prestamo_inicial:
            initial["motivo"] = Sancion.Motivo.DEVOLUCION_TARDIA
            initial["tipo"] = Sancion.Tipo.BLOQUEO_TEMPORAL
            dias_retraso = (timezone.now().date() - prestamo_inicial.fecha_devolucion_esperada).days
            if dias_retraso > 0:
                initial["dias_bloqueo"] = min(max(dias_retraso, 3), 30)
                initial["descripcion"] = (
                    f"Devolución con {dias_retraso} "
                    f"{'día' if dias_retraso == 1 else 'días'} de retraso "
                    f"sobre la fecha esperada "
                    f"({prestamo_inicial.fecha_devolucion_esperada:%d/%m/%Y})."
                )
        form = SancionForm(initial=initial)

    return render(request, "usuarios/sancion_form.html", {
        "form": form,
        "persona": persona,
        "prestamo_inicial": prestamo_inicial,
    })


@login_required
@require_POST
def sancion_levantar(request, pk):
    sancion = get_object_or_404(Sancion, pk=pk)
    if not sancion.activa:
        messages.info(request, "Esta sanción ya estaba inactiva.")
        return redirect("usuarios:persona_detalle", pk=sancion.usuario_id)

    sancion.activa = False
    sancion.levantada_en = timezone.now()
    sancion.levantada_por = request.user
    sancion.motivo_levantamiento = (request.POST.get("motivo_levantamiento") or "").strip()
    sancion.save(update_fields=[
        "activa", "levantada_en", "levantada_por", "motivo_levantamiento"
    ])
    messages.success(
        request,
        f"Sanción levantada para {sancion.usuario.nombre_completo}.",
    )
    return redirect("usuarios:persona_detalle", pk=sancion.usuario_id)


@login_required
def sanciones_lista(request):
    hoy = timezone.now().date()

    bloqueantes = (
        Sancion.objects.filter(activa=True)
        .filter(
            Q(tipo=Sancion.Tipo.BLOQUEO_INDEFINIDO)
            | Q(tipo=Sancion.Tipo.BLOQUEO_TEMPORAL, fecha_fin__gte=hoy)
        )
        .select_related("usuario", "creada_por", "prestamo__ejemplar__libro")
        .annotate(
            _orden=Case(
                When(tipo=Sancion.Tipo.BLOQUEO_INDEFINIDO, then=1),
                When(tipo=Sancion.Tipo.BLOQUEO_TEMPORAL, then=2),
                default=3,
                output_field=IntegerField(),
            )
        )
        .order_by("_orden", "fecha_fin", "-fecha_inicio")
    )

    advertencias = (
        Sancion.objects.filter(activa=True, tipo=Sancion.Tipo.ADVERTENCIA)
        .select_related("usuario", "creada_por")
        .order_by("-fecha_inicio")[:20]
    )

    historial = (
        Sancion.objects.filter(
            Q(activa=False)
            | Q(tipo=Sancion.Tipo.BLOQUEO_TEMPORAL, fecha_fin__lt=hoy)
        )
        .select_related("usuario", "levantada_por")
        .order_by("-fecha_inicio")[:50]
    )

    return render(request, "usuarios/sanciones_lista.html", {
        "bloqueantes": bloqueantes,
        "advertencias": advertencias,
        "historial": historial,
        "stats": {
            "bloqueantes": bloqueantes.count(),
            "advertencias": advertencias.count(),
            "total": Sancion.objects.count(),
        },
    })
