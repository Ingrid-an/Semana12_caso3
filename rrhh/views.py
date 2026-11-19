"""views.py — RF2, RF3, RF4: asistencia, permisos, auth y autorización jerárquica."""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import Empleado, Asistencia, Permiso
from .forms import AsistenciaForm, PermisoForm


def _empleado(request):
    return getattr(request.user, "empleado", None)


# ---------- Login / Logout (RF4) ----------
def iniciar_sesion(request):
    if request.method == "POST":
        user = authenticate(request, username=request.POST.get("username"),
                            password=request.POST.get("password"))
        if user:
            login(request, user)
            return redirect("rrhh:panel")
        messages.error(request, "Credenciales incorrectas.")
    return render(request, "rrhh/login.html")


def cerrar_sesion(request):
    logout(request)
    messages.info(request, "Sesión cerrada.")
    return redirect("rrhh:login")


# ---------- Panel según rol (RF4) ----------
@login_required(login_url="rrhh:login")
def panel(request):
    emp = _empleado(request)
    ctx = {"empleado": emp}
    if emp:
        ctx["mis_asistencias"] = emp.asistencias.all()[:5]
        ctx["mis_permisos"] = emp.permisos.all()[:5]
        # Jefe de área / RRHH ven permisos pendientes para aprobar
        if emp.rol in ("jefe_area", "admin_rrhh"):
            pendientes = Permiso.objects.filter(estado="pendiente")
            if emp.rol == "jefe_area":
                pendientes = pendientes.filter(empleado__area=emp.area)
            ctx["pendientes"] = pendientes.select_related("empleado")
    return render(request, "rrhh/panel.html", ctx)


# ---------- RF2: marcar asistencia ----------
@login_required(login_url="rrhh:login")
def marcar_asistencia(request):
    if request.method == "POST":
        form = AsistenciaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Asistencia registrada correctamente.")
            return redirect("rrhh:panel")
    else:
        emp = _empleado(request)
        form = AsistenciaForm(initial={"empleado": emp, "hora_entrada": timezone.now()})
    return render(request, "rrhh/asistencia.html", {"form": form})


# ---------- RF3: solicitar permiso ----------
@login_required(login_url="rrhh:login")
def solicitar_permiso(request):
    if request.method == "POST":
        form = PermisoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Solicitud de permiso enviada. Estado: pendiente.")
            return redirect("rrhh:panel")
    else:
        form = PermisoForm(initial={"empleado": _empleado(request)})
    return render(request, "rrhh/permiso.html", {"form": form})


# ---------- RF3: flujo de aprobación ----------
@login_required(login_url="rrhh:login")
def aprobar_permiso(request, pk, accion):
    emp = _empleado(request)
    # Autorización: solo jefe de área o RRHH
    if not emp or emp.rol not in ("jefe_area", "admin_rrhh"):
        messages.error(request, "No tienes permiso para aprobar solicitudes.")
        return redirect("rrhh:panel")
    permiso = get_object_or_404(Permiso, pk=pk)
    # Jefe solo aprueba de su área
    if emp.rol == "jefe_area" and permiso.empleado.area != emp.area:
        messages.error(request, "Solo puedes gestionar permisos de tu área.")
        return redirect("rrhh:panel")
    permiso.estado = "aprobado" if accion == "aprobar" else "rechazado"
    permiso.aprobado_por = emp
    permiso.save()
    messages.success(request, f"Permiso {permiso.estado}.")
    return redirect("rrhh:panel")
