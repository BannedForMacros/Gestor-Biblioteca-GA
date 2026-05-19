from django.db.models import Case, IntegerField, When

from .models import Alerta


def alertas(request):
    """Expone contador y top 5 de alertas no leídas a todas las plantillas."""
    if not getattr(request, "user", None) or not request.user.is_authenticated:
        return {"alertas_no_leidas_count": 0, "alertas_top": []}

    qs = Alerta.objects.filter(leida=False).annotate(
        _orden_nivel=Case(
            When(nivel=Alerta.Nivel.CRITICA, then=1),
            When(nivel=Alerta.Nivel.ADVERTENCIA, then=2),
            When(nivel=Alerta.Nivel.INFO, then=3),
            default=4,
            output_field=IntegerField(),
        )
    ).order_by("_orden_nivel", "-creada_en")

    return {
        "alertas_no_leidas_count": qs.count(),
        "alertas_top": list(
            qs.select_related(
                "prestamo__ejemplar__libro", "prestamo__usuario"
            )[:5]
        ),
    }
