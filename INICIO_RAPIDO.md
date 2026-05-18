# Gestor Biblioteca FACEAC — Inicio Rápido

Proyecto inicializado. Ahora hay 3 pasos manuales que solo tú puedes hacer (porque
involucran tu contraseña de PostgreSQL).

---

## Paso 1 · Pon tu contraseña de PostgreSQL

Abre el archivo `.env` (está en la raíz del proyecto) y reemplaza
`CAMBIAR_ESTO_POR_TU_PASSWORD_DE_POSTGRES` por la contraseña real de tu
usuario `postgres`:

```
DB_PASSWORD=tu_password_real_aqui
```

> Este archivo está en `.gitignore`, nunca se sube a git.

---

## Paso 2 · Crea la base de datos en PostgreSQL

Abre **PowerShell** y ejecuta:

```powershell
& "C:\Program Files\PostgreSQL\17\bin\psql.exe" -U postgres -c "CREATE DATABASE gestor_biblioteca ENCODING 'UTF8';"
```

Te pedirá tu contraseña de postgres. Si todo va bien verás `CREATE DATABASE`.

---

## Paso 3 · Migra el esquema y crea tu usuario administrador

Estos 3 comandos los corres desde la carpeta del proyecto:

```powershell
cd C:\MacSoft\RENACYT\Bilioteca

# 1. Activar el entorno virtual
.\.venv\Scripts\Activate.ps1

# 2. Crear las tablas
python manage.py makemigrations
python manage.py migrate

# 3. Crear tu usuario administrador (te pedirá nombre, email y password)
python manage.py createsuperuser

# 4. Levantar el servidor
python manage.py runserver
```

Abre tu navegador en **http://127.0.0.1:8000/** y verás la pantalla de bienvenida.
El panel de administración está en **http://127.0.0.1:8000/admin/**.

---

## Estructura del proyecto

```
C:\MacSoft\RENACYT\Bilioteca\
├── .venv/                     # Entorno virtual Python
├── apps/                      # Tus apps Django
│   ├── catalogo/              # Libros, Ejemplares, Categorías, Capítulos
│   ├── usuarios/              # Estudiantes, Docentes
│   ├── prestamos/             # Préstamos y devoluciones
│   ├── importacion/           # ETL de Excel a BD (próximo paso)
│   └── reportes/              # Dashboard y KPIs (próximo paso)
├── config/                    # Settings de Django
├── data/excel_originales/     # Tus 4 Excel originales
├── docs/                      # Documento Word del proyecto
├── static/img/logo.png        # Logo GestorBiblioteca
├── templates/                 # base.html, home.html
├── .env                       # ⚠️ Tu password va aquí
├── .env.example               # Plantilla pública
├── manage.py
└── requirements.txt
```

---

## Próximos pasos (cuando confirmes que esto arranca)

1. **Importar los 4 Excel a la BD** — script ETL que limpia y separa los ejemplares.
2. **Pantalla de Préstamo** con lector de barras + entrada manual (HTMX).
3. **Pantalla de Devolución**.
4. **Búsqueda de libros** con autocompletado.
5. **Dashboard** con KPIs.

Cada uno será una pantalla con el mismo nivel de diseño que `home.html`.
