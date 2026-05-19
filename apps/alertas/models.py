from django.conf import settings
from django.db import models
from django.utils import timezone


class Alerta(models.Model):
    """Notificación generada por el sistema para el personal de biblioteca."""

    class Tipo(models.TextChoices):
        POR_VENCER = "POR_VENCER", "Préstamo por vencer"
        VENCIDO = "VENCIDO", "Préstamo vencido"

    class Nivel(models.TextChoices):
        INFO = "INFO", "Información"
        ADVERTENCIA = "WARN", "Advertencia"
        CRITICA = "CRIT", "Crítica"

    tipo = models.CharField(max_length=20, choices=Tipo.choices, db_index=True)
    nivel = models.CharField(
        max_length=10, choices=Nivel.choices, default=Nivel.INFO, db_index=True
    )
    prestamo = models.ForeignKey(
        "prestamos.Prestamo",
        on_delete=models.CASCADE,
        related_name="alertas",
        null=True, blank=True,
    )
    titulo = models.CharField(max_length=160)
    mensaje = models.TextField(blank=True)
    leida = models.BooleanField(default=False, db_index=True)
    creada_en = models.DateTimeField(auto_now_add=True)
    actualizada_en = models.DateTimeField(auto_now=True)
    leida_en = models.DateTimeField(null=True, blank=True)
    leida_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="alertas_marcadas",
    )

    class Meta:
        verbose_name = "Alerta"
        verbose_name_plural = "Alertas"
        ordering = ["leida", "-creada_en"]
        indexes = [
            models.Index(fields=["leida", "-creada_en"]),
            models.Index(fields=["tipo", "leida"]),
        ]

    def __str__(self):
        return f"[{self.get_nivel_display()}] {self.titulo}"

    def marcar_leida(self, user=None):
        if self.leida:
            return
        self.leida = True
        self.leida_en = timezone.now()
        if user is not None and getattr(user, "is_authenticated", False):
            self.leida_por = user
        self.save(update_fields=["leida", "leida_en", "leida_por"])
