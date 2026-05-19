from datetime import timedelta

from django.utils import timezone

from apps.prestamos.models import Prestamo
from .models import Alerta


DIAS_AVISO_PREVIO = 2


def _mensaje_prestamo(prestamo: Prestamo) -> str:
    return (
        f"El libro «{prestamo.ejemplar.libro.titulo}» "
        f"(código {prestamo.ejemplar.codigo}) prestado a "
        f"{prestamo.usuario.nombre_completo} "
        f"({prestamo.usuario.codigo_universitario}) "
        f"debe devolverse el {prestamo.fecha_devolucion_esperada:%d/%m/%Y}."
    )


def generar_alertas(dias_aviso_previo: int = DIAS_AVISO_PREVIO) -> dict:
    """Genera/actualiza alertas para préstamos por vencer y vencidos.

    Idempotente: si ya existe una alerta activa (no leída) para el mismo
    préstamo y tipo, la actualiza en vez de duplicarla. Si fue marcada como
    leída por el bibliotecario y la situación persiste, se vuelve a crear.
    """
    hoy = timezone.now().date()
    fecha_limite = hoy + timedelta(days=dias_aviso_previo)

    creadas = 0
    actualizadas = 0

    # ----- VENCIDOS (CRÍTICA) -----
    vencidos = Prestamo.objects.select_related(
        "ejemplar__libro", "usuario"
    ).filter(
        estado=Prestamo.Estado.ACTIVO,
        fecha_devolucion_esperada__lt=hoy,
    )
    total_vencidos = vencidos.count()

    for prestamo in vencidos:
        dias_retraso = (hoy - prestamo.fecha_devolucion_esperada).days
        titulo = (
            f"Préstamo vencido hace {dias_retraso} "
            f"{'día' if dias_retraso == 1 else 'días'}"
        )
        mensaje = _mensaje_prestamo(prestamo)

        alerta, creada = Alerta.objects.get_or_create(
            tipo=Alerta.Tipo.VENCIDO,
            prestamo=prestamo,
            leida=False,
            defaults={
                "nivel": Alerta.Nivel.CRITICA,
                "titulo": titulo,
                "mensaje": mensaje,
            },
        )
        if creada:
            creadas += 1
        elif alerta.titulo != titulo or alerta.mensaje != mensaje or alerta.nivel != Alerta.Nivel.CRITICA:
            alerta.titulo = titulo
            alerta.mensaje = mensaje
            alerta.nivel = Alerta.Nivel.CRITICA
            alerta.save(update_fields=["titulo", "mensaje", "nivel"])
            actualizadas += 1

    # ----- POR VENCER (ADVERTENCIA si vence hoy, INFO si después) -----
    por_vencer = Prestamo.objects.select_related(
        "ejemplar__libro", "usuario"
    ).filter(
        estado=Prestamo.Estado.ACTIVO,
        fecha_devolucion_esperada__gte=hoy,
        fecha_devolucion_esperada__lte=fecha_limite,
    )
    total_por_vencer = por_vencer.count()

    for prestamo in por_vencer:
        dias_restantes = (prestamo.fecha_devolucion_esperada - hoy).days
        if dias_restantes == 0:
            titulo = "Préstamo vence hoy"
            nivel = Alerta.Nivel.ADVERTENCIA
        elif dias_restantes == 1:
            titulo = "Préstamo vence mañana"
            nivel = Alerta.Nivel.INFO
        else:
            titulo = f"Préstamo vence en {dias_restantes} días"
            nivel = Alerta.Nivel.INFO

        mensaje = _mensaje_prestamo(prestamo)

        alerta, creada = Alerta.objects.get_or_create(
            tipo=Alerta.Tipo.POR_VENCER,
            prestamo=prestamo,
            leida=False,
            defaults={
                "nivel": nivel,
                "titulo": titulo,
                "mensaje": mensaje,
            },
        )
        if creada:
            creadas += 1
        elif alerta.titulo != titulo or alerta.mensaje != mensaje or alerta.nivel != nivel:
            alerta.titulo = titulo
            alerta.mensaje = mensaje
            alerta.nivel = nivel
            alerta.save(update_fields=["titulo", "mensaje", "nivel"])
            actualizadas += 1

    return {
        "creadas": creadas,
        "actualizadas": actualizadas,
        "vencidos_total": total_vencidos,
        "por_vencer_total": total_por_vencer,
    }
