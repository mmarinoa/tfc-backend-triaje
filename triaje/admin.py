from django.contrib import admin
from .models import Paciente, Consulta, CategoriaTriage, ConsultaCategoriaTriage

# Register your models here.
@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre_completo', 'dni', 'fecha_registro')
    search_fields = ('nombre_completo', 'dni')


@admin.register(CategoriaTriage)
class CategoriaTriageAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'prioridad')
    ordering = ('prioridad',)


@admin.register(Consulta)
class ConsultaAdmin(admin.ModelAdmin):
    list_display = ('id', 'paciente', 'estado', 'categoria', 'prioridad_ia', 'fecha_creacion')
    list_filter = ('estado', 'categoria')
    search_fields = ('paciente__nombre_completo', 'paciente__dni', 'motivo')
    ordering = ('fecha_creacion',)

@admin.register(ConsultaCategoriaTriage)
class ConsultaCategoriaTriageAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'consulta',
        'categoria',
        'prioridad_ia',
        'origen',
        'usuario',
        'fecha_creacion',
    )
    list_filter = (
        'categoria',
        'origen',
        'fecha_creacion',
    )
    search_fields = (
        'consulta__paciente__nombre_completo',
        'consulta__paciente__dni',
        'consulta__motivo',
        'motivo_en_ese_momento',
        'observaciones',
    )
    readonly_fields = (
        'fecha_creacion',
    )
    ordering = (
        '-fecha_creacion',
    )