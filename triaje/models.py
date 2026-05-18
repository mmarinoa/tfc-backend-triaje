from django.db import models
from django.conf import settings

# Create your models here.
class Paciente(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='paciente'
    )
    nombre_completo = models.CharField(max_length=150)
    dni = models.CharField(max_length=9, unique=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre_completo} ({self.dni})"


class CategoriaTriage(models.Model):
    nombre = models.CharField(max_length=50)
    prioridad = models.IntegerField(unique=True)

    def __str__(self):
        return f"{self.nombre} - {self.prioridad}"


class Consulta(models.Model):
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('en_espera', 'En espera'),
        ('atendida', 'Atendida'),
        ('cancelada', 'Cancelada'),
    ]

    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.CASCADE,
        related_name='consultas'
    )
    motivo = models.TextField()
    categoria = models.ForeignKey(
        CategoriaTriage,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='consultas'
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default='pendiente'
    )
    prioridad_ia = models.IntegerField(null=True, blank=True)
    observaciones = models.TextField(blank=True, default='')
    orden_manual = models.IntegerField(default=0)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Consulta #{self.id} - {self.paciente.nombre_completo}"

class ConsultaCategoriaTriage(models.Model):
    ORIGEN_CHOICES = [
        ('ia', 'Inteligencia artificial'),
        ('medico', 'Médico'),
        ('sistema', 'Sistema'),
    ]

    consulta = models.ForeignKey(
        Consulta,
        on_delete=models.CASCADE,
        related_name='historial_categorias'
    )
    categoria = models.ForeignKey(
        CategoriaTriage,
        on_delete=models.PROTECT,
        related_name='historial_consultas'
    )
    prioridad_ia = models.IntegerField(null=True, blank=True)
    motivo_en_ese_momento = models.TextField()
    origen = models.CharField(
        max_length=20,
        choices=ORIGEN_CHOICES,
        default='sistema'
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cambios_categoria_triaje'
    )
    observaciones = models.TextField(blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha_creacion']
        verbose_name = 'Histórico de categoría de triaje'
        verbose_name_plural = 'Históricos de categorías de triaje'

    def __str__(self):
        return (
            f"Consulta #{self.consulta_id} - "
            f"{self.categoria.nombre} - "
            f"{self.get_origen_display()}"
        )