from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone


class UsuarioBiblioteca(models.Model):
    """
    Persona que puede pedir préstamos: estudiante o docente de la FACEAC.
    No es un usuario de login del sistema (eso lo maneja django.contrib.auth).
    """

    class Tipo(models.TextChoices):
        ESTUDIANTE = "ESTUDIANTE", "Estudiante"
        DOCENTE = "DOCENTE", "Docente"
        ADMINISTRATIVO = "ADMIN", "Administrativo"

    codigo_universitario = models.CharField(
        max_length=20, unique=True, db_index=True,
        verbose_name="Código universitario"
    )
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    tipo = models.CharField(max_length=15, choices=Tipo.choices, default=Tipo.ESTUDIANTE)
    escuela = models.CharField(
        max_length=80, blank=True,
        help_text="Escuela profesional (Economía, Administración, etc.)"
    )
    correo = models.EmailField(blank=True)
    telefono = models.CharField(max_length=20, blank=True, verbose_name="Teléfono")
    activo = models.BooleanField(
        default=True,
        help_text="Si está desactivado, no podrá pedir nuevos préstamos."
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Usuario de Biblioteca"
        verbose_name_plural = "Usuarios de Biblioteca"
        ordering = ["apellidos", "nombres"]

    def __str__(self):
        return f"{self.apellidos}, {self.nombres} ({self.codigo_universitario})"

    @property
    def nombre_completo(self):
        return f"{self.nombres} {self.apellidos}".strip()

    def sancion_bloqueante(self):
        """Devuelve la sanción activa que actualmente bloquea préstamos, o None."""
        hoy = timezone.now().date()
        return self.sanciones.filter(activa=True).filter(
            Q(tipo=Sancion.Tipo.BLOQUEO_INDEFINIDO)
            | Q(tipo=Sancion.Tipo.BLOQUEO_TEMPORAL, fecha_fin__gte=hoy)
        ).order_by("-fecha_inicio").first()

    @property
    def esta_bloqueado(self):
        return self.sancion_bloqueante() is not None

    @property
    def puede_pedir_prestamo(self):
        return self.activo and not self.esta_bloqueado


class Sancion(models.Model):
    """Sanción o restricción aplicada a un usuario de biblioteca."""

    class Motivo(models.TextChoices):
        DEVOLUCION_TARDIA = "TARDIA", "Devolución tardía"
        LIBRO_DANADO = "DANO", "Libro dañado"
        LIBRO_PERDIDO = "PERDIDO", "Libro perdido"
        COMPORTAMIENTO = "COMPORT", "Comportamiento inadecuado"
        OTRO = "OTRO", "Otro motivo"

    class Tipo(models.TextChoices):
        BLOQUEO_TEMPORAL = "TEMP", "Bloqueo temporal"
        BLOQUEO_INDEFINIDO = "INDEF", "Bloqueo indefinido"
        ADVERTENCIA = "ADV", "Advertencia (sin bloqueo)"

    usuario = models.ForeignKey(
        UsuarioBiblioteca, on_delete=models.CASCADE, related_name="sanciones"
    )
    motivo = models.CharField(max_length=10, choices=Motivo.choices)
    tipo = models.CharField(
        max_length=10, choices=Tipo.choices, default=Tipo.BLOQUEO_TEMPORAL
    )
    descripcion = models.TextField(
        blank=True,
        help_text="Detalle del incidente (opcional)."
    )
    prestamo = models.ForeignKey(
        "prestamos.Prestamo",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="sanciones_originadas",
        help_text="Préstamo que originó la sanción (si aplica)."
    )
    fecha_inicio = models.DateField(default=timezone.now)
    fecha_fin = models.DateField(
        null=True, blank=True,
        help_text="Solo para bloqueo temporal."
    )
    activa = models.BooleanField(default=True, db_index=True)
    levantada_en = models.DateTimeField(null=True, blank=True)
    levantada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="sanciones_levantadas",
    )
    motivo_levantamiento = models.TextField(blank=True)
    creada_en = models.DateTimeField(auto_now_add=True)
    creada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="sanciones_creadas",
    )

    class Meta:
        verbose_name = "Sanción"
        verbose_name_plural = "Sanciones"
        ordering = ["-fecha_inicio"]
        indexes = [
            models.Index(fields=["activa", "tipo"]),
        ]

    def __str__(self):
        return f"{self.get_motivo_display()} → {self.usuario.nombre_completo}"

    @property
    def bloquea(self):
        return self.tipo in {self.Tipo.BLOQUEO_TEMPORAL, self.Tipo.BLOQUEO_INDEFINIDO}

    @property
    def vigente(self):
        """Está activa Y actualmente impide préstamos."""
        if not self.activa or not self.bloquea:
            return False
        if self.tipo == self.Tipo.BLOQUEO_INDEFINIDO:
            return True
        return self.fecha_fin is not None and self.fecha_fin >= timezone.now().date()

    @property
    def expirada(self):
        """Era un bloqueo temporal pero ya pasó la fecha_fin."""
        return (
            self.tipo == self.Tipo.BLOQUEO_TEMPORAL
            and self.fecha_fin is not None
            and self.fecha_fin < timezone.now().date()
        )

    @property
    def dias_restantes(self):
        if self.tipo != self.Tipo.BLOQUEO_TEMPORAL or not self.fecha_fin:
            return None
        delta = (self.fecha_fin - timezone.now().date()).days
        return max(delta, 0)
