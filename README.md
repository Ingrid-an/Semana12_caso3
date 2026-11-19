# TecnoAndes — Sistema de Control de Asistencia y Permisos (Caso 3)

**Asignatura:** Desarrollo de Aplicaciones Web (IS093A) · Unidad II — Desarrollo Web Fullstack
**Práctica Grupal Semana 12 — Caso 3**
**Integrantes:** Andrade Egoavil Ingrid Ivette · Yaranga Ruiz Josué

Sistema web para la empresa ficticia **TecnoAndes S.A.C.** que automatiza el
registro de asistencia, la gestión de permisos/vacaciones con flujo de
aprobación, y los reportes para planilla, con control de acceso jerárquico.

---

## Estructura del proyecto

```
tecnoandes/
├── manage.py
├── requirements.txt
├── .gitignore
├── config/
│   ├── settings.py          middlewares, sesiones (45 min), CSRF, auth, logging
│   └── urls.py
└── rrhh/
    ├── models.py            Area, Empleado, Asistencia, Permiso, RegistroAuditoria
    ├── forms.py             ModelForm + clásico, validaciones complejas (RF1-RF3)
    ├── admin.py             reportes, filtros, acciones masivas, campos calculados (RF6)
    ├── middleware.py        auditoría, bloqueo de cuenta, recordatorio (RF5)
    ├── views.py             asistencia, permisos, auth, flujo de aprobación (RF2-RF4)
    ├── urls.py
    ├── management/commands/
    │   └── seed_data.py     datos de prueba
    └── templates/rrhh/      base, login, panel, asistencia, permiso
```

---

## Requisitos funcionales cubiertos

- **RF1 Empleados y Áreas:** modelo Empleado con DNI único, email corporativo
  (@tecnoandes.pe), fecha de ingreso no futura, cargo obligatorio, campo
  calculado de antigüedad.
- **RF2 Asistencia:** marcación entrada/salida, validación de entrada duplicada,
  salida posterior a entrada, cálculo de horas y detección de horas extras (>8h).
  Corrección solo RRHH con justificación de 50+ caracteres.
- **RF3 Permisos y Vacaciones:** solicitud con tipo, fechas (fin ≥ inicio), motivo
  de 30+ caracteres, documento, validación de superposición y de días de
  vacaciones disponibles. Flujo pendiente → aprobado/rechazado.
- **RF4 Autenticación y Autorización:** login corporativo, 4 roles (Admin RRHH,
  Jefe de Área, Empleado, Contador), autorización jerárquica, sesión de 45 min.
- **RF5 Middleware:** auditoría de modificaciones, bloqueo de cuentas desactivadas,
  recordatorio de marcación.
- **RF6 Django Admin:** vistas de asistencia y permisos con filtros, acción masiva
  "Aprobar permisos seleccionados", campo calculado de vacaciones disponibles.

---

## Cómo ejecutar (paso a paso)

Requiere **Python 3.11+**.

```bash
# 1. (opcional) entorno virtual
python -m venv venv
venv\Scripts\activate        # Windows

# 2. instalar Django
pip install -r requirements.txt

# 3. migraciones
python manage.py makemigrations
python manage.py migrate

# 4. poblar datos de prueba (10 empleados, 50 asistencias, 10 permisos)
python manage.py seed_data

# 5. superusuario (para el admin)
python manage.py createsuperuser

# 6. arrancar
python manage.py runserver
```

### Usuarios de prueba
Todos los empleados usan su **DNI como usuario** y la contraseña **`tecno2026`**.

| Rol | Usuario (DNI) | Nombre |
|---|---|---|
| Admin RRHH | 40111222 | María Quispe |
| Jefe de Área (Sistemas) | 40222333 | Carlos Mamani |
| Empleado | 40555666 | Ingrid Andrade |
| Contador | 40777888 | Rosa Ticona |

Rutas: `/login/`, `/panel/`, `/asistencia/`, `/permiso/`, `/admin/`.

---

## Mapa de la rúbrica

| Criterio | Dónde |
|---|---|
| Formularios y Validación | `forms.py` (ModelForm + clásico, clean(), clean_campo(), regex, sanitize) |
| Django Admin | `admin.py` (list_display, filtros, acción masiva, @admin.display) |
| Middleware | `middleware.py` (3 middlewares con __init__/__call__) |
| Autenticación y Autorización | `views.py` (login, @login_required, roles jerárquicos) |
| Sesiones y Seguridad | `settings.py` (sesión 45 min, CSRF, X-Frame-Options) |
| Documentación | este README + capturas |

---

## Notas de seguridad
- `db.sqlite3`, `__pycache__/` y `.env` en `.gitignore` (no se suben).
- CSRF activo en todos los formularios POST.
- Validación en servidor (no se confía en el frontend).
- `python manage.py check` sin problemas.
