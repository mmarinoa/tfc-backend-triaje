import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings


class N8NClassificationError(Exception):
    """
    Error controlado al llamar al webhook de n8n o al interpretar su respuesta.
    """


def _parse_n8n_response(raw_response: str) -> dict:
    """
    Convierte la respuesta de n8n en un diccionario Python.

    El workflow definitivo de n8n debe devolver un JSON similar a:

        {
            "id_consulta": 1,
            "id_paciente": 2,
            "prioridad_ia": 4,
            "recomendacion": "Texto breve de recomendación"
        }

    Django utilizará principalmente prioridad_ia y recomendacion.
    """
    try:
        data = json.loads(raw_response)
    except json.JSONDecodeError as error:
        raise N8NClassificationError(
            "n8n no devolvió un JSON válido."
        ) from error

    if not isinstance(data, dict):
        raise N8NClassificationError(
            "La respuesta de n8n no tiene el formato esperado."
        )

    return data


def _extract_priority(data: dict) -> int:
    """
    Obtiene y valida la prioridad IA devuelta por n8n.

    La prioridad debe ser un número entero entre 1 y 5.
    """
    prioridad = data.get("prioridad_ia")

    if prioridad is None:
        raise N8NClassificationError(
            "n8n no devolvió el campo prioridad_ia."
        )

    try:
        prioridad = int(prioridad)
    except (TypeError, ValueError) as error:
        raise N8NClassificationError(
            "La prioridad IA devuelta por n8n no es un número entero."
        ) from error

    if prioridad < 1 or prioridad > 5:
        raise N8NClassificationError(
            "La prioridad IA devuelta por n8n debe estar entre 1 y 5."
        )

    return prioridad


def _extract_recommendation(data: dict) -> str:
    """
    Obtiene la recomendación devuelta por n8n.

    Si n8n no devuelve recomendación, se usa una cadena vacía.
    """
    recomendacion = data.get("recomendacion", "")

    if recomendacion is None:
        return ""

    return str(recomendacion).strip()


def solicitar_clasificacion_n8n(consulta) -> dict:
    """
    Envía una consulta al webhook de n8n y devuelve la clasificación normalizada.

    Devuelve:

        {
            "prioridad_ia": 4,
            "recomendacion": "Texto breve de recomendación"
        }
    """
    webhook_url = getattr(settings, "N8N_TRIAGE_WEBHOOK_URL", "")

    if not webhook_url:
        raise N8NClassificationError(
            "No está configurada la URL del webhook de n8n."
        )

    payload = {
        "consulta_id": consulta.id,
        "paciente_id": consulta.paciente_id,
        "motivo_consulta": consulta.motivo,
    }

    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    request = Request(
        webhook_url,
        data=body,
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "Accept": "application/json",
        },
        method="POST",
    )

    timeout = getattr(settings, "N8N_TRIAGE_TIMEOUT_SECONDS", 15)

    try:
        with urlopen(request, timeout=timeout) as response:
            raw_response = response.read().decode("utf-8")
    except HTTPError as error:
        raise N8NClassificationError(
            f"n8n respondió con error HTTP {error.code}."
        ) from error
    except URLError as error:
        raise N8NClassificationError(
            "No se pudo conectar con n8n."
        ) from error
    except TimeoutError as error:
        raise N8NClassificationError(
            "La llamada a n8n tardó demasiado tiempo."
        ) from error

    data = _parse_n8n_response(raw_response)

    return {
        "prioridad_ia": _extract_priority(data),
        "recomendacion": _extract_recommendation(data),
    }


def construir_observaciones_clasificacion(clasificacion: dict) -> str:
    """
    Construye el texto de observaciones que se guardará en el histórico.
    """
    recomendacion = clasificacion.get("recomendacion", "").strip()

    if recomendacion:
        return (
            "Clasificación generada automáticamente por el agente de IA. "
            f"Recomendación: {recomendacion}"
        )

    return "Clasificación generada automáticamente por el agente de IA."