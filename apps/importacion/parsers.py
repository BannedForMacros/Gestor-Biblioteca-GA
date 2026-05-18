"""
Lógica de parsing de los Excel originales de la biblioteca FACEAC.

Cada archivo tiene un esquema distinto, así que mantenemos una configuración
por escuela. La función principal `importar_excel()` es idempotente: si se
vuelve a correr con el mismo archivo, no duplica ejemplares (usa el código
como llave natural).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

import openpyxl
from django.db import transaction

from apps.catalogo.models import Categoria, Libro, Ejemplar, Capitulo


CONFIG_ESCUELAS = {
    "ECON": {
        "nombre": "Economía",
        "header_row": 2,
        "col_codigos": 1,
        "col_clasificacion": 2,
        "col_titulo": 3,
        "col_autor": 4,
        "col_anio": 5,
        "col_editorial": 6,
        "col_isbn": 7,
        "col_paginas": 8,
        "col_ubicacion": 9,
        "col_estado": 10,
        "col_capitulo": 11,
    },
    "ADM": {
        "nombre": "Administración",
        "header_row": 2,
        "col_codigos": 1,
        "col_clasificacion": 2,
        "col_titulo": 3,
        "col_autor": 4,
        "col_anio": 5,
        "col_editorial": 6,
        "col_isbn": 7,
        "col_paginas": 8,
        "col_ubicacion": 9,
        "col_estado": 10,
        "col_capitulo": 11,
    },
    "CONT": {
        "nombre": "Contabilidad",
        "header_row": 2,
        "col_codigos": 2,
        "col_clasificacion": 3,
        "col_titulo": 5,
        "col_autor": 6,
        "col_anio": 7,
        "col_editorial": 8,
        "col_isbn": 9,
        "col_paginas": 10,
        "col_ubicacion": 11,
        "col_estado": 12,
        "col_capitulo": 13,
    },
    "CNI": {
        "nombre": "Comercio",
        "header_row": 3,
        "col_codigos": 2,
        "col_clasificacion": 3,
        "col_titulo": 5,
        "col_autor": 6,
        "col_anio": 7,
        "col_editorial": 8,
        "col_isbn": 9,
        "col_paginas": 10,
        "col_ubicacion": 11,
        "col_estado": 12,
        "col_capitulo": 13,
    },
}


@dataclass
class ResultadoImportacion:
    libros_creados: int = 0
    libros_existentes: int = 0
    ejemplares_creados: int = 0
    ejemplares_existentes: int = 0
    capitulos_creados: int = 0
    filas_omitidas: int = 0
    advertencias: list[dict] = field(default_factory=list)

    @property
    def total_filas_procesadas(self) -> int:
        return (
            self.libros_creados + self.libros_existentes
            + self.filas_omitidas
        )

    def agregar_advertencia(self, fila: int, mensaje: str):
        if len(self.advertencias) < 200:
            self.advertencias.append({"fila": fila, "mensaje": mensaje})


def _limpiar_str(valor) -> str:
    if valor is None:
        return ""
    return str(valor).strip()


def _limpiar_int(valor) -> Optional[int]:
    if valor is None or valor == "":
        return None
    try:
        return int(float(valor))
    except (ValueError, TypeError):
        return None


def _separar_tokens(valor: str) -> list[str]:
    """Divide un string con valores separados por uno o más espacios.
    Ej: 'L-ECON-0001  L-ECON-0002' -> ['L-ECON-0001', 'L-ECON-0002']
    """
    if not valor:
        return []
    return [t for t in re.split(r"\s+", valor.strip()) if t]


def _mapear_condicion(estado_texto: str) -> str:
    """Mapea el texto del estado del Excel a las opciones del modelo."""
    t = (estado_texto or "").strip().upper()
    if "MAL" in t:
        return Ejemplar.Condicion.MALO
    if "REGULAR" in t:
        return Ejemplar.Condicion.REGULAR
    return Ejemplar.Condicion.BUENO


@transaction.atomic
def importar_excel(
    ruta_o_buffer,
    categoria_codigo: str,
) -> ResultadoImportacion:
    """
    Importa un archivo Excel a la BD para la categoría indicada.

    Idempotente: usa el código del ejemplar como llave única.
    Atómica: si algo falla catastróficamente, se revierten todos los cambios.

    Args:
        ruta_o_buffer: Path al .xlsx o un file-like object (request.FILES['archivo']).
        categoria_codigo: Una de ECON, ADM, CONT, CNI.

    Returns:
        ResultadoImportacion con conteos y advertencias.
    """
    if categoria_codigo not in CONFIG_ESCUELAS:
        raise ValueError(f"Código de categoría inválido: {categoria_codigo}")

    cfg = CONFIG_ESCUELAS[categoria_codigo]
    resultado = ResultadoImportacion()

    categoria, _ = Categoria.objects.get_or_create(
        codigo_corto=categoria_codigo,
        defaults={"nombre": cfg["nombre"]},
    )

    wb = openpyxl.load_workbook(ruta_o_buffer, data_only=True, read_only=True)
    ws = wb.active

    libro_actual: Optional[Libro] = None
    orden_capitulo_actual = 0

    for row_idx, row in enumerate(ws.iter_rows(values_only=True), start=1):
        if row_idx <= cfg["header_row"]:
            continue

        def cell(col_1based: int):
            idx = col_1based - 1
            return row[idx] if idx < len(row) else None

        titulo = _limpiar_str(cell(cfg["col_titulo"]))
        codigos_raw = _limpiar_str(cell(cfg["col_codigos"]))
        capitulo_txt = _limpiar_str(cell(cfg["col_capitulo"]))

        if not titulo and not codigos_raw and not capitulo_txt:
            continue

        if not titulo and capitulo_txt and libro_actual:
            orden_capitulo_actual += 1
            Capitulo.objects.create(
                libro=libro_actual,
                orden=orden_capitulo_actual,
                titulo=capitulo_txt[:400],
            )
            resultado.capitulos_creados += 1
            continue

        if not titulo:
            resultado.filas_omitidas += 1
            continue

        try:
            autor = _limpiar_str(cell(cfg["col_autor"]))
            anio = _limpiar_int(cell(cfg["col_anio"]))
            editorial = _limpiar_str(cell(cfg["col_editorial"]))
            isbn = _limpiar_str(cell(cfg["col_isbn"]))
            paginas = _limpiar_int(cell(cfg["col_paginas"]))
            ubicacion = _limpiar_str(cell(cfg["col_ubicacion"]))
            estado_txt = _limpiar_str(cell(cfg["col_estado"]))

            libro, libro_creado = Libro.objects.get_or_create(
                titulo=titulo[:300],
                autor=autor[:200],
                categoria=categoria,
                defaults={
                    "anio": anio,
                    "editorial": editorial[:150],
                    "isbn": isbn[:20],
                    "numero_paginas": paginas,
                },
            )
            if libro_creado:
                resultado.libros_creados += 1
            else:
                resultado.libros_existentes += 1
                if not libro.isbn and isbn:
                    libro.isbn = isbn[:20]
                    libro.save(update_fields=["isbn"])

            libro_actual = libro
            orden_capitulo_actual = 0

            codigos = _separar_tokens(codigos_raw)
            clasificaciones = _separar_tokens(_limpiar_str(cell(cfg["col_clasificacion"])))

            condicion = _mapear_condicion(estado_txt)

            for i, cod in enumerate(codigos):
                cod_limpio = cod.strip()[:50]
                if not cod_limpio:
                    continue
                clasif = clasificaciones[i] if i < len(clasificaciones) else ""

                ej, ej_creado = Ejemplar.objects.get_or_create(
                    codigo=cod_limpio,
                    defaults={
                        "libro": libro,
                        "clasificacion": clasif[:80],
                        "ubicacion": ubicacion[:50],
                        "condicion": condicion,
                    },
                )
                if ej_creado:
                    resultado.ejemplares_creados += 1
                else:
                    resultado.ejemplares_existentes += 1
                    if ej.libro_id != libro.id:
                        resultado.agregar_advertencia(
                            row_idx,
                            f"El código '{cod_limpio}' ya existía asociado a otro libro "
                            f"('{ej.libro.titulo[:60]}'). Se mantuvo el registro original."
                        )

            if capitulo_txt:
                orden_capitulo_actual += 1
                Capitulo.objects.create(
                    libro=libro,
                    orden=orden_capitulo_actual,
                    titulo=capitulo_txt[:400],
                )
                resultado.capitulos_creados += 1

        except Exception as e:
            resultado.agregar_advertencia(
                row_idx,
                f"No se pudo procesar la fila: {type(e).__name__}: {e}"
            )

    return resultado
