from django.urls import path
from . import views

app_name = "rrhh"

urlpatterns = [
    path("", views.panel, name="panel"),
    path("panel/", views.panel, name="panel_alt"),
    path("login/", views.iniciar_sesion, name="login"),
    path("logout/", views.cerrar_sesion, name="logout"),
    path("asistencia/", views.marcar_asistencia, name="asistencia"),
    path("permiso/", views.solicitar_permiso, name="permiso"),
    path("permiso/<int:pk>/<str:accion>/", views.aprobar_permiso, name="aprobar"),
]
