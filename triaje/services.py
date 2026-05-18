from django.db import transaction

from .models import CategoriaTriage, Consulta, ConsultaCategoriaTriage


def asignar_categoria_a_consulta(
    consulta: Consulta,
    prioridad_ia: int,
    origen: str = "sistema",
    usuario=None,
    observaciones: str = "",
) -> ConsultaCategoriaTriage:
    """
    Asigna una categoría de triaje a una consulta y guarda el histórico.

    La prioridad IA se usa para buscar la CategoriaTriage correspondiente.
    Por ejemplo:
        prioridad_ia = 1 -> Rojo
        prioridad_ia = 2 -> Naranja
        prioridad_ia = 3 -> Amarillo
        prioridad_ia = 4 -> Verde
        prioridad_ia = 5 -> Azul
    """
    try:
        prioridad_ia = int(prioridad_ia)
    except (TypeError, ValueError):
        raise ValueError("La prioridad IA debe ser un número entero.")

    if prioridad_ia < 1 or prioridad_ia > 5:
        raise ValueError("La prioridad IA debe estar entre 1 y 5.")

    categoria = CategoriaTriage.objects.filter(prioridad=prioridad_ia).first()

    if categoria is None:
        raise ValueError(
            f"No existe una categoría de triaje con prioridad {prioridad_ia}."
        )

    origenes_validos = [
        choice[0]
        for choice in ConsultaCategoriaTriage.ORIGEN_CHOICES
    ]

    if origen not in origenes_validos:
        raise ValueError(
            f"Origen no válido. Valores permitidos: {', '.join(origenes_validos)}."
        )

    with transaction.atomic():
        consulta.prioridad_ia = prioridad_ia
        consulta.categoria = categoria
        consulta.save(update_fields=[
            "prioridad_ia",
            "categoria",
            "fecha_actualizacion",
        ])

        historico = ConsultaCategoriaTriage.objects.create(
            consulta=consulta,
            categoria=categoria,
            prioridad_ia=prioridad_ia,
            motivo_en_ese_momento=consulta.motivo,
            origen=origen,
            usuario=usuario,
            observaciones=observaciones,
        )

    return historico