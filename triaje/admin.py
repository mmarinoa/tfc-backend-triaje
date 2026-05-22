from django import forms
from django.contrib import admin, messages

from .models import Paciente, Consulta, CategoriaTriage, ConsultaCategoriaTriage
from .services import asignar_categoria_a_consulta


class ConsultaAdminForm(forms.ModelForm):
    class Meta:
        model = Consulta
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()

        categoria = cleaned_data.get("categoria")
        prioridad_ia = cleaned_data.get("prioridad_ia")

        if categoria is not None:
            cleaned_data["prioridad_ia"] = categoria.prioridad
            return cleaned_data

        if prioridad_ia is not None:
            try:
                prioridad_ia = int(prioridad_ia)
            except (TypeError, ValueError):
                raise forms.ValidationError(
                    "La prioridad IA debe ser un número entero."
                )

            if prioridad_ia < 1 or prioridad_ia > 5:
                raise forms.ValidationError(
                    "La prioridad IA debe estar entre 1 y 5."
                )

        return cleaned_data


@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre_completo", "dni", "fecha_registro")
    search_fields = ("nombre_completo", "dni")


@admin.register(CategoriaTriage)
class CategoriaTriageAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre", "prioridad")
    ordering = ("prioridad",)


@admin.register(Consulta)
class ConsultaAdmin(admin.ModelAdmin):
    form = ConsultaAdminForm

    list_display = (
        "id",
        "paciente",
        "estado",
        "categoria",
        "prioridad_ia",
        "fecha_creacion",
    )
    list_filter = ("estado", "categoria")
    search_fields = ("paciente__nombre_completo", "paciente__dni", "motivo")
    ordering = ("fecha_creacion",)

    def save_model(self, request, obj, form, change):
        categoria_anterior_id = None
        prioridad_anterior = None

        if change and obj.pk:
            consulta_anterior = Consulta.objects.filter(pk=obj.pk).first()

            if consulta_anterior is not None:
                categoria_anterior_id = consulta_anterior.categoria_id
                prioridad_anterior = consulta_anterior.prioridad_ia

        super().save_model(request, obj, form, change)

        categoria_actual_id = obj.categoria_id
        prioridad_actual = obj.prioridad_ia

        es_consulta_nueva_con_categoria = (
            not change and (
                categoria_actual_id is not None or prioridad_actual is not None
            )
        )

        ha_cambiado_categoria = (
            change and categoria_anterior_id != categoria_actual_id
        )

        ha_cambiado_prioridad = (
            change and prioridad_anterior != prioridad_actual
        )

        debe_registrar_historico = (
            es_consulta_nueva_con_categoria
            or ha_cambiado_categoria
            or ha_cambiado_prioridad
        )

        if not debe_registrar_historico:
            return

        if obj.categoria is not None:
            prioridad_para_historico = obj.categoria.prioridad
        else:
            prioridad_para_historico = obj.prioridad_ia

        if prioridad_para_historico is None:
            return

        try:
            asignar_categoria_a_consulta(
                consulta=obj,
                prioridad_ia=prioridad_para_historico,
                origen="medico",
                usuario=request.user,
                observaciones="Categoría modificada manualmente desde Django Admin.",
            )
        except ValueError as error:
            self.message_user(
                request,
                str(error),
                level=messages.ERROR,
            )


@admin.register(ConsultaCategoriaTriage)
class ConsultaCategoriaTriageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "consulta",
        "categoria",
        "prioridad_ia",
        "motivo_resumido",
        "origen",
        "usuario",
        "fecha_creacion",
    )
    list_filter = (
        "categoria",
        "origen",
        "fecha_creacion",
    )
    search_fields = (
        "consulta__paciente__nombre_completo",
        "consulta__paciente__dni",
        "consulta__motivo",
        "motivo_en_ese_momento",
        "observaciones",
    )
    readonly_fields = (
        "fecha_creacion",
    )
    ordering = (
        "-fecha_creacion",
    )

    def motivo_resumido(self, obj):
        motivo = obj.motivo_en_ese_momento or ""

        if len(motivo) > 80:
            return motivo[:80] + "..."

        return motivo

    motivo_resumido.short_description = "Motivo en ese momento"