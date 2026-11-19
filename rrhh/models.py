"""Modelos del Sistema de Control de Asistencia y Permisos - TecnoAndes S.A.C."""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date


class Area(models.Model):
    """RF1 - Área de la empresa."""
    nombre = models.CharField("Nombre", max_length=50, unique=True)

    class Meta:
        verbose_name = "Área"
        verbose_name_plural = "Áreas"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Empleado(models.Model):
    """RF1 - Empleado de la empresa."""
    TIPO_CONTRATO = [("planilla", "Planilla"), ("locacion", "Locación")]
    ROLES = [
        ("admin_rrhh", "Administrador RRHH"),
        ("jefe_area", "Jefe de Área"),
        ("empleado", "Empleado"),
        ("contador", "Contador"),
    ]

    usuario = models.OneToOneField(User, on_delete=models.CASCADE,
                                   related_name="empleado", null=True, blank=True)
    dni = models.CharField("DNI", max_length=8, unique=True)
    nombres = models.CharField("Nombres", max_length=80)
    apellidos = models.CharField("Apellidos", max_length=80)
    cargo = models.CharField("Cargo", max_length=80)
    area = models.ForeignKey(Area, on_delete=models.PROTECT, related_name="empleados")
    rol = models.CharField("Rol", max_length=20, choices=ROLES, default="empleado")
    fecha_ingreso = models.DateField("Fecha de ingreso")
    tipo_contrato = models.CharField("Tipo de contrato", max_length=10,
                                     choices=TIPO_CONTRATO, default="planilla")
    email = models.EmailField("Email corporativo", unique=True)
    dias_vacaciones_tomados = models.PositiveIntegerField("Días de vacaciones tomados", default=0)
    activo = models.BooleanField("Activo", default=True)

    class Meta:
        verbose_name = "Empleado"
        verbose_name_plural = "Empleados"
        ordering = ["apellidos", "nombres"]

    def __str__(self):
        return f"{self.apellidos}, {self.nombres} ({self.dni})"

    @property
    def nombre_completo(self):
        return f"{self.nombres} {self.apellidos}"

    @property
    def antiguedad(self):
        """Campo calculado RF1: antigüedad en años y meses."""
        hoy = date.today()
        meses = (hoy.year - self.fecha_ingreso.year) * 12 + (hoy.month - self.fecha_ingreso.month)
        if hoy.day < self.fecha_ingreso.day:
            meses -= 1
        anios, resto = divmod(max(meses, 0), 12)
        return f"{anios} años, {resto} meses"

    @property
    def dias_vacaciones_disponibles(self):
        """RF6: 30 días por año menos los tomados."""
        return 30 - self.dias_vacaciones_tomados


class Asistencia(models.Model):
    """RF2 - Registro de asistencia (entrada/salida)."""
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name="asistencias")
    fecha = models.DateField("Fecha", default=timezone.now)
    hora_entrada = models.DateTimeField("Hora de entrada")
    hora_salida = models.DateTimeField("Hora de salida", null=True, blank=True)
    horas_trabajadas = models.DecimalField("Horas trabajadas", max_digits=4,
                                           decimal_places=2, default=0)
    horas_extras = models.DecimalField("Horas extras", max_digits=4,
                                       decimal_places=2, default=0)

    class Meta:
        verbose_name = "Asistencia"
        verbose_name_plural = "Asistencias"
        ordering = ["-fecha", "-hora_entrada"]

    def __str__(self):
        return f"{self.empleado.nombre_completo} - {self.fecha}"

    def calcular_horas(self):
        """Calcula horas trabajadas y detecta horas extras (>8h)."""
        if self.hora_salida and self.hora_entrada:
            delta = self.hora_salida - self.hora_entrada
            horas = round(delta.total_seconds() / 3600, 2)
            self.horas_trabajadas = horas
            self.horas_extras = round(max(horas - 8, 0), 2)


class Permiso(models.Model):
    """RF3 - Solicitud de permiso o vacaciones."""
    TIPOS = [
        ("personal", "Personal"), ("medico", "Médico"), ("duelo", "Duelo"),
        ("maternidad", "Maternidad/Paternidad"), ("vacaciones", "Vacaciones"), ("otro", "Otro"),
    ]
    ESTADOS = [("pendiente", "Pendiente"), ("aprobado", "Aprobado"), ("rechazado", "Rechazado")]

    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name="permisos")
    tipo = models.CharField("Tipo", max_length=15, choices=TIPOS)
    fecha_inicio = models.DateField("Fecha de inicio")
    fecha_fin = models.DateField("Fecha de fin")
    motivo = models.TextField("Motivo detallado")
    documento = models.CharField("Documento adjunto (descripción)", max_length=200, blank=True)
    estado = models.CharField("Estado", max_length=12, choices=ESTADOS, default="pendiente")
    aprobado_por = models.ForeignKey(Empleado, on_delete=models.SET_NULL, null=True,
                                     blank=True, related_name="permisos_aprobados")
    creado_en = models.DateTimeField("Solicitado", auto_now_add=True)

    class Meta:
        verbose_name = "Permiso"
        verbose_name_plural = "Permisos"
        ordering = ["-creado_en"]

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.empleado.nombre_completo} [{self.estado}]"

    @property
    def dias_solicitados(self):
        return (self.fecha_fin - self.fecha_inicio).days + 1


class RegistroAuditoria(models.Model):
    """RF5 - Log de auditoría de modificaciones."""
    usuario = models.CharField("Usuario", max_length=150)
    accion = models.CharField("Acción", max_length=200)
    ruta = models.CharField("Ruta", max_length=200)
    timestamp = models.DateTimeField("Fecha/hora", auto_now_add=True)

    class Meta:
        verbose_name = "Registro de auditoría"
        verbose_name_plural = "Registros de auditoría"
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.timestamp:%Y-%m-%d %H:%M} - {self.usuario} - {self.accion}"
