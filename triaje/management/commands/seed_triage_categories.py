from django.core.management.base import BaseCommand
from django.db import transaction

from triaje.models import CategoriaTriage


class Command(BaseCommand):
    help = "Carga las categorías oficiales de triaje."

    CATEGORIAS_OFICIALES = [
        {"nombre": "Rojo", "prioridad": 1},
        {"nombre": "Naranja", "prioridad": 2},
        {"nombre": "Amarillo", "prioridad": 3},
        {"nombre": "Verde", "prioridad": 4},
        {"nombre": "Azul", "prioridad": 5},
    ]

    def handle(self, *args, **options):
        with transaction.atomic():
            categorias_borradas, _ = CategoriaTriage.objects.all().delete()

            categorias_creadas = [
                CategoriaTriage(
                    nombre=categoria["nombre"],
                    prioridad=categoria["prioridad"]
                )
                for categoria in self.CATEGORIAS_OFICIALES
            ]

            CategoriaTriage.objects.bulk_create(categorias_creadas)

        self.stdout.write(
            self.style.SUCCESS(
                f"Categorías de triaje cargadas correctamente. "
                f"Eliminadas: {categorias_borradas}. "
                f"Creadas: {len(categorias_creadas)}."
            )
        )