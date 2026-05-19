from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Case, IntegerField, When
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Alerta
from .services import generar_alertas


def _orden_por_nivel():
    return Case(
        When(nivel=Alerta.Nivel.CRITICA, then=1),
        When(nivel=Alerta.Nivel.ADVERTENCIA, then=2),
        When(nivel=Alerta.Nivel.INFO, then=3),
        default=4,
        output_field=IntegerField(),
    )


@login_required
def lista(request):
    leidas_filter = request.GET.get("leidas") or "no"
    tipo = request.GET.get("tipo") or ""
    nivel = request.GET.get("nivel") or ""

    alertas = Alerta.objects.select_related(
        "prestamo__ejemplar__libro",
        "prestamo__ejemplar__libro__categoria",
        "prestamo__usuario",
        "leida_por",
    ).annotate(_orden_nivel=_orden_por_nivel()).order_by(
        "leida", "_orden_nivel", "-creada_en"
    )

    if leidas_filter == "no":
        alertas = alertas.filter(leida=False)
    elif leidas_filter == "si":
        alertas = alertas.filter(leida=True)
    # "todas" -> sin filtro

    if tipo:
        alertas = alertas.filter(tipo=tipo)
    if nivel:
        alertas = alertas.filter(nivel=nivel)

    paginator = Paginator(alertas, 25)
    page = paginator.get_page(request.GET.get("page"))

    stats = {
        "total": Alerta.objects.count(),
        "no_leidas": Alerta.objects.filter(leida=False).count(),
        "criticas": Alerta.objects.filter(
            leida=False, nivel=Alerta.Nivel.CRITICA
        ).count(),
        "advertencias": Alerta.objects.filter(
            leida=False, nivel=Alerta.Nivel.ADVERTENCIA
        ).count(),
    }

    return render(request, "alertas/lista.html", {
        "page": page,
        "leidas_filter": leidas_filter,
        "tipo": tipo,
        "nivel": nivel,
        "stats": stats,
        "tipos": Alerta.Tipo.choices,
        "niveles": Alerta.Nivel.choices,
    })


@login_required
@require_POST
def marcar_leida(request, pk):
    alerta = get_object_or_404(Alerta, pk=pk)
    alerta.marcar_leida(user=request.user)
    next_url = request.POST.get("next")
    if next_url and next_url.startswith("/"):
        return redirect(next_url)
    return redirect("alertas:lista")


@login_required
@require_POST
def marcar_todas_leidas(request):
    actualizadas = Alerta.objects.filter(leida=False).update(
        leida=True,
        leida_en=timezone.now(),
        leida_por=request.user,
    )
    if actualizadas:
        messages.success(
            request,
            f"{actualizadas} alerta{'s' if actualizadas != 1 else ''} "
            f"marcada{'s' if actualizadas != 1 else ''} como leída"
            f"{'s' if actualizadas != 1 else ''}."
        )
    else:
        messages.info(request, "No había alertas pendientes.")
    return redirect("alertas:lista")


@login_required
@require_POST
def regenerar(request):
    resultado = generar_alertas()
    messages.success(
        request,
        f"Alertas actualizadas. Nuevas: {resultado['creadas']} · "
        f"Actualizadas: {resultado['actualizadas']} · "
        f"Vencidos: {resultado['vencidos_total']} · "
        f"Por vencer: {resultado['por_vencer_total']}."
    )
    return redirect("alertas:lista")
