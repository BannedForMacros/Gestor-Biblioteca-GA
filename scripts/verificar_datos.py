"""Verificacion de la importacion."""
import os
import sys
import django

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.db.models import Count
from apps.catalogo.models import Categoria, Libro, Ejemplar, Capitulo

print()
print("=" * 70)
print("VERIFICACION DE DATOS EN BD")
print("=" * 70)

print()
print(">> Por categoria:")
print(f"{'Categoria':<20} {'Libros':>10} {'Ejemplares':>12} {'Capitulos':>12}")
print("-" * 60)
for cat in Categoria.objects.all().order_by('nombre'):
    libros = Libro.objects.filter(categoria=cat).count()
    ejemplares = Ejemplar.objects.filter(libro__categoria=cat).count()
    caps = Capitulo.objects.filter(libro__categoria=cat).count()
    print(f"{cat.nombre:<20} {libros:>10} {ejemplares:>12} {caps:>12}")

print()
print(">> Distribucion de ejemplares por libro:")
libros_con_count = Libro.objects.annotate(n=Count("ejemplares")).values_list("n", flat=True)
from collections import Counter
distrib = Counter(libros_con_count)
for n_ej in sorted(distrib.keys()):
    print(f"  Libros con {n_ej} ejemplar(es): {distrib[n_ej]}")

print()
print(">> Muestra de 3 libros con mas ejemplares:")
top = Libro.objects.annotate(n=Count("ejemplares")).order_by("-n")[:3]
for l in top:
    codigos = list(l.ejemplares.values_list("codigo", flat=True)[:8])
    print(f"  [{l.categoria.codigo_corto}] {l.titulo[:55]}")
    print(f"     {l.n} ejemplares: {codigos}")

print()
print(">> Libros que en el Excel deberian tener varios ejemplares pero solo tienen 1:")
solo_uno = Libro.objects.annotate(n=Count("ejemplares")).filter(n=1)[:5]
for l in solo_uno:
    cod = l.ejemplares.first().codigo
    print(f"  [{l.categoria.codigo_corto}] {l.titulo[:55]} - codigo: {cod}")

print()
