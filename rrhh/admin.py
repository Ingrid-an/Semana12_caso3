"""admin.py — RF6: Django Admin para operaciones de RRHH."""
from django.contrib import admin
from .models import Area, Empleado, Asistencia, Permiso, RegistroAuditoria


@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "total_empleados")
    search_fields = ("nombre",)

    @admin.display(description="N° empleados")
    def total_empleados(self, obj):
        return obj.empleados.count()


@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ("dni", "nombre_completo", "cargo", "area", "rol",
                    "antiguedad", "dias_disponibles", "activo")
    list_filter = ("area", "rol", "tipo_contrato", "activo")
    search_fields = ("dni", "nombres", "apellidos", "email")
    list_select_related = ("area",)

    @admin.display(description="Nombre")
    def nombre_completo(self, obj):
        return obj.nombre_completo

    @admin.display(description="Vacaciones disp.")
    def dias_disponibles(self, obj):
        """Campo calculado RF6: días de vacaciones disponibles."""
        return f"{obj.dias_vacaciones_disponibles} días"


@admin.register(Asistencia)
class AsistenciaAdmin(admin.ModelAdmin):
    list_display = ("empleado", "fecha", "hora_entrada", "hora_salida",
                    "horas_trabajadas", "horas_extras")
    list_filter = ("fecha", "empleado__area")
    search_fields = ("empleado__nombres", "empleado__apellidos", "empleado__dni")
    list_select_related = ("empleado", "empleado__area")


@admin.action(description="Aprobar permisos seleccionados")
def aprobar_permisos(modeladmin, request, queryset):
    """RF6 - Acción masiva: aprobar permisos."""
    queryset.update(estado="aprobado")


@admin.action(description="Rechazar permisos seleccionados")
def rechazar_permisos(modeladmin, request, queryset):
    queryset.update(estado="rechazado")


@admin.register(Permiso)
class PermisoAdmin(admin.ModelAdmin):
    list_display = ("empleado", "tipo", "fecha_inicio", "fecha_fin",
                    "dias_solicitados", "estado", "creado_en")
    list_filter = ("estado", "tipo", "empleado__area")
    search_fields = ("empleado__nombres", "empleado__apellidos")
    actions = [aprobar_permisos, rechazar_permisos]
    list_select_related = ("empleado",)

    @admin.display(description="Días")
    def dias_solicitados(self, obj):
        return obj.dias_solicitados


@admin.register(RegistroAuditoria)
class RegistroAuditoriaAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "usuario", "accion", "ruta")
    list_filter = ("usuario", "timestamp")
    search_fields = ("usuario", "accion")
    readonly_fields = ("usuario", "accion", "ruta", "timestamp")
