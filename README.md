# 🏥 TFC Backend Triaje

Backend del proyecto **Sistema de triaje inteligente para urgencias**, desarrollado con **Django** como parte del TFC del ciclo de **Desarrollo de Aplicaciones Multiplataforma**.

Este backend actúa como servidor central del sistema. Se encarga de recibir las peticiones de la aplicación Android, gestionar los pacientes, guardar las consultas médicas, servir la información necesaria para el panel médico y mantener un histórico de los cambios de categoría de triaje.

La idea final del proyecto es que las consultas enviadas por los pacientes puedan ser clasificadas mediante un flujo de **n8n** conectado a un agente de inteligencia artificial. Esta IA devolverá una prioridad numérica y, a partir de esa prioridad, el sistema podrá asignar automáticamente la categoría de triaje correspondiente.

El objetivo no es sustituir al personal médico, sino ofrecer una herramienta de apoyo para ordenar mejor las consultas pendientes y agilizar la revisión inicial de los pacientes.

---

## 🚀 Tecnologías utilizadas

- **Python**
- **Django**
- **SQLite**
- **HTML**
- **CSS**
- **Git / GitHub**
- **Django REST Framework**
- **Simple JWT**
- **OpenAPI**
- **n8n** *(previsto para la integración con IA)*

---

## 📌 Estado actual del proyecto

Actualmente el backend permite:

- Registro de pacientes desde la app Android.
- Login de pacientes desde la app Android.
- Autenticación mediante tokens JWT.
- Validación de usuarios existentes.
- Validación de contraseña incorrecta.
- Validación del formato del DNI.
- Validación de la letra real del DNI.
- Relación 1:1 entre el modelo `Paciente` y el usuario de Django.
- Gestión de pacientes.
- Gestión de consultas protegidas mediante JWT.
- Creación de consultas desde Android.
- Actualización de consultas desde Android.
- Cancelación de consultas desde Android.
- Modelo de categorías de triaje.
- Comando para cargar categorías oficiales de triaje.
- Histórico de cambios de categoría de triaje.
- Relación N:M entre consultas y categorías mediante un modelo intermedio.
- Asignación automática de categoría según la prioridad IA.
- Registro automático del histórico al actualizar la prioridad IA.
- Panel de administración con Django Admin.
- Panel web básico para el médico.
- Endpoints REST propios para registro, login y consultas.
- Conversión manual de objetos Django a JSON mediante serializadores propios.
- Especificación OpenAPI de la API REST.
- Pruebas en local con SQLite.

---

## 🧩 Funcionalidades principales

### Registro de pacientes

El backend permite crear un usuario y un paciente asociado a partir de los datos enviados por Android.

Endpoint:

    POST /api/auth/register/

Ejemplo de JSON recibido:

    {
      "nombre_completo": "Marta Garcia",
      "dni": "12345678Z",
      "email": "marta@test.com",
      "password": "123456"
    }

Respuesta esperada:

    {
      "message": "Usuario registrado correctamente",
      "paciente": {
        "id": 1,
        "nombre_completo": "Marta Garcia",
        "dni": "12345678Z",
        "email": "marta@test.com",
        "fecha_registro": "2026-04-28T09:33:35.753639+00:00"
      }
    }

El DNI se valida en dos pasos:

- Debe tener 8 números y una letra.
- La letra debe corresponder realmente con el número del DNI.

---

### Login de pacientes

El backend comprueba si el usuario existe y si la contraseña es correcta.

Cuando el login es correcto, Django devuelve los datos del paciente junto con los tokens JWT necesarios para autenticar las siguientes peticiones.

Endpoint:

    POST /api/auth/login/

Ejemplo de JSON recibido:

    {
      "email": "marta@test.com",
      "password": "123456"
    }

Respuesta esperada:

    {
      "message": "Login correcto",
      "access": "token_de_acceso",
      "refresh": "token_de_refresco",
      "paciente": {
        "id": 1,
        "nombre_completo": "Marta Garcia",
        "dni": "12345678Z",
        "email": "marta@test.com",
        "fecha_registro": "2026-04-28T09:33:35.753639+00:00"
      }
    }

Errores controlados:

    {
      "error": "Usuario no reconocido, regístrese primero."
    }

    {
      "error": "Contraseña incorrecta."
    }

---

### Gestión de consultas

El backend cuenta con endpoints para listar, crear, consultar, actualizar y cancelar consultas.

Endpoints actuales:

    GET    /api/consultas/
    POST   /api/consultas/
    GET    /api/consultas/<id>/
    PUT    /api/consultas/<id>/
    DELETE /api/consultas/<id>/

Estos endpoints están protegidos mediante JWT. Por tanto, para acceder a ellos es necesario enviar el token de acceso en la cabecera de la petición:

    Authorization: Bearer <access_token>

Actualmente el modelo de consulta ya está preparado para guardar:

- Paciente asociado.
- Motivo de consulta.
- Estado.
- Categoría de triaje actual.
- Prioridad devuelta por IA.
- Observaciones.
- Orden manual.
- Fecha de creación.
- Fecha de actualización.

La aplicación Android ya puede crear, consultar, actualizar y cancelar consultas usando estos endpoints.

---

### Creación de consultas

Cuando un paciente crea una consulta desde Android, se envía únicamente el motivo de consulta. El paciente no se identifica mediante DNI ni nombre en esta petición, sino mediante el token JWT.

Endpoint:

    POST /api/consultas/

Ejemplo de JSON recibido:

    {
      "motivo": "Dolor fuerte en el pecho desde hace una hora"
    }

Respuesta esperada:

    {
      "message": "Consulta creada correctamente",
      "consulta": {
        "id": 1,
        "paciente": {
          "id": 1,
          "nombre_completo": "Marta Garcia",
          "dni": "12345678Z",
          "email": "marta@test.com"
        },
        "motivo": "Dolor fuerte en el pecho desde hace una hora",
        "estado": "pendiente",
        "categoria": null,
        "prioridad_ia": null,
        "observaciones": "",
        "orden_manual": 0,
        "fecha_creacion": "2026-04-28T09:33:35.753639+00:00",
        "fecha_actualizacion": "2026-04-28T09:33:35.753639+00:00"
      }
    }

---

### Actualización de consultas

El backend permite actualizar una consulta concreta mediante una petición `PUT`.

Endpoint:

    PUT /api/consultas/<id>/

Ejemplo de JSON recibido para modificar el motivo:

    {
      "motivo": "Dolor fuerte en el pecho y dificultad para respirar"
    }

También se pueden actualizar campos como el estado o la prioridad IA, siempre con validaciones para evitar valores incorrectos.

Estados válidos:

    pendiente
    en_espera
    atendida
    cancelada

La prioridad IA debe ser un número entero entre 1 y 5.

Ejemplo de JSON recibido para actualizar la prioridad IA:

    {
      "prioridad_ia": 2
    }

Cuando se actualiza `prioridad_ia`, el sistema busca automáticamente la categoría de triaje correspondiente.

Ejemplo:

    prioridad_ia = 2  ->  CategoriaTriage = Naranja

Además, en ese mismo proceso se crea un registro en el histórico de categorías de triaje, guardando la categoría asignada, la prioridad IA, el motivo de consulta en ese momento, el origen del cambio, el usuario y la fecha.

---

### Cancelación de consultas

El endpoint `DELETE` no elimina físicamente la consulta de la base de datos. En su lugar, cambia su estado a `cancelada`.

Endpoint:

    DELETE /api/consultas/<id>/

Respuesta esperada:

    {
      "message": "Consulta cancelada correctamente",
      "consulta": {
        "id": 1,
        "estado": "cancelada"
      }
    }

Este comportamiento permite conservar el registro de la consulta, algo importante en un sistema relacionado con el ámbito sanitario.

---

### Panel médico

El backend incluye una vista web básica para que el personal médico pueda consultar las consultas registradas.

Endpoint:

    GET /api/panel/consultas/

La idea final es que este panel muestre las consultas ordenadas por prioridad de triaje, para facilitar al médico la revisión de los pacientes pendientes.

Actualmente el panel puede ordenar las consultas teniendo en cuenta:

- Orden manual.
- Prioridad sugerida por IA.
- Fecha de creación.

El médico tendrá siempre la última palabra y podrá modificar manualmente el orden de atención si considera que un paciente debe ser atendido antes o después.

---

## 🗂️ Estructura del proyecto

    backend-django/
    ├── backend/              # Configuración principal del proyecto Django
    │   ├── settings.py       # Configuración global
    │   ├── urls.py           # Rutas principales del proyecto
    │   ├── asgi.py
    │   └── wsgi.py
    │
    ├── triaje/               # App principal del sistema
    │   ├── models.py         # Modelos Paciente, Consulta, CategoriaTriage e histórico
    │   ├── views.py          # Vistas y endpoints de la API
    │   ├── urls.py           # Rutas de la app triaje
    │   ├── serializers.py    # Validación y conversión manual a JSON
    │   ├── services.py       # Lógica auxiliar del dominio
    │   ├── admin.py          # Registro de modelos en Django Admin
    │   ├── migrations/       # Migraciones de base de datos
    │   ├── management/       # Comandos personalizados de Django
    │   └── templates/        # Plantillas HTML del panel médico
    │
    ├── db.sqlite3            # Base de datos local de desarrollo
    ├── manage.py             # Comando principal de Django
    ├── requirements.txt      # Dependencias del proyecto
    ├── openapi.yaml          # Especificación OpenAPI de la API REST
    └── README.md

---

## 🗃️ Modelos principales

### Paciente

Representa al paciente registrado en el sistema.

Campos principales:

- `user`: relación 1:1 con el usuario de Django.
- `nombre_completo`: nombre completo del paciente.
- `dni`: documento identificativo único.
- `fecha_registro`: fecha en la que se creó el paciente.

El modelo `Paciente` está vinculado al modelo `User` de Django. De esta forma se aprovecha el sistema de autenticación propio de Django para gestionar usuarios y contraseñas, mientras que el modelo `Paciente` guarda los datos específicos del paciente.

Esta decisión permite representar de forma clara una relación 1:1 dentro del modelo de datos: cada usuario está asociado a un único paciente y cada paciente pertenece a un único usuario.

---

### Consulta

Representa el motivo por el que un paciente acude a urgencias.

Campos principales:

- `paciente`: paciente asociado a la consulta.
- `motivo`: texto escrito por el paciente.
- `categoria`: categoría de triaje actual asignada.
- `estado`: estado actual de la consulta.
- `prioridad_ia`: prioridad numérica devuelta por la IA.
- `observaciones`: información adicional o resumen.
- `orden_manual`: ajuste manual para el orden de atención.
- `fecha_creacion`: fecha de creación.
- `fecha_actualizacion`: última modificación.

La idea es que `prioridad_ia` guarde el número devuelto por la inteligencia artificial. Ese número se utiliza para asignar automáticamente la categoría de triaje correspondiente.

Por ejemplo:

    prioridad_ia = 1  ->  CategoriaTriage = Rojo
    prioridad_ia = 2  ->  CategoriaTriage = Naranja
    prioridad_ia = 3  ->  CategoriaTriage = Amarillo
    prioridad_ia = 4  ->  CategoriaTriage = Verde
    prioridad_ia = 5  ->  CategoriaTriage = Azul

De esta forma, la IA propone una prioridad y el sistema la traduce a una categoría de triaje. Aun así, el médico siempre tendrá la última palabra y podrá modificar el orden de atención o la clasificación si lo considera necesario.

El campo `orden_manual` está pensado precisamente para permitir que el personal médico pueda ajustar el orden de atención desde el panel médico, incluso aunque la IA haya propuesto otra prioridad.

---

### CategoriaTriage

Representa una categoría de prioridad dentro del sistema de triaje.

Campos principales:

- `nombre`: nombre de la categoría.
- `prioridad`: valor numérico asociado a la urgencia.

Categorías oficiales previstas:

    Rojo     -> prioridad 1
    Naranja  -> prioridad 2
    Amarillo -> prioridad 3
    Verde    -> prioridad 4
    Azul     -> prioridad 5

Estas categorías se utilizan para representar visualmente el nivel de urgencia asociado a una consulta. La prioridad numérica permite relacionar el valor devuelto por la IA con una categoría concreta.

---

### ConsultaCategoriaTriage

Representa el histórico de categorías de triaje por las que ha pasado una consulta.

Este modelo actúa como tabla intermedia entre `Consulta` y `CategoriaTriage`, permitiendo representar una relación N:M entre ambas entidades.

Campos principales:

- `consulta`: consulta asociada al cambio de categoría.
- `categoria`: categoría asignada en ese momento.
- `prioridad_ia`: prioridad numérica asociada a esa categoría.
- `motivo_en_ese_momento`: copia del motivo de consulta en el momento del cambio.
- `origen`: indica si el cambio viene de IA, médico o sistema.
- `usuario`: usuario que realizó el cambio, si existe.
- `observaciones`: explicación o comentario adicional.
- `fecha_creacion`: fecha en la que se registró el cambio.

Este modelo permite conservar la trazabilidad de las categorías asignadas a una consulta.

Por ejemplo, una consulta podría tener este histórico:

    09:00  ->  Amarillo  ->  Motivo: "Me duele el tobillo"
    09:15  ->  Naranja   ->  Motivo: "Me duele el tobillo y se me está hinchando mucho"

Esto es útil porque el motivo de consulta puede cambiar y, por tanto, también puede cambiar la categoría de triaje asignada.

---

## 🔗 Relaciones entre modelos

### Relación 1:1

El sistema utiliza una relación 1:1 entre `User` y `Paciente`.

    User 1:1 Paciente

Cada usuario de Django está asociado a un único paciente, y cada paciente pertenece a un único usuario.

---

### Relaciones 1:N

El sistema utiliza varias relaciones 1:N.

    Paciente 1:N Consulta

Un paciente puede tener varias consultas, pero cada consulta pertenece a un único paciente.

    CategoriaTriage 1:N Consulta

Una categoría de triaje puede estar asignada como categoría actual a muchas consultas, pero cada consulta tiene una única categoría actual.

---

### Relación N:M

El sistema representa una relación N:M entre `Consulta` y `CategoriaTriage` mediante el modelo intermedio `ConsultaCategoriaTriage`.

    Consulta N:M CategoriaTriage

Esta relación se implementa de forma práctica mediante dos relaciones 1:N:

    Consulta 1:N ConsultaCategoriaTriage
    CategoriaTriage 1:N ConsultaCategoriaTriage

Esto permite que una consulta pueda pasar por varias categorías a lo largo del tiempo, y que una misma categoría pueda aparecer en el histórico de muchas consultas distintas.

Además, al usar un modelo intermedio propio, se puede guardar información adicional del cambio, como el motivo en ese momento, el origen, el usuario y la fecha.

---

## 🧠 Relación entre prioridad IA, categoría, histórico y orden manual

El sistema diferencia cuatro conceptos importantes.

### Prioridad IA

Es el valor numérico sugerido por la inteligencia artificial. Este número estará entre 1 y 5.

Ejemplo:

    prioridad_ia = 2

En este caso, la IA estaría indicando una prioridad equivalente al nivel 2.

---

### Categoría de triaje

Es la categoría oficial asociada a esa prioridad.

Ejemplo:

    prioridad_ia = 2
    CategoriaTriage = Naranja

La categoría permite representar la prioridad de forma más clara para el personal médico.

---

### Histórico de categorías

Cada vez que se asigna o modifica la prioridad IA de una consulta, el sistema puede registrar un histórico de la categoría asociada.

Esto permite saber:

- Qué categoría tuvo la consulta.
- Qué prioridad IA se aplicó.
- Qué motivo tenía la consulta en ese momento.
- Si el cambio fue realizado por el sistema, la IA o un médico.
- Qué usuario realizó el cambio.
- Cuándo se realizó.

Esto es importante porque una consulta puede cambiar. Por ejemplo, un paciente puede enviar inicialmente un motivo leve y más tarde modificarlo añadiendo nuevos síntomas. En ese caso, la categoría de triaje puede cambiar y el sistema conserva el registro anterior.

---

### Orden manual

Es el ajuste que puede realizar el médico desde el panel web.

Aunque la IA proponga una prioridad y el sistema asigne una categoría, el profesional sanitario podrá modificar el orden si considera que un paciente debe ser atendido antes o después.

La idea final del orden de visualización en el panel médico sería:

    orden_manual -> prioridad_ia -> fecha_creacion

De esta manera, el sistema puede usar la IA como ayuda inicial, pero mantiene la intervención del médico como decisión final.

---

## 🧩 Servicio de asignación de categoría

El proyecto incluye una función de servicio para asignar categorías de triaje de forma controlada.

Archivo:

    triaje/services.py

Función principal:

    asignar_categoria_a_consulta()

Esta función recibe una consulta y una prioridad IA. A partir de esa prioridad, busca la categoría de triaje correspondiente y actualiza la consulta.

Además, crea un registro en `ConsultaCategoriaTriage` para mantener el histórico de categorías.

Ejemplo de funcionamiento:

    prioridad_ia = 2

Resultado:

    consulta.prioridad_ia = 2
    consulta.categoria = Naranja

Y se crea un histórico con:

    consulta
    categoria = Naranja
    prioridad_ia = 2
    motivo_en_ese_momento
    origen
    usuario
    observaciones
    fecha_creacion

Esta lógica evita tener que repetir el mismo código en distintas partes del backend y asegura que cada cambio de prioridad quede registrado correctamente.

---

## 🧰 Comando para cargar categorías de triaje

El proyecto incluye un comando personalizado para cargar las categorías oficiales de triaje.

Comando:

    python manage.py seed_triage_categories

Este comando elimina las categorías existentes y crea de nuevo las categorías oficiales:

    Rojo
    Naranja
    Amarillo
    Verde
    Azul

Esto permite mantener siempre las mismas categorías de triaje, aunque se trabaje desde distintos ordenadores o se reinicie la base de datos local.

---

## 📄 Especificación OpenAPI

La especificación completa de la API REST se encuentra en el archivo:

    openapi.yaml

Este archivo documenta los endpoints principales del backend, los cuerpos JSON esperados, las respuestas posibles y la autenticación mediante JWT.

Endpoints documentados:

    POST   /api/auth/register/
    POST   /api/auth/login/

    GET    /api/consultas/
    POST   /api/consultas/
    GET    /api/consultas/<id>/
    PUT    /api/consultas/<id>/
    DELETE /api/consultas/<id>/

    GET    /api/panel/consultas/

---

## 🔗 Rutas principales

    POST   /api/auth/register/
    POST   /api/auth/login/

    GET    /api/consultas/
    POST   /api/consultas/
    GET    /api/consultas/<id>/
    PUT    /api/consultas/<id>/
    DELETE /api/consultas/<id>/

    GET    /api/panel/consultas/

---

## ▶️ Ejecución en local

Crear y activar el entorno virtual:

    python -m venv venv

En Windows:

    venv\Scripts\activate

Si el entorno virtual está una carpeta por encima del proyecto:

    ..\venv\Scripts\Activate.ps1

Instalar dependencias:

    pip install -r requirements.txt

Aplicar migraciones:

    python manage.py migrate

Cargar categorías oficiales de triaje:

    python manage.py seed_triage_categories

Crear superusuario:

    python manage.py createsuperuser

Ejecutar servidor:

    python manage.py runserver

El servidor estará disponible en:

    http://127.0.0.1:8000/

Panel de administración:

    http://127.0.0.1:8000/admin/

---

## 📱 Conexión con Android

Durante el desarrollo, la app Android se prueba con un emulador de Android Studio.

Desde Android no se usa:

    http://127.0.0.1:8000/

En su lugar se utiliza:

    http://10.0.2.2:8000/

Ejemplo:

    http://10.0.2.2:8000/api/auth/login/

Esto permite que el emulador Android se conecte al servidor Django que está ejecutándose en el ordenador.

En la app Android, la URL base del servidor está centralizada en la clase `ApiConfig.java`, para que no sea necesario cambiarla en varias activities si en el futuro se usa otra IP o un servidor desplegado.

---

## 🤖 Integración prevista con n8n e IA

En una fase posterior, Django enviará a n8n el motivo de consulta del paciente.

Flujo previsto:

    Android --> Django --> n8n --> Agente de IA --> Prioridad IA --> CategoriaTriage --> Django

La IA devolverá una prioridad numérica entre 1 y 5. Django guardará ese valor en `prioridad_ia` y asignará automáticamente la categoría de triaje correspondiente.

Ejemplo:

    IA devuelve prioridad_ia = 2
    Django asigna CategoriaTriage = Naranja

Al asignarse esa categoría, también se creará una entrada en el histórico de categorías de la consulta. Esto permitirá saber qué categoría tuvo cada consulta en cada momento y con qué motivo se asignó.

Después, el médico podrá ver la consulta en el panel web y modificar manualmente el orden o la categoría si lo considera necesario.

---

## 📍 Próximos pasos

- Integrar Django con n8n mediante webhook.
- Clasificar consultas mediante IA.
- Asignar automáticamente la categoría de triaje según la prioridad devuelta por IA.
- Mejorar el panel médico para mostrar consultas ordenadas por prioridad.
- Permitir ajustes manuales del orden desde el panel médico.
- Mostrar el histórico de categorías de forma más detallada en el panel médico.
- Preparar renovación de tokens JWT.
- Preparar despliegue futuro con una base de datos más robusta.

---

## 👩‍💻 Autora

Proyecto desarrollado por **Marta Mariño Alvite** como parte del TFC del ciclo de **Desarrollo de Aplicaciones Multiplataforma**.