"""Crea 5 usuarios de biblioteca de prueba para poder demostrar el flujo."""
import os
import sys
import django

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.usuarios.models import UsuarioBiblioteca

USUARIOS_DEMO = [
    {
        "codigo_universitario": "175000A",
        "nombres": "Maria Fernanda",
        "apellidos": "Garcia Lopez",
        "tipo": "ESTUDIANTE",
        "escuela": "Economia",
        "correo": "maria.garcia@unprg.edu.pe",
        "telefono": "987654321",
    },
    {
        "codigo_universitario": "175001B",
        "nombres": "Carlos Alberto",
        "apellidos": "Ramirez Diaz",
        "tipo": "ESTUDIANTE",
        "escuela": "Contabilidad",
        "correo": "carlos.ramirez@unprg.edu.pe",
        "telefono": "987654322",
    },
    {
        "codigo_universitario": "165050C",
        "nombres": "Lucia Beatriz",
        "apellidos": "Torres Vargas",
        "tipo": "ESTUDIANTE",
        "escuela": "Administracion",
        "correo": "lucia.torres@unprg.edu.pe",
        "telefono": "987654323",
    },
    {
        "codigo_universitario": "D-1502",
        "nombres": "Roberto Daniel",
        "apellidos": "Mendoza Salazar",
        "tipo": "DOCENTE",
        "escuela": "Economia",
        "correo": "rmendoza@unprg.edu.pe",
        "telefono": "987654324",
    },
    {
        "codigo_universitario": "D-1810",
        "nombres": "Patricia Elena",
        "apellidos": "Quispe Aguilar",
        "tipo": "DOCENTE",
        "escuela": "Comercio",
        "correo": "pquispe@unprg.edu.pe",
        "telefono": "987654325",
    },
]

print()
print("Creando usuarios de demo...")
print("-" * 60)
for datos in USUARIOS_DEMO:
    usuario, creado = UsuarioBiblioteca.objects.get_or_create(
        codigo_universitario=datos["codigo_universitario"],
        defaults=datos,
    )
    estado = "CREADO " if creado else "EXISTE "
    print(f"  [{estado}] {usuario.codigo_universitario:8s} - {usuario.apellidos}, {usuario.nombres}")

total = UsuarioBiblioteca.objects.count()
print("-" * 60)
print(f"Total de usuarios de biblioteca: {total}")
print()
