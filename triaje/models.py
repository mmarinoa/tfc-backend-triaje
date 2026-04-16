from django.db import models

# Create your models here.
class Paciente(models.Model):
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

    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='consultas')
    motivo = models.TextField()
    categoria = models.ForeignKey(
        CategoriaTriage,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='consultas'
    )
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    prioridad_ia = models.IntegerField(null=True, blank=True)
    observaciones = models.TextField(blank=True, default='')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Consulta #{self.id} - {self.paciente.nombre_completo}"