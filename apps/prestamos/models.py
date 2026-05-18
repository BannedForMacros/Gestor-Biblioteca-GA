from django.db import models
from django.utils import timezone
from datetime import timedelta


def fecha_devolucion_default():
    """Por defecto, devolución a 7 días."""
    return timezone.now().date() + timedelta(days=7)


class Prestamo(models.Model):
    """Registra el préstamo de un ejemplar a un usuario de biblioteca."""

    class Estado(models.TextChoices):
        ACTIVO = "ACTIVO", "Activo"
        DEVUELTO = "DEVUELTO", "Devuelto"
        VENCIDO = "VENCIDO", "Vencido"

    ejemplar = models.ForeignKey(
        "catalogo.Ejemplar", on_delete=models.PROTECT, related_name="prestamos"
    )
    usuario = models.ForeignKey(
        "usuarios.UsuarioBiblioteca", on_delete=models.PROTECT, related_name="prestamos"
    )
    fecha_prestamo = models.DateTimeField(default=timezone.now)
    fecha_devolucion_esperada = models.DateField(default=fecha_devolucion_default)
    fecha_devolucion_real = models.DateTimeField(null=True, blank=True)
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.ACTIVO, db_index=True)
    registrado_por = models.ForeignKey(
        "auth.User", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="prestamos_registrados",
        help_text="Personal de biblioteca que registró el préstamo"
    )
    observaciones = models.TextField(blank=True)

    class Meta:
        verbose_name = "Préstamo"
        verbose_name_plural = "Préstamos"
        ordering = ["-fecha_prestamo"]
        indexes = [
            models.Index(fields=["estado", "fecha_devolucion_esperada"]),
        ]

    def __str__(self):
        return f"{self.ejemplar.codigo} → {self.usuario.nombre_completo}"

    @property
    def esta_vencido(self):
        if self.estado != self.Estado.ACTIVO:
            return False
        return timezone.now().date() > self.fecha_devolucion_esperada

    @property
    def dias_de_retraso(self):
        if not self.esta_vencido:
            return 0
        return (timezone.now().date() - self.fecha_devolucion_esperada).days
