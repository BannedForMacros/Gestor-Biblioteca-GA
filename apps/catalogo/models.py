from django.db import models


class Categoria(models.Model):
    """Facultad/Escuela: Economía, Administración, Contabilidad, Comercio."""
    nombre = models.CharField(max_length=80, unique=True)
    codigo_corto = models.CharField(max_length=10, unique=True, help_text="Ej: ECON, ADM, CONT, CNI")

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Libro(models.Model):
    """Un título único en el catálogo. Puede tener varios ejemplares físicos."""
    titulo = models.CharField(max_length=300)
    autor = models.CharField(max_length=200, blank=True)
    anio = models.PositiveIntegerField(null=True, blank=True, verbose_name="Año")
    editorial = models.CharField(max_length=150, blank=True)
    isbn = models.CharField(max_length=20, blank=True, db_index=True)
    numero_paginas = models.PositiveIntegerField(null=True, blank=True, verbose_name="N° de páginas")
    categoria = models.ForeignKey(
        Categoria, on_delete=models.PROTECT, related_name="libros",
        verbose_name="Categoría / Escuela"
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Libro"
        verbose_name_plural = "Libros"
        ordering = ["titulo"]
        indexes = [
            models.Index(fields=["titulo"]),
            models.Index(fields=["autor"]),
        ]

    def __str__(self):
        return f"{self.titulo} — {self.autor}" if self.autor else self.titulo


class Ejemplar(models.Model):
    """Cada copia física del libro. Cada uno tiene su propio código de barras."""

    class Estado(models.TextChoices):
        DISPONIBLE = "DISPONIBLE", "Disponible"
        PRESTADO = "PRESTADO", "Prestado"
        RESERVADO = "RESERVADO", "Reservado"
        DADO_DE_BAJA = "BAJA", "Dado de baja"

    class Condicion(models.TextChoices):
        BUENO = "BUENO", "Buen estado"
        REGULAR = "REGULAR", "Regular"
        MALO = "MALO", "Mal estado"

    libro = models.ForeignKey(Libro, on_delete=models.CASCADE, related_name="ejemplares")
    codigo = models.CharField(
        max_length=50, unique=True, db_index=True,
        help_text="Código único del ejemplar. Es el que lee el código de barras (ej: L-ECON-0001)."
    )
    clasificacion = models.CharField(
        max_length=80, blank=True,
        help_text="Clasificación bibliográfica / signatura (ej: 338.5A59E.1)"
    )
    ubicacion = models.CharField(max_length=50, blank=True, verbose_name="Ubicación física")
    estado = models.CharField(
        max_length=15, choices=Estado.choices, default=Estado.DISPONIBLE,
        db_index=True
    )
    condicion = models.CharField(
        max_length=10, choices=Condicion.choices, default=Condicion.BUENO,
        verbose_name="Condición física"
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Ejemplar"
        verbose_name_plural = "Ejemplares"
        ordering = ["codigo"]

    def __str__(self):
        return f"{self.codigo} · {self.libro.titulo}"


class Capitulo(models.Model):
    """Capítulo o contenido individual asociado a un libro (opcional)."""
    libro = models.ForeignKey(Libro, on_delete=models.CASCADE, related_name="capitulos")
    orden = models.PositiveIntegerField(default=1)
    titulo = models.CharField(max_length=400)

    class Meta:
        verbose_name = "Capítulo"
        verbose_name_plural = "Capítulos"
        ordering = ["libro", "orden"]

    def __str__(self):
        return f"{self.orden}. {self.titulo}"
