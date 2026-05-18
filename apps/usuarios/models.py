from django.db import models


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
