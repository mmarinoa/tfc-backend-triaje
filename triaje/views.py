import json
from datetime import timedelta

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Max
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse, OpenApiParameter, inline_serializer, extend_schema_view
from rest_framework import serializers

from .models import Paciente, Consulta, CategoriaTriage
from .n8n_client import (
    N8NClassificationError,
    construir_observaciones_clasificacion,
    solicitar_clasificacion_n8n,
)
from .serializers import (
    consulta_to_dict,
    paciente_to_dict,
    validate_login_data,
    validate_register_data,
)
from .services import asignar_categoria_a_consulta


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


def get_authenticated_user(request):
    """
    Comprueba el token JWT enviado en la cabecera Authorization.

    Formato esperado:
    Authorization: Bearer <access_token>
    """
    jwt_authenticator = JWTAuthentication()

    try:
        auth_result = jwt_authenticator.authenticate(request)
    except (AuthenticationFailed, InvalidToken, TokenError):
        return None, JsonResponse(
            {'error': 'Token inválido o caducado.'},
            status=401
        )

    if auth_result is None:
        return None, JsonResponse(
            {'error': 'Autenticación requerida.'},
            status=401
        )

    user, _ = auth_result

    if not user.is_active:
        return None, JsonResponse(
            {'error': 'Usuario inactivo.'},
            status=401
        )

    return user, None

@extend_schema(
    tags=["Autenticación"],
    summary="Registrar paciente",
    description="Crea un usuario de Django y un paciente asociado.",
    auth=[],
    request=inline_serializer(
        name="RegistroPacienteRequest",
        fields={
            "nombre_completo": serializers.CharField(),
            "dni": serializers.CharField(),
            "email": serializers.EmailField(),
            "password": serializers.CharField(),
        },
    ),
    responses={
        201: inline_serializer(
            name="RegistroPacienteResponse",
            fields={
                "message": serializers.CharField(),
                "paciente": serializers.DictField(),
            },
        ),
        400: OpenApiResponse(description="Datos inválidos."),
    },
    examples=[
        OpenApiExample(
            "Ejemplo de registro",
            value={
                "nombre_completo": "Marta Garcia",
                "dni": "12345678A",
                "email": "marta@test.com",
                "password": "123456",
            },
            request_only=True,
        )
    ],
)
@api_view(["POST"])
@permission_classes([AllowAny])

@csrf_exempt
def register_view(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)

    is_valid, cleaned_data, errors = validate_register_data(body)

    if not is_valid:
        return JsonResponse({'errors': errors}, status=400)

    try:
        with transaction.atomic():
            user = User.objects.create_user(
                username=cleaned_data['email'],
                email=cleaned_data['email'],
                password=cleaned_data['password'],
            )

            paciente = Paciente.objects.create(
                user=user,
                nombre_completo=cleaned_data['nombre_completo'],
                dni=cleaned_data['dni'],
            )

    except Exception:
        return JsonResponse(
            {'error': 'No se pudo registrar el usuario.'},
            status=500
        )

    return JsonResponse(
        {
            'message': 'Usuario registrado correctamente',
            'paciente': paciente_to_dict(paciente),
        },
        status=201
    )

@extend_schema(
    tags=["Autenticación"],
    summary="Iniciar sesión",
    description=(
        "Autentica a un paciente mediante email y contraseña. "
        "Si las credenciales son correctas, devuelve los tokens JWT y los datos del paciente."
    ),
    auth=[],
    request=inline_serializer(
        name="LoginRequest",
        fields={
            "email": serializers.EmailField(),
            "password": serializers.CharField(),
        },
    ),
    responses={
        200: inline_serializer(
            name="LoginResponse",
            fields={
                "message": serializers.CharField(),
                "access": serializers.CharField(),
                "refresh": serializers.CharField(),
                "paciente": serializers.DictField(),
            },
        ),
        400: OpenApiResponse(description="JSON inválido o datos incompletos."),
        401: OpenApiResponse(description="Credenciales incorrectas."),
    },
    examples=[
        OpenApiExample(
            "Ejemplo de login",
            value={
                "email": "marta@test.com",
                "password": "123456",
            },
            request_only=True,
        )
    ],
)
@api_view(["POST"])
@permission_classes([AllowAny])

@csrf_exempt
def login_view(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)

    is_valid, cleaned_data, errors = validate_login_data(body)

    if not is_valid:
        return JsonResponse({'errors': errors}, status=400)

    email = cleaned_data['email']
    password = cleaned_data['password']

    user = User.objects.filter(email=email).first()

    if user is None:
        return JsonResponse(
            {'error': 'Usuario no reconocido, regístrese primero.'},
            status=404
        )

    authenticated_user = authenticate(
        request,
        username=user.username,
        password=password
    )

    if authenticated_user is None:
        return JsonResponse(
            {'error': 'Contraseña incorrecta.'},
            status=401
        )

    try:
        paciente = authenticated_user.paciente
    except Paciente.DoesNotExist:
        return JsonResponse(
            {'error': 'El usuario existe, pero no tiene paciente asociado.'},
            status=500
        )

    tokens = get_tokens_for_user(authenticated_user)

    return JsonResponse(
        {
            'message': 'Login correcto',
            'access': tokens['access'],
            'refresh': tokens['refresh'],
            'paciente': paciente_to_dict(paciente),
        },
        status=200
    )

@extend_schema_view(
    get=extend_schema(
        tags=["Consultas"],
        summary="Listar consultas",
        description=(
            "Devuelve las consultas del paciente autenticado. "
            "Permite filtrar por estado mediante query param."
        ),
        parameters=[
            OpenApiParameter(
                name="estado",
                description="Filtra las consultas por estado.",
                required=False,
                type=str,
                location=OpenApiParameter.QUERY,
                examples=[
                    OpenApiExample("Pendiente", value="pendiente"),
                    OpenApiExample("En espera", value="en_espera"),
                    OpenApiExample("Atendida", value="atendida"),
                    OpenApiExample("Cancelada", value="cancelada"),
                ],
            )
        ],
        responses={
            200: inline_serializer(
                name="ConsultaListResponse",
                many=True,
                fields={
                    "id": serializers.IntegerField(),
                    "paciente": serializers.DictField(),
                    "motivo": serializers.CharField(),
                    "estado": serializers.CharField(),
                    "categoria": serializers.CharField(allow_blank=True, required=False),
                    "prioridad_ia": serializers.IntegerField(required=False, allow_null=True),
                    "observaciones": serializers.CharField(required=False, allow_blank=True),
                    "orden_manual": serializers.IntegerField(),
                    "fecha_creacion": serializers.DateTimeField(),
                    "fecha_actualizacion": serializers.DateTimeField(),
                },
            ),
            401: OpenApiResponse(description="Autenticación requerida."),
        },
    ),
    post=extend_schema(
        tags=["Consultas"],
        summary="Crear consulta",
        description=(
            "Crea una nueva consulta para el paciente autenticado. "
            "Después de guardarla, el backend puede enviarla a n8n para obtener "
            "una clasificación automática mediante IA."
        ),
        request=inline_serializer(
            name="ConsultaCreateRequest",
            fields={
                "motivo": serializers.CharField(),
            },
        ),
        responses={
            201: inline_serializer(
                name="ConsultaCreateResponse",
                fields={
                    "id": serializers.IntegerField(),
                    "paciente": serializers.DictField(),
                    "motivo": serializers.CharField(),
                    "estado": serializers.CharField(),
                    "categoria": serializers.CharField(allow_blank=True, required=False),
                    "prioridad_ia": serializers.IntegerField(required=False, allow_null=True),
                    "observaciones": serializers.CharField(required=False, allow_blank=True),
                    "orden_manual": serializers.IntegerField(),
                    "fecha_creacion": serializers.DateTimeField(),
                    "fecha_actualizacion": serializers.DateTimeField(),
                },
            ),
            400: OpenApiResponse(description="Datos inválidos."),
            401: OpenApiResponse(description="Autenticación requerida."),
        },
        examples=[
            OpenApiExample(
                "Ejemplo de creación de consulta",
                value={
                    "motivo": "Me duele el tobillo y se me está hinchando bastante"
                },
                request_only=True,
            )
        ],
    ),
)
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])

@csrf_exempt
def consultas_view(request):
    user, auth_error = get_authenticated_user(request)

    if auth_error is not None:
        return auth_error

    if request.method == 'GET':
        estado = request.GET.get('estado')
        orden = request.GET.get('orden')

        consultas = Consulta.objects.select_related(
            'paciente',
            'paciente__user',
            'categoria'
        )

        if not user.is_staff and not user.is_superuser:
            consultas = consultas.filter(paciente__user=user)

        if estado:
            consultas = consultas.filter(estado=estado)

        if orden == 'prioridad':
            consultas = consultas.order_by('prioridad_ia', 'fecha_creacion')
        else:
            consultas = consultas.order_by('-fecha_creacion')

        data = [consulta_to_dict(consulta) for consulta in consultas]

        return JsonResponse(data, safe=False, status=200)

    if request.method == 'POST':
        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'JSON inválido'}, status=400)

        motivo = body.get('motivo', '').strip()

        if not motivo:
            return JsonResponse(
                {'error': 'El motivo de consulta es obligatorio.'},
                status=400
            )

        try:
            paciente = user.paciente
        except Paciente.DoesNotExist:
            return JsonResponse(
                {'error': 'El usuario autenticado no tiene paciente asociado.'},
                status=403
            )

        limite_duplicado = timezone.now() - timedelta(minutes=2)

        consulta_duplicada = Consulta.objects.filter(
            paciente=paciente,
            motivo__iexact=motivo,
            estado__in=['pendiente', 'en_espera'],
            fecha_creacion__gte=limite_duplicado,
        ).select_related(
            'paciente',
            'paciente__user',
            'categoria',
        ).order_by('-fecha_creacion').first()

        if consulta_duplicada is not None:
            return JsonResponse(
                {
                    'message': 'Consulta ya registrada recientemente',
                    'consulta': consulta_to_dict(consulta_duplicada),
                    'aviso': (
                        'Ya existe una consulta reciente con el mismo motivo. '
                        'Se devuelve la consulta existente para evitar duplicados.'
                    )
                },
                status=200
            )
        
        consulta = Consulta.objects.create(
            paciente=paciente,
            motivo=motivo,
            estado='pendiente'
        )

        clasificacion_n8n = None
        aviso_n8n = None

        try:
            clasificacion_n8n = solicitar_clasificacion_n8n(consulta)
            observaciones = construir_observaciones_clasificacion(
                clasificacion_n8n
            )

            asignar_categoria_a_consulta(
                consulta=consulta,
                prioridad_ia=clasificacion_n8n['prioridad_ia'],
                origen='ia',
                usuario=None,
                observaciones=observaciones,
            )

            consulta.estado = 'en_espera'
            consulta.observaciones = observaciones
            consulta.save(update_fields=[
                'estado',
                'observaciones',
                'fecha_actualizacion',
            ])
            consulta.refresh_from_db()

        except N8NClassificationError as error:
            aviso_n8n = str(error)

        except ValueError as error:
            aviso_n8n = str(error)

        response_data = {
            'message': 'Consulta creada correctamente',
            'consulta': consulta_to_dict(consulta),
        }

        if clasificacion_n8n is not None:
            response_data['clasificacion_n8n'] = clasificacion_n8n

        if aviso_n8n is not None:
            response_data['aviso_n8n'] = aviso_n8n

        return JsonResponse(response_data, status=201)

    return JsonResponse({'error': 'Método no permitido'}, status=405)

@extend_schema_view(
    get=extend_schema(
        tags=["Consultas"],
        summary="Obtener detalle de consulta",
        description="Devuelve el detalle de una consulta concreta del paciente autenticado.",
        parameters=[
            OpenApiParameter(
                name="consulta_id",
                description="Identificador de la consulta.",
                required=True,
                type=int,
                location=OpenApiParameter.PATH,
            )
        ],
        responses={
            200: inline_serializer(
                name="ConsultaDetailResponse",
                fields={
                    "id": serializers.IntegerField(),
                    "paciente": serializers.DictField(),
                    "motivo": serializers.CharField(),
                    "estado": serializers.CharField(),
                    "categoria": serializers.CharField(allow_blank=True, required=False),
                    "prioridad_ia": serializers.IntegerField(required=False, allow_null=True),
                    "observaciones": serializers.CharField(required=False, allow_blank=True),
                    "orden_manual": serializers.IntegerField(),
                    "fecha_creacion": serializers.DateTimeField(),
                    "fecha_actualizacion": serializers.DateTimeField(),
                },
            ),
            401: OpenApiResponse(description="Autenticación requerida."),
            404: OpenApiResponse(description="Consulta no encontrada."),
        },
    ),
    put=extend_schema(
        tags=["Consultas"],
        summary="Actualizar motivo de consulta",
        description=(
            "Actualiza el motivo de una consulta del paciente autenticado. "
            "Tras modificar el motivo, el backend puede volver a enviarla a n8n "
            "para recalcular la prioridad IA y la categoría de triaje."
        ),
        parameters=[
            OpenApiParameter(
                name="consulta_id",
                description="Identificador de la consulta.",
                required=True,
                type=int,
                location=OpenApiParameter.PATH,
            )
        ],
        request=inline_serializer(
            name="ConsultaUpdateRequest",
            fields={
                "motivo": serializers.CharField(),
            },
        ),
        responses={
            200: inline_serializer(
                name="ConsultaUpdateResponse",
                fields={
                    "id": serializers.IntegerField(),
                    "paciente": serializers.DictField(),
                    "motivo": serializers.CharField(),
                    "estado": serializers.CharField(),
                    "categoria": serializers.CharField(allow_blank=True, required=False),
                    "prioridad_ia": serializers.IntegerField(required=False, allow_null=True),
                    "observaciones": serializers.CharField(required=False, allow_blank=True),
                    "orden_manual": serializers.IntegerField(),
                    "fecha_creacion": serializers.DateTimeField(),
                    "fecha_actualizacion": serializers.DateTimeField(),
                },
            ),
            400: OpenApiResponse(description="Datos inválidos."),
            401: OpenApiResponse(description="Autenticación requerida."),
            404: OpenApiResponse(description="Consulta no encontrada."),
        },
        examples=[
            OpenApiExample(
                "Ejemplo de actualización de consulta",
                value={
                    "motivo": "El dolor ha empeorado y ahora tengo inflamación"
                },
                request_only=True,
            )
        ],
    ),
    delete=extend_schema(
        tags=["Consultas"],
        summary="Cancelar consulta",
        description=(
            "Cancela una consulta del paciente autenticado. "
            "La consulta no se elimina físicamente, sino que cambia su estado a cancelada."
        ),
        parameters=[
            OpenApiParameter(
                name="consulta_id",
                description="Identificador de la consulta.",
                required=True,
                type=int,
                location=OpenApiParameter.PATH,
            )
        ],
        responses={
            200: inline_serializer(
                name="ConsultaCancelResponse",
                fields={
                    "message": serializers.CharField(),
                    "consulta": serializers.DictField(),
                },
            ),
            401: OpenApiResponse(description="Autenticación requerida."),
            404: OpenApiResponse(description="Consulta no encontrada."),
        },
    ),
)
@api_view(["GET", "PUT", "DELETE"])
@permission_classes([IsAuthenticated])

@csrf_exempt
def consulta_detail_view(request, consulta_id):
    user, auth_error = get_authenticated_user(request)

    if auth_error is not None:
        return auth_error

    try:
        consulta = Consulta.objects.select_related(
            'paciente',
            'paciente__user',
            'categoria'
        ).get(id=consulta_id)
    except Consulta.DoesNotExist:
        return JsonResponse({'error': 'Consulta no encontrada'}, status=404)

    if not user.is_staff and not user.is_superuser:
        if consulta.paciente.user_id != user.id:
            return JsonResponse({'error': 'Consulta no encontrada'}, status=404)

    if request.method == 'GET':
        return JsonResponse(consulta_to_dict(consulta), status=200)

    if request.method == 'PUT':
        try:
            body = json.loads(request.body)

            motivo = body.get('motivo')
            estado = body.get('estado')
            prioridad_ia = body.get('prioridad_ia')
            motivo_actualizado = False
            aviso_n8n = None
            clasificacion_n8n = None

            if motivo is not None:
                motivo = motivo.strip()

                if not motivo:
                    return JsonResponse(
                        {'error': 'El motivo de consulta no puede estar vacío.'},
                        status=400
                    )

                if motivo != consulta.motivo:
                    consulta.motivo = motivo
                    motivo_actualizado = True

            if estado is not None:
                estados_validos = [choice[0] for choice in Consulta.ESTADOS]

                if estado not in estados_validos:
                    return JsonResponse(
                        {
                            'error': 'Estado no válido.',
                            'estados_validos': estados_validos,
                        },
                        status=400
                    )

                consulta.estado = estado

            if prioridad_ia is not None:
                try:
                    asignar_categoria_a_consulta(
                        consulta=consulta,
                        prioridad_ia=prioridad_ia,
                        origen='sistema',
                        usuario=user if user.is_authenticated else None,
                        observaciones='Categoría asignada desde actualización de consulta.'
                    )
                except ValueError as error:
                    return JsonResponse(
                        {'error': str(error)},
                        status=400
                    )

            consulta.save()
            consulta.refresh_from_db()

            puede_reclasificar = consulta.estado not in [
                'cancelada',
                'atendida',
            ]

            if motivo_actualizado and puede_reclasificar:
                try:
                    clasificacion_n8n = solicitar_clasificacion_n8n(consulta)
                    observaciones = construir_observaciones_clasificacion(
                        clasificacion_n8n
                    )

                    asignar_categoria_a_consulta(
                        consulta=consulta,
                        prioridad_ia=clasificacion_n8n['prioridad_ia'],
                        origen='ia',
                        usuario=None,
                        observaciones=observaciones,
                    )

                    consulta.estado = 'en_espera'
                    consulta.observaciones = observaciones
                    consulta.save(update_fields=[
                        'estado',
                        'observaciones',
                        'fecha_actualizacion',
                    ])
                    consulta.refresh_from_db()

                except N8NClassificationError as error:
                    aviso_n8n = str(error)

                except ValueError as error:
                    aviso_n8n = str(error)

            response_data = {
                'message': 'Consulta actualizada correctamente',
                'consulta': consulta_to_dict(consulta),
            }

            if clasificacion_n8n is not None:
                response_data['clasificacion_n8n'] = clasificacion_n8n

            if aviso_n8n is not None:
                response_data['aviso_n8n'] = aviso_n8n

            return JsonResponse(response_data, status=200)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'JSON inválido'}, status=400)

    if request.method == 'DELETE':
        consulta.estado = 'cancelada'
        consulta.save()

        return JsonResponse({
            'message': 'Consulta cancelada correctamente',
            'consulta': consulta_to_dict(consulta),
        }, status=200)

    return JsonResponse({'error': 'Método no permitido'}, status=405)


def panel_medico_view(request):
    filtro_estado = request.GET.get('estado', 'activas')

    consultas = Consulta.objects.select_related(
        'paciente',
        'paciente__user',
        'categoria'
    )

    if filtro_estado == 'activas':
        consultas = consultas.filter(estado__in=['pendiente', 'en_espera'])
    elif filtro_estado in ['pendiente', 'en_espera', 'atendida', 'cancelada']:
        consultas = consultas.filter(estado=filtro_estado)

    consultas = consultas.order_by(
        'orden_manual',
        'prioridad_ia',
        'fecha_creacion'
    )

    estados_filtro = [
        {'valor': 'activas', 'texto': 'Activas'},
        {'valor': 'pendiente', 'texto': 'Pendientes'},
        {'valor': 'en_espera', 'texto': 'En espera'},
        {'valor': 'atendida', 'texto': 'Atendidas'},
        {'valor': 'cancelada', 'texto': 'Canceladas'},
        {'valor': 'todas', 'texto': 'Todas'},
    ]

    categorias_triaje = CategoriaTriage.objects.order_by('prioridad')

    return render(
        request,
        'triaje/panel_medico.html',
        {
            'consultas': consultas,
            'filtro_estado': filtro_estado,
            'estados_filtro': estados_filtro,
            'categorias_triaje': categorias_triaje,
        }
    )

def panel_consultas_version_view(request):
    filtro_estado = request.GET.get('estado', 'activas')

    consultas = Consulta.objects.all()

    if filtro_estado == 'activas':
        consultas = consultas.filter(estado__in=['pendiente', 'en_espera'])
    elif filtro_estado in ['pendiente', 'en_espera', 'atendida', 'cancelada']:
        consultas = consultas.filter(estado=filtro_estado)

    resumen = consultas.aggregate(
        ultima_actualizacion=Max('fecha_actualizacion')
    )

    ultima_actualizacion = resumen['ultima_actualizacion']
    total = consultas.count()

    if ultima_actualizacion is None:
        version = f"empty-{total}"
    else:
        version = f"{ultima_actualizacion.isoformat()}-{total}"

    return JsonResponse(
        {
            'version': version,
            'total': total,
        },
        status=200
    )

@require_POST
def panel_marcar_atendida_view(request, consulta_id):
    consulta = get_object_or_404(Consulta, id=consulta_id)

    if consulta.estado != 'cancelada':
        consulta.estado = 'atendida'
        consulta.save(update_fields=[
            'estado',
            'fecha_actualizacion',
        ])

    return redirect('/api/panel/consultas/')

@require_POST
def panel_actualizar_orden_view(request, consulta_id):
    consulta = get_object_or_404(Consulta, id=consulta_id)

    orden_manual = request.POST.get('orden_manual', '0')

    try:
        orden_manual = int(orden_manual)
    except (TypeError, ValueError):
        orden_manual = 0

    if orden_manual < 0:
        orden_manual = 0

    consulta.orden_manual = orden_manual
    consulta.save(update_fields=[
        'orden_manual',
        'fecha_actualizacion',
    ])

    return redirect('/api/panel/consultas/')

@require_POST
def panel_actualizar_categoria_view(request, consulta_id):
    consulta = get_object_or_404(Consulta, id=consulta_id)

    categoria_id = request.POST.get('categoria_id')

    if not categoria_id:
        return redirect('/api/panel/consultas/')

    categoria = get_object_or_404(CategoriaTriage, id=categoria_id)

    try:
        asignar_categoria_a_consulta(
            consulta=consulta,
            prioridad_ia=categoria.prioridad,
            origen='medico',
            usuario=request.user if request.user.is_authenticated else None,
            observaciones='Categoría modificada manualmente desde el panel médico.'
        )
    except ValueError:
        return redirect('/api/panel/consultas/')

    consulta.refresh_from_db()

    return redirect('/api/panel/consultas/')