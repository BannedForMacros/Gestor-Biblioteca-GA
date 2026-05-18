from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, ProtectedError, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import UsuarioBibliotecaForm
from .models import UsuarioBiblioteca


@login_required
def personas_lista(request):
    q = (request.GET.get("q") or "").strip()
    tipo = request.GET.get("tipo") or ""
    activo = request.GET.get("activo") or ""

    personas = UsuarioBiblioteca.objects.annotate(
        n_prestamos=Count("prestamos", distinct=True),
    ).order_by("apellidos", "nombres")

    if q:
        personas = personas.filter(
            Q(codigo_universitario__icontains=q)
            | Q(nombres__icontains=q)
            | Q(apellidos__icontains=q)
            | Q(correo__icontains=q)
        )
    if tipo:
        personas = personas.filter(tipo=tipo)
    if activo == "1":
        personas = personas.filter(activo=True)
    elif activo == "0":
        personas = personas.filter(activo=False)

    paginator = Paginator(personas, 25)
    page = paginator.get_page(request.GET.get("page"))

    return render(request, "usuarios/personas_lista.html", {
        "page": page,
        "q": q,
        "tipo": tipo,
        "activo": activo,
        "tipos": UsuarioBiblioteca.Tipo.choices,
        "total": paginator.count,
    })


@login_required
def persona_detalle(request, pk):
    persona = get_object_or_404(UsuarioBiblioteca, pk=pk)
    prestamos = persona.prestamos.select_related(
        "ejemplar__libro", "ejemplar__libro__categoria"
    ).order_by("-fecha_prestamo")[:20]
    return render(request, "usuarios/persona_detalle.html", {
        "persona": persona,
        "prestamos": prestamos,
    })


@login_required
def persona_form(request, pk=None):
    persona = get_object_or_404(UsuarioBiblioteca, pk=pk) if pk else None
    if request.method == "POST":
        form = UsuarioBibliotecaForm(request.POST, instance=persona)
        if form.is_valid():
            obj = form.save()
            messages.success(
                request,
                f"Persona «{obj.nombre_completo}» {'actualizada' if persona else 'registrada'} correctamente.",
            )
            return redirect("usuarios:persona_detalle", pk=obj.pk)
    else:
        form = UsuarioBibliotecaForm(instance=persona)

    return render(request, "usuarios/persona_form.html", {
        "form": form,
        "persona": persona,
        "es_edicion": persona is not None,
    })


@login_required
@require_POST
def persona_toggle(request, pk):
    persona = get_object_or_404(UsuarioBiblioteca, pk=pk)
    persona.activo = not persona.activo
    persona.save(update_fields=["activo"])
    estado = "activada" if persona.activo else "desactivada"
    messages.success(request, f"Persona «{persona.nombre_completo}» {estado}.")
    return redirect("usuarios:persona_detalle", pk=pk)


@login_required
@require_POST
def persona_eliminar(request, pk):
    persona = get_object_or_404(UsuarioBiblioteca, pk=pk)
    nombre = persona.nombre_completo
    try:
        persona.delete()
        messages.success(request, f"Persona «{nombre}» eliminada.")
    except ProtectedError:
        messages.error(request, "No se puede eliminar: la persona tiene préstamos asociados. Use desactivar.")
        return redirect("usuarios:persona_detalle", pk=pk)
    return redirect("usuarios:personas_lista")
