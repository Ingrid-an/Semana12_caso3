"""Comando: python manage.py seed_data — datos de prueba del Caso 3."""
import random
from datetime import date, timedelta, datetime, time
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from rrhh.models import Area, Empleado, Asistencia, Permiso


class Command(BaseCommand):
    help = "Puebla datos de prueba: empleados, áreas, asistencias y permisos."

    def handle(self, *args, **opts):
        Asistencia.objects.all().delete()
        Permiso.objects.all().delete()
        Empleado.objects.all().delete()
        Area.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()

        # Áreas (RF1)
        areas = {}
        for n in ["Sistemas", "Contabilidad", "Ventas", "Logística", "RRHH"]:
            areas[n] = Area.objects.create(nombre=n)

        # 10 empleados con roles variados
        base = [
            ("40111222", "María", "Quispe Rojas", "Gerente de RRHH", "RRHH", "admin_rrhh"),
            ("40222333", "Carlos", "Mamani Flores", "Jefe de Sistemas", "Sistemas", "jefe_area"),
            ("40333444", "Lucía", "Huamán Vega", "Jefa de Ventas", "Ventas", "jefe_area"),
            ("40444555", "Josué", "Yaranga Ruiz", "Desarrollador", "Sistemas", "empleado"),
            ("40555666", "Ingrid", "Andrade Egoavil", "Analista QA", "Sistemas", "empleado"),
            ("40666777", "Pedro", "Chávez Luna", "Vendedor", "Ventas", "empleado"),
            ("40777888", "Rosa", "Ticona Apaza", "Contadora", "Contabilidad", "contador"),
            ("40888999", "Luis", "Paredes Soto", "Almacenero", "Logística", "empleado"),
            ("40999000", "Ana", "Cueva Ríos", "Asistente RRHH", "RRHH", "empleado"),
            ("41000111", "Jorge", "Ramos Díaz", "Soporte TI", "Sistemas", "empleado"),
        ]
        empleados = []
        for dni, nom, ape, cargo, area, rol in base:
            user = User.objects.create_user(
                username=dni, password="tecno2026",
                first_name=nom, last_name=ape)
            emp = Empleado.objects.create(
                usuario=user, dni=dni, nombres=nom, apellidos=ape, cargo=cargo,
                area=areas[area], rol=rol,
                fecha_ingreso=date.today() - timedelta(days=random.randint(200, 2000)),
                tipo_contrato=random.choice(["planilla", "locacion"]),
                email=f"{nom.lower()}.{ape.split()[0].lower()}@tecnoandes.pe",
                dias_vacaciones_tomados=random.randint(0, 15))
            empleados.append(emp)

        # 50 registros de asistencia
        for _ in range(50):
            emp = random.choice(empleados)
            dia = date.today() - timedelta(days=random.randint(1, 30))
            h_ent = timezone.make_aware(datetime.combine(dia, time(8, random.randint(0, 30))))
            h_sal = h_ent + timedelta(hours=random.randint(8, 10))
            a = Asistencia(empleado=emp, fecha=dia, hora_entrada=h_ent, hora_salida=h_sal)
            a.calcular_horas()
            a.save()

        # 10 permisos variados
        tipos = ["personal", "medico", "duelo", "vacaciones", "otro"]
        estados = ["pendiente", "aprobado", "rechazado"]
        for i in range(10):
            emp = random.choice(empleados)
            ini = date.today() + timedelta(days=random.randint(1, 20))
            fin = ini + timedelta(days=random.randint(0, 3))
            Permiso.objects.create(
                empleado=emp, tipo=random.choice(tipos),
                fecha_inicio=ini, fecha_fin=fin,
                motivo="Motivo de prueba detallado para la solicitud de permiso número " + str(i),
                estado=random.choice(estados))

        self.stdout.write(self.style.SUCCESS(
            f"OK: {Area.objects.count()} áreas, {Empleado.objects.count()} empleados, "
            f"{Asistencia.objects.count()} asistencias, {Permiso.objects.count()} permisos."))
        self.stdout.write("Usuarios: DNI como username, contraseña 'tecno2026'.")
