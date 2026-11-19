"""Formularios con validación en 3 niveles (campo, formulario, modelo)."""
import re
from datetime import date
from django import forms
from django.utils.html import escape
from .models import Empleado, Asistencia, Permiso, Area


def sanitize_input(texto):
    """Sanitización básica: recorta y escapa HTML (anti-XSS)."""
    if texto is None:
        return ""
    return escape(texto.strip())


# ---------- RF1: ModelForm de Empleado ----------
class EmpleadoForm(forms.ModelForm):
    class Meta:
        model = Empleado
        fields = ["dni", "nombres", "apellidos", "cargo", "area", "rol",
                  "fecha_ingreso", "tipo_contrato", "email"]
        widgets = {"fecha_ingreso": forms.DateInput(attrs={"type": "date"})}

    def clean_dni(self):
        dni = sanitize_input(self.cleaned_data.get("dni"))
        if not re.match(r"^\d{8}$", dni):
            raise forms.ValidationError("El DNI debe tener exactamente 8 dígitos.")
        return dni

    def clean_email(self):
        """Validación: email corporativo @tecnoandes.pe."""
        email = sanitize_input(self.cleaned_data.get("email")).lower()
        if not email.endswith("@tecnoandes.pe"):
            raise forms.ValidationError("El email debe ser corporativo (@tecnoandes.pe).")
        return email

    def clean_cargo(self):
        cargo = sanitize_input(self.cleaned_data.get("cargo"))
        if not cargo:
            raise forms.ValidationError("El cargo no puede estar vacío.")
        return cargo

    def clean_fecha_ingreso(self):
        fecha = self.cleaned_data.get("fecha_ingreso")
        if fecha and fecha > date.today():
            raise forms.ValidationError("La fecha de ingreso no puede ser futura.")
        return fecha


# ---------- RF2: formulario de marcación de asistencia ----------
class AsistenciaForm(forms.ModelForm):
    class Meta:
        model = Asistencia
        fields = ["empleado", "hora_entrada", "hora_salida"]
        widgets = {
            "hora_entrada": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "hora_salida": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    def clean(self):
        """clean() cross-field: salida posterior a entrada + no duplicar entrada."""
        cleaned = super().clean()
        empleado = cleaned.get("empleado")
        entrada = cleaned.get("hora_entrada")
        salida = cleaned.get("hora_salida")

        if entrada and salida and salida <= entrada:
            self.add_error("hora_salida", "La hora de salida debe ser posterior a la entrada.")

        # No registrar entrada si ya hay una del mismo día sin salida
        if empleado and entrada:
            existe = Asistencia.objects.filter(
                empleado=empleado, fecha=entrada.date(), hora_salida__isnull=True
            )
            if self.instance.pk:
                existe = existe.exclude(pk=self.instance.pk)
            if existe.exists():
                raise forms.ValidationError(
                    "Ya existe una entrada sin salida registrada para este empleado hoy.")
        return cleaned

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.fecha = obj.hora_entrada.date()
        obj.calcular_horas()
        if commit:
            obj.save()
        return obj


# ---------- RF3: formulario de solicitud de permiso ----------
class PermisoForm(forms.ModelForm):
    class Meta:
        model = Permiso
        fields = ["empleado", "tipo", "fecha_inicio", "fecha_fin", "motivo", "documento"]
        widgets = {
            "fecha_inicio": forms.DateInput(attrs={"type": "date"}),
            "fecha_fin": forms.DateInput(attrs={"type": "date"}),
            "motivo": forms.Textarea(attrs={"rows": 3}),
        }

    def clean_motivo(self):
        """Validación: motivo mínimo 30 caracteres."""
        motivo = sanitize_input(self.cleaned_data.get("motivo"))
        if len(motivo) < 30:
            raise forms.ValidationError("El motivo debe tener al menos 30 caracteres.")
        return motivo

    def clean(self):
        """clean() cross-field: fechas, superposición y días de vacaciones."""
        cleaned = super().clean()
        empleado = cleaned.get("empleado")
        inicio = cleaned.get("fecha_inicio")
        fin = cleaned.get("fecha_fin")
        tipo = cleaned.get("tipo")

        if inicio and fin:
            if fin < inicio:
                self.add_error("fecha_fin", "La fecha de fin debe ser mayor o igual a la de inicio.")
            else:
                dias = (fin - inicio).days + 1
                # Superposición de permisos
                if empleado:
                    solapados = Permiso.objects.filter(
                        empleado=empleado, estado__in=["pendiente", "aprobado"],
                        fecha_inicio__lte=fin, fecha_fin__gte=inicio,
                    )
                    if self.instance.pk:
                        solapados = solapados.exclude(pk=self.instance.pk)
                    if solapados.exists():
                        raise forms.ValidationError(
                            "El empleado ya tiene un permiso que se superpone con estas fechas.")
                # Días de vacaciones disponibles
                if tipo == "vacaciones" and empleado:
                    if dias > empleado.dias_vacaciones_disponibles:
                        self.add_error("fecha_fin",
                            f"Solo tiene {empleado.dias_vacaciones_disponibles} días de vacaciones disponibles.")
        return cleaned


# ---------- RF2: corrección de asistencia (solo RRHH) - formulario clásico ----------
class CorreccionForm(forms.Form):
    MOTIVOS = [("error_sistema", "Error de sistema"), ("olvido", "Olvido"), ("otro", "Otro")]
    motivo = forms.ChoiceField(label="Motivo", choices=MOTIVOS)
    justificacion = forms.CharField(label="Justificación", widget=forms.Textarea(attrs={"rows": 4}))

    def clean_justificacion(self):
        """Validación: justificación obligatoria mínimo 50 caracteres."""
        just = sanitize_input(self.cleaned_data.get("justificacion"))
        if len(just) < 50:
            raise forms.ValidationError("La justificación debe tener al menos 50 caracteres.")
        return just
