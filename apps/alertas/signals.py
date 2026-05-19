from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from apps.prestamos.models import Prestamo
from .models import Alerta


@receiver(post_save, sender=Prestamo)
def resolver_alertas_al_devolver(sender, instance, **kwargs):
    """Cuando un préstamo se marca como devuelto, resuelve sus alertas activas."""
    if instance.estado == Prestamo.Estado.DEVUELTO:
        Alerta.objects.filter(prestamo=instance, leida=False).update(
            leida=True,
            leida_en=timezone.now(),
        )
