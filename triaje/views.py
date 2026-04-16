import json

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import Paciente, Consulta

# Create your views here.
@csrf_exempt
def consultas_view(request):
    if request.method == 'GET':
        estado = request.GET.get('estado')
        orden = request.GET.get('orden')

        consultas = Consulta.objects.select_related('paciente', 'categoria').all()

        if estado:
            consultas = consultas.filter(estado=estado)

        if orden == 'prioridad':
            consultas = consultas.order_by('prioridad_ia', 'fecha_creacion')
        else:
            consultas = consultas.order_by('-fecha_creacion')

        data = []
        for consulta in consultas:
            data.append({
                'id': consulta.id,
                'paciente': consulta.paciente.nombre_completo,
                'dni': consulta.paciente.dni,
                'motivo': consulta.motivo,
                'estado': consulta.estado,
                'categoria': consulta.categoria.nombre if consulta.categoria else None,
                'prioridad_ia': consulta.prioridad_ia,
                'fecha_creacion': consulta.fecha_creacion.isoformat(),
            })

        return JsonResponse(data, safe=False, status=200)

    if request.method == 'POST':
        try:
            body = json.loads(request.body)

            nombre_completo = body.get('nombre_completo', '').strip()
            dni = body.get('dni', '').strip().upper()
            motivo = body.get('motivo', '').strip()

            if not nombre_completo or not dni or not motivo:
                return JsonResponse(
                    {'error': 'nombre_completo, dni y motivo son obligatorios'},
                    status=400
                )

            paciente, _ = Paciente.objects.get_or_create(
                dni=dni,
                defaults={'nombre_completo': nombre_completo}
            )

            if paciente.nombre_completo != nombre_completo:
                paciente.nombre_completo = nombre_completo
                paciente.save()

            consulta = Consulta.objects.create(
                paciente=paciente,
                motivo=motivo,
                estado='pendiente'
            )

            return JsonResponse({
                'message': 'Consulta creada correctamente',
                'consulta_id': consulta.id
            }, status=201)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'JSON inválido'}, status=400)

    return JsonResponse({'error': 'Método no permitido'}, status=405)


@csrf_exempt
def consulta_detail_view(request, consulta_id):
    try:
        consulta = Consulta.objects.select_related('paciente', 'categoria').get(id=consulta_id)
    except Consulta.DoesNotExist:
        return JsonResponse({'error': 'Consulta no encontrada'}, status=404)

    if request.method == 'GET':
        data = {
            'id': consulta.id,
            'paciente': consulta.paciente.nombre_completo,
            'dni': consulta.paciente.dni,
            'motivo': consulta.motivo,
            'estado': consulta.estado,
            'categoria': consulta.categoria.nombre if consulta.categoria else None,
            'prioridad_ia': consulta.prioridad_ia,
            'fecha_creacion': consulta.fecha_creacion.isoformat(),
        }
        return JsonResponse(data, status=200)

    if request.method == 'PUT':
        try:
            body = json.loads(request.body)

            motivo = body.get('motivo')
            estado = body.get('estado')
            prioridad_ia = body.get('prioridad_ia')

            if motivo is not None:
                consulta.motivo = motivo.strip()

            if estado is not None:
                consulta.estado = estado

            if prioridad_ia is not None:
                consulta.prioridad_ia = prioridad_ia

            consulta.save()

            return JsonResponse({'message': 'Consulta actualizada correctamente'}, status=200)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'JSON inválido'}, status=400)

    if request.method == 'DELETE':
        consulta.delete()
        return JsonResponse({'message': 'Consulta eliminada correctamente'}, status=200)

    return JsonResponse({'error': 'Método no permitido'}, status=405)