import re
from typing import Any

from django.contrib.auth.models import User
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

from .models import Paciente, Consulta


DNI_REGEX = r"^[0-9]{8}[A-Za-z]$"


def validate_register_data(data: dict[str, Any]) -> tuple[bool, dict[str, str], dict[str, str]]:
    """
    Para validar los datos q llegan desde Android --> registrar un paciente.

    Devuelve:
    - is_valid: True/False
    - cleaned_data: los datos limpios (si son válidos)
    - errors: errores si algo está mal
    """
    errors: dict[str, str] = {}

    nombre_completo = str(data.get("nombre_completo", "")).strip()
    dni = str(data.get("dni", "")).strip().upper()
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", "")).strip()

    if not nombre_completo:
        errors["nombre_completo"] = "El nombre completo es obligatorio."

    if not dni:
        errors["dni"] = "El DNI es obligatorio."
    elif not re.match(DNI_REGEX, dni):
        errors["dni"] = "El DNI debe tener 8 números y una letra."

    if not email:
        errors["email"] = "El email es obligatorio."
    else:
        try:
            validate_email(email)
        except ValidationError:
            errors["email"] = "El email no tiene un formato válido."

    if not password:
        errors["password"] = "La contraseña es obligatoria."
    elif len(password) < 6:
        errors["password"] = "La contraseña debe tener al menos 6 caracteres."

    if email and User.objects.filter(email=email).exists():
        errors["email"] = "Ya existe un usuario registrado con este email."

    if dni and Paciente.objects.filter(dni=dni).exists():
        errors["dni"] = "Ya existe un paciente registrado con este DNI."

    cleaned_data = {
        "nombre_completo": nombre_completo,
        "dni": dni,
        "email": email,
        "password": password,
    }

    return len(errors) == 0, cleaned_data, errors


def validate_login_data(data: dict[str, Any]) -> tuple[bool, dict[str, str], dict[str, str]]:
    """
    Valida los datos que llegan desde Android para iniciar sesión.
    """
    errors: dict[str, str] = {}

    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", "")).strip()

    if not email:
        errors["email"] = "El email es obligatorio."
    else:
        try:
            validate_email(email)
        except ValidationError:
            errors["email"] = "El email no tiene un formato válido."

    if not password:
        errors["password"] = "La contraseña es obligatoria."

    cleaned_data = {
        "email": email,
        "password": password,
    }

    return len(errors) == 0, cleaned_data, errors


def paciente_to_dict(paciente: Paciente) -> dict[str, Any]:
    """
    Convierte un objeto Paciente de Django en un diccionario JSON-friendly.
    """
    return {
        "id": paciente.id,
        "nombre_completo": paciente.nombre_completo,
        "dni": paciente.dni,
        "email": paciente.user.email,
        "fecha_registro": paciente.fecha_registro.isoformat(),
    }


def consulta_to_dict(consulta: Consulta) -> dict[str, Any]:
    """
    Convierte una Consulta en un diccionario JSON-friendly.
    """
    return {
        "id": consulta.id,
        "paciente": {
            "id": consulta.paciente.id,
            "nombre_completo": consulta.paciente.nombre_completo,
            "dni": consulta.paciente.dni,
            "email": consulta.paciente.user.email,
        },
        "motivo": consulta.motivo,
        "estado": consulta.estado,
        "categoria": consulta.categoria.nombre if consulta.categoria else None,
        "prioridad_ia": consulta.prioridad_ia,
        "observaciones": consulta.observaciones,
        "orden_manual": consulta.orden_manual,
        "fecha_creacion": consulta.fecha_creacion.isoformat(),
        "fecha_actualizacion": consulta.fecha_actualizacion.isoformat(),
    }


def consulta_list_to_dict(consultas) -> list[dict[str, Any]]:
    """
    Convierte una lista de consultas en una lista de diccionarios.
    """
    return [consulta_to_dict(consulta) for consulta in consultas]