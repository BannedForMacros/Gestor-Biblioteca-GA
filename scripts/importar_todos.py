"""Script standalone para importar los 4 Excel originales.

Uso (desde la raiz del proyecto, con .venv activado):
    python scripts/importar_todos.py
"""
import os
import sys
import django

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.importacion.parsers import importar_excel

DATA_DIR = os.path.join(ROOT, "data", "excel_originales")

ARCHIVOS = [
    ("ECON", "BASE-DE-DATOS-BIBLIOTECA-FACEAC- ECONOMIA.xlsx"),
    ("ADM",  "BASE-DE-DATOS-BIBLIOTECA-FACEAC-ADMINISTRACION.xlsx"),
    ("CONT", "BASE-DE-DATOS-BIBLIOTECA-FACEAC-CONTABILIDAD.xlsx"),
    ("CNI",  "BASE_DE_DATOS_BIBLIOTECA_FACEAC_COMERCIO.xlsx"),
]

def main():
    print()
    print("=" * 70)
    print("IMPORTACION MASIVA - GESTOR BIBLIOTECA FACEAC")
    print("=" * 70)

    totales = {"libros": 0, "ejemplares": 0, "capitulos": 0, "advertencias": 0}

    for codigo, nombre_archivo in ARCHIVOS:
        ruta = os.path.join(DATA_DIR, nombre_archivo)
        print()
        print(f">>> Procesando: {nombre_archivo}")
        print(f"    Escuela: {codigo}")
        if not os.path.exists(ruta):
            print(f"    [ERROR] No se encontro el archivo en {ruta}")
            continue
        try:
            r = importar_excel(ruta, codigo)
            print(f"    Libros nuevos:       {r.libros_creados}")
            print(f"    Libros existentes:   {r.libros_existentes}")
            print(f"    Ejemplares nuevos:   {r.ejemplares_creados}")
            print(f"    Ejemplares existen.: {r.ejemplares_existentes}")
            print(f"    Capitulos creados:   {r.capitulos_creados}")
            print(f"    Filas omitidas:      {r.filas_omitidas}")
            print(f"    Advertencias:        {len(r.advertencias)}")
            totales["libros"] += r.libros_creados
            totales["ejemplares"] += r.ejemplares_creados
            totales["capitulos"] += r.capitulos_creados
            totales["advertencias"] += len(r.advertencias)
        except Exception as e:
            print(f"    [FALLO] {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()

    print()
    print("=" * 70)
    print("TOTALES")
    print("=" * 70)
    print(f"  Libros nuevos:        {totales['libros']}")
    print(f"  Ejemplares nuevos:    {totales['ejemplares']}")
    print(f"  Capitulos creados:    {totales['capitulos']}")
    print(f"  Advertencias totales: {totales['advertencias']}")
    print()


if __name__ == "__main__":
    main()
