"""
middleware.py — RF5: middlewares de control y auditoría.

Cada middleware define __init__ (una vez) y __call__ (cada petición).
"""
import logging
from django.contrib import messages
from django.shortcuts import redirect

logger = logging.getLogger("tecnoandes")


class AuditoriaMiddleware:
    """RF5 - Registra las modificaciones (POST) a asistencia y permisos."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Solo audita modificaciones (POST) de usuarios autenticados
        if request.method == "POST" and request.user.is_authenticated:
            from .models import RegistroAuditoria
            RegistroAuditoria.objects.create(
                usuario=request.user.username,
                accion=f"POST {request.path}",
                ruta=request.path,
            )
            logger.info("[AUDITORÍA] %s modificó %s", request.user.username, request.path)

        response["X-TecnoAndes-Audit"] = "activo"
        return response


class BloqueoCuentaMiddleware:
    """RF5 - Impide el acceso a usuarios cuyo empleado está desactivado."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and not request.user.is_superuser:
            empleado = getattr(request.user, "empleado", None)
            if empleado and not empleado.activo:
                from django.contrib.auth import logout
                logout(request)
                logger.warning("[BLOQUEO] Cuenta desactivada: %s", request.user.username)
                return redirect("rrhh:login")
        return self.get_response(request)


class RecordatorioAsistenciaMiddleware:
    """RF5 - Si el empleado no ha marcado entrada hoy, muestra un recordatorio."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and not request.user.is_superuser:
            empleado = getattr(request.user, "empleado", None)
            if empleado and not request.session.get("recordatorio_mostrado"):
                from django.utils import timezone
                from .models import Asistencia
                hoy = timezone.now().date()
                marco = Asistencia.objects.filter(empleado=empleado, fecha=hoy).exists()
                if not marco and request.path == "/panel/":
                    messages.info(request, "Recordatorio: aún no has marcado tu entrada hoy.")
                    request.session["recordatorio_mostrado"] = True
                    request.session.modified = True
        return self.get_response(request)
