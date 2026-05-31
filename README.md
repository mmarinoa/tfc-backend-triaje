# 🏥 TFC Backend Triaje

Backend del proyecto **Sistema de triaje inteligente para urgencias**, desarrollado con **Django** como parte del TFC del ciclo de **Desarrollo de Aplicaciones Multiplataforma**.

Este backend actúa como servidor central del sistema. Se encarga de recibir las peticiones de la aplicación Android, gestionar pacientes, guardar consultas médicas, comunicarse con n8n para obtener una clasificación automática mediante inteligencia artificial y servir el panel médico web.

El objetivo del proyecto no es sustituir al personal sanitario, sino ofrecer una herramienta de apoyo para organizar mejor las consultas pendientes y agilizar la revisión inicial de los pacientes. La IA propone una prioridad y una recomendación, pero el médico puede revisar la consulta, cambiar la categoría de triaje, modificar el orden de atención o marcar la consulta como atendida.

---

## 🚀 Tecnologías utilizadas

- **Python**
- **Django**
- **SQLite**
- **HTML**
- **CSS**
- **JavaScript**
- **Git / GitHub**
- **Django REST Framework**
- **Simple JWT**
- **drf-spectacular**
- **OpenAPI / Swagger**
- **n8n**
- **Agente de inteligencia artificial**

---

## 📌 Estado actual del proyecto

Actualmente el backend permite:

- Registro de pacientes desde la app Android.
- Login de pacientes desde la app Android.
- Autenticación mediante tokens JWT.
- Relación 1:1 entre el modelo `Paciente` y el usuario de Django.
- Validación de usuarios existentes.
- Validación de contraseña incorrecta.
- Validación de formato del DNI.
- Validación de letra real del DNI.
- Gestión de consultas protegidas mediante JWT.
- Creación de consultas desde Android.
- Consulta del detalle de una consulta.
- Actualización del motivo de una consulta.
- Reclasificación automática al modificar el motivo.
- Cancelación lógica de consultas.
- Modelo de categorías de triaje.
- Comando para cargar categorías oficiales de triaje.
- Histórico de cambios de categoría de triaje.
- Relación N:M entre consultas y categorías mediante modelo intermedio.
- Integración real con n8n mediante webhook.
- Clasificación automática mediante agente de IA.
- Asignación automática de categoría según prioridad IA.
- Registro automático del histórico al asignar o modificar una categoría.
- Panel de administración con Django Admin.
- Panel médico web para revisar consultas activas.
- Filtro de consultas por estado en el panel médico.
- Visualización de recomendación generada por IA.
- Cambio manual de categoría desde el panel médico.
- Cambio de orden manual de atención.
- Marcado de consultas como atendidas.
- Actualización automática del panel médico mediante polling.
- Endpoints REST propios para registro, login y consultas.
- Conversión manual de objetos Django a JSON mediante serializadores propios.
- Documentación Swagger/OpenAPI generada con `drf-spectacular`.
- Pruebas en local con SQLite.

---

## 🧩 Funcionalidades principales

### Registro de pacientes

El backend permite crear un usuario de Django y un paciente asociado a partir de los datos enviados por Android.

Endpoint:

```http
POST /api/auth/register/
```

Ejemplo de JSON recibido:

```json
{
  "nombre_completo": "Marta Garcia",
  "dni": "12345678Z",
  "email": "marta@test.com",
  "password": "123456"
}
```

Respuesta esperada:

```json
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
```

El DNI se valida en dos pasos:

- Debe tener 8 números y una letra.
- La letra debe corresponder realmente con el número del DNI.

---

### Login de pacientes

El backend comprueba si el usuario existe y si la contraseña es correcta.

Cuando el login es correcto, Django devuelve los datos del paciente junto con los tokens JWT necesarios para autenticar las siguientes peticiones.

Endpoint:

```http
POST /api/auth/login/
```

Ejemplo de JSON recibido:

```json
{
  "email": "marta@test.com",
  "password": "123456"
}
```

Respuesta esperada:

```json
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
```

Errores controlados:

```json
{
  "error": "Usuario no reconocido, regístrese primero."
}
```

```json
{
  "error": "Contraseña incorrecta."
}
```

---

## 🩺 Gestión de consultas

El backend cuenta con endpoints para listar, crear, consultar, actualizar y cancelar consultas.

Endpoints actuales:

```http
GET    /api/consultas/
POST   /api/consultas/
GET    /api/consultas/<id>/
PUT    /api/consultas/<id>/
DELETE /api/consultas/<id>/
```

Estos endpoints están protegidos mediante JWT. Para acceder a ellos es necesario enviar el token de acceso en la cabecera de la petición:

```http
Authorization: Bearer <access_token>
```

El modelo de consulta guarda:

- Paciente asociado.
- Motivo de consulta.
- Estado.
- Categoría de triaje actual.
- Prioridad devuelta por IA.
- Observaciones o recomendación.
- Orden manual.
- Fecha de creación.
- Fecha de actualización.

La aplicación Android puede crear, consultar, actualizar y cancelar consultas usando estos endpoints.

---

### Creación de consultas

Cuando un paciente crea una consulta desde Android, se envía únicamente el motivo de consulta. El paciente no se identifica mediante DNI ni nombre en esta petición, sino mediante el token JWT.

Endpoint:

```http
POST /api/consultas/
```

Ejemplo de JSON recibido:

```json
{
  "motivo": "Dolor fuerte en el pecho desde hace una hora"
}
```

Cuando se crea la consulta, Django la guarda inicialmente y puede enviarla a n8n para obtener una clasificación automática. Si n8n devuelve una respuesta válida, Django actualiza la consulta con:

- `prioridad_ia`
- `categoria`
- `observaciones`
- `estado = en_espera`

Ejemplo de respuesta esperada:

```json
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
    "estado": "en_espera",
    "categoria": "Naranja",
    "prioridad_ia": 2,
    "observaciones": "Se recomienda valoración médica prioritaria.",
    "orden_manual": 0,
    "fecha_creacion": "2026-04-28T09:33:35.753639+00:00",
    "fecha_actualizacion": "2026-04-28T09:33:35.753639+00:00"
  }
}
```

---

### Control de consultas duplicadas

El backend incluye una validación para evitar que se creen consultas duplicadas recientes.

Si un paciente envía una consulta con el mismo motivo en un intervalo muy corto de tiempo y ya existe una consulta pendiente o en espera, Django devuelve la consulta existente en lugar de crear una nueva.

Esto evita duplicados causados por reintentos, problemas de conexión o pulsaciones repetidas.

---

### Actualización de consultas

El backend permite actualizar una consulta concreta mediante una petición `PUT`.

Endpoint:

```http
PUT /api/consultas/<id>/
```

Ejemplo de JSON recibido:

```json
{
  "motivo": "Dolor fuerte en el pecho y dificultad para respirar"
}
```

Cuando se modifica el motivo de una consulta, Django puede volver a enviarla a n8n para obtener una nueva clasificación automática.

Estados válidos:

```text
pendiente
en_espera
atendida
cancelada
```

La prioridad IA debe ser un número entero entre 1 y 5.

Ejemplo:

```text
prioridad_ia = 2  ->  CategoriaTriage = Naranja
```

Cada cambio de categoría queda registrado en el histórico de triaje.

---

### Cancelación de consultas

El endpoint `DELETE` no elimina físicamente la consulta de la base de datos. En su lugar, cambia su estado a `cancelada`.

Endpoint:

```http
DELETE /api/consultas/<id>/
```

Respuesta esperada:

```json
{
  "message": "Consulta cancelada correctamente",
  "consulta": {
    "id": 1,
    "estado": "cancelada"
  }
}
```

Este comportamiento permite conservar el registro de la consulta, algo importante en un sistema relacionado con el ámbito sanitario.

---

## 🤖 Integración con n8n e IA

El backend ya está integrado con n8n mediante webhook.

Flujo general:

```text
Android → Django → n8n → Agente IA → n8n → Django → Panel médico
```

Cuando se crea o modifica una consulta, Django envía a n8n un JSON con los datos necesarios:

```json
{
  "consulta_id": 1,
  "paciente_id": 1,
  "motivo_consulta": "Me duele mucho la cadera después de una caída"
}
```

n8n procesa el motivo mediante un agente de inteligencia artificial y devuelve una respuesta con la prioridad y la recomendación:

```json
{
  "prioridad_ia": 2,
  "recomendacion": "Debe acudir a urgencias para valoración de posible fractura o lesión grave."
}
```

Django valida la prioridad recibida antes de usarla. La prioridad debe ser un número entero entre 1 y 5.

Relación entre prioridad IA y categoría:

```text
prioridad_ia = 1  ->  Rojo
prioridad_ia = 2  ->  Naranja
prioridad_ia = 3  ->  Amarillo
prioridad_ia = 4  ->  Verde
prioridad_ia = 5  ->  Azul
```

Si la respuesta de n8n es válida, Django actualiza la consulta, asigna la categoría correspondiente y guarda un registro en el histórico.

Si n8n falla o no responde, la consulta no se pierde. Puede quedar creada como pendiente para que el personal médico pueda revisarla manualmente.

---

## 🖥️ Panel médico web

El backend incluye un panel médico web servido desde Django.

Endpoint:

```http
GET /api/panel/consultas/
```

El panel permite al personal sanitario:

- Ver consultas activas.
- Filtrar consultas por estado.
- Revisar el motivo de consulta.
- Ver la recomendación generada por IA.
- Ver la prioridad IA.
- Ver y modificar la categoría de triaje.
- Cambiar el orden manual de atención.
- Marcar consultas como atendidas.
- Consultar consultas pendientes, en espera, atendidas, canceladas o todas.

Por defecto, el panel muestra las consultas activas, es decir, las pendientes o en espera.

Cuando una consulta se marca como atendida, deja de aparecer en el listado principal de trabajo pendiente, pero sigue estando registrada en la base de datos y se puede consultar usando el filtro de estado.

El médico puede cambiar manualmente la categoría de una consulta. Cuando esto ocurre, Django actualiza la consulta y guarda el cambio en el histórico con origen `medico`.

---

### Actualización automática del panel

El panel médico incluye una actualización automática sencilla.

El navegador consulta periódicamente un endpoint ligero del backend para comprobar si ha habido cambios. Si detecta una versión diferente del listado, recarga la página.

Esta solución se eligió por ser más sencilla que WebSockets y suficiente para el prototipo.

---

## 🗂️ Estructura del proyecto

```text
backend-django/
├── backend/              # Configuración principal del proyecto Django
│   ├── settings.py       # Configuración global
│   ├── urls.py           # Rutas principales del proyecto
│   ├── asgi.py
│   └── wsgi.py
│
├── triaje/               # App principal del sistema
│   ├── models.py         # Modelos Paciente, Consulta, CategoriaTriage e histórico
│   ├── views.py          # Vistas y endpoints de la API y panel médico
│   ├── urls.py           # Rutas de la app triaje
│   ├── serializers.py    # Validación y conversión manual a JSON
│   ├── services.py       # Lógica de categorías e histórico
│   ├── n8n_client.py     # Cliente para comunicación con n8n
│   ├── admin.py          # Registro de modelos en Django Admin
│   ├── migrations/       # Migraciones de base de datos
│   ├── management/       # Comandos personalizados de Django
│   ├── templates/        # Plantillas HTML del panel médico
│   └── static/           # CSS y recursos estáticos del panel
│
├── db.sqlite3            # Base de datos local de desarrollo
├── manage.py             # Comando principal de Django
├── requirements.txt      # Dependencias del proyecto
└── README.md
```

---

## 🗃️ Modelos principales

### Paciente

Representa al paciente registrado en el sistema.

Campos principales:

- `user`: relación 1:1 con el usuario de Django.
- `nombre_completo`: nombre completo del paciente.
- `dni`: documento identificativo único.
- `fecha_creacion`: fecha en la que se creó el paciente.

El modelo `Paciente` está vinculado al modelo `User` de Django. De esta forma se aprovecha el sistema de autenticación propio de Django para gestionar usuarios y contraseñas, mientras que el modelo `Paciente` guarda los datos específicos del paciente.

---

### Consulta

Representa el motivo por el que un paciente acude a urgencias.

Campos principales:

- `paciente`: paciente asociado a la consulta.
- `motivo`: texto escrito por el paciente.
- `estado`: estado actual de la consulta.
- `categoria`: categoría de triaje actual asignada.
- `prioridad_ia`: prioridad numérica devuelta por la IA.
- `observaciones`: recomendación o información adicional.
- `orden_manual`: ajuste manual para el orden de atención.
- `fecha_creacion`: fecha de creación.
- `fecha_actualizacion`: última modificación.

Estados posibles:

```text
pendiente
en_espera
atendida
cancelada
```

---

### CategoriaTriage

Representa una categoría de prioridad dentro del sistema de triaje.

Campos principales:

- `nombre`: nombre de la categoría.
- `prioridad`: valor numérico asociado a la urgencia.

Categorías utilizadas:

```text
Rojo     -> prioridad 1
Naranja  -> prioridad 2
Amarillo -> prioridad 3
Verde    -> prioridad 4
Azul     -> prioridad 5
```

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

---

## 🔗 Relaciones entre modelos

### Relación 1:1

```text
User 1:1 Paciente
```

Cada usuario de Django está asociado a un único paciente, y cada paciente pertenece a un único usuario.

### Relaciones 1:N

```text
Paciente 1:N Consulta
Consulta 1:N ConsultaCategoriaTriage
CategoriaTriage 1:N ConsultaCategoriaTriage
```

Un paciente puede tener varias consultas, pero cada consulta pertenece a un único paciente.

Una consulta puede tener varios registros de histórico, y una categoría puede aparecer en el histórico de muchas consultas distintas.

### Relación N:M

La relación N:M entre `Consulta` y `CategoriaTriage` se implementa mediante el modelo intermedio `ConsultaCategoriaTriage`.

```text
Consulta N:M CategoriaTriage
```

Esto permite que una consulta pueda pasar por varias categorías a lo largo del tiempo, y que una misma categoría pueda aparecer en muchas consultas distintas.

---

## 🧠 Relación entre prioridad IA, categoría, histórico y orden manual

El sistema diferencia cuatro conceptos importantes.

### Prioridad IA

Es el valor numérico sugerido por la inteligencia artificial. Este número debe estar entre 1 y 5.

### Categoría de triaje

Es la categoría oficial asociada a esa prioridad.

```text
prioridad_ia = 2
CategoriaTriage = Naranja
```

### Histórico de categorías

Cada vez que se asigna o modifica la categoría de una consulta, el sistema registra un histórico.

Esto permite saber:

- Qué categoría tuvo la consulta.
- Qué prioridad IA se aplicó.
- Qué motivo tenía la consulta en ese momento.
- Si el cambio fue realizado por IA, sistema o médico.
- Qué usuario realizó el cambio.
- Cuándo se realizó.

### Orden manual

Es el ajuste que puede realizar el médico desde el panel web.

La ordenación principal del panel tiene en cuenta:

```text
orden_manual → prioridad_ia → fecha_creacion
```

De esta manera, el sistema puede usar la IA como ayuda inicial, pero mantiene la intervención del médico como decisión final.

---

## 🧩 Servicio de asignación de categoría

El proyecto incluye una función de servicio para asignar categorías de triaje de forma controlada.

Archivo:

```text
triaje/services.py
```

Función principal:

```text
asignar_categoria_a_consulta()
```

Esta función recibe una consulta y una prioridad IA. A partir de esa prioridad, busca la categoría de triaje correspondiente y actualiza la consulta.

Además, crea un registro en `ConsultaCategoriaTriage` para mantener el histórico de categorías.

Ejemplo:

```text
prioridad_ia = 2
consulta.prioridad_ia = 2
consulta.categoria = Naranja
```

Y se crea un histórico con:

```text
consulta
categoria = Naranja
prioridad_ia = 2
motivo_en_ese_momento
origen
usuario
observaciones
fecha_creacion
```

Esta lógica evita repetir código en distintas partes del backend y asegura que cada cambio de prioridad quede registrado correctamente.

---

## 🧰 Comando para cargar categorías de triaje

El proyecto incluye un comando personalizado para cargar las categorías oficiales de triaje.

Comando:

```bash
python manage.py seed_triage_categories
```

Este comando crea las categorías oficiales:

```text
Rojo
Naranja
Amarillo
Verde
Azul
```

Esto permite mantener siempre las mismas categorías de triaje, aunque se trabaje desde distintos ordenadores o se reinicie la base de datos local.

---

## 📄 Documentación OpenAPI / Swagger

La API REST está documentada mediante `drf-spectacular`.

Rutas de documentación:

```http
GET /api/schema/
GET /api/docs/
```

- `/api/schema/` genera el esquema OpenAPI.
- `/api/docs/` muestra la documentación visual mediante Swagger UI.

Endpoints documentados:

```http
POST   /api/auth/register/
POST   /api/auth/login/

GET    /api/consultas/
POST   /api/consultas/
GET    /api/consultas/<id>/
PUT    /api/consultas/<id>/
DELETE /api/consultas/<id>/
```

La documentación incluye:

- Métodos HTTP.
- Parámetros de ruta.
- Parámetros de query.
- Cuerpos JSON esperados.
- Respuestas posibles.
- Autenticación JWT.

---

## 🔗 Rutas principales

### Autenticación

```http
POST /api/auth/register/
POST /api/auth/login/
```

### Consultas

```http
GET    /api/consultas/
POST   /api/consultas/
GET    /api/consultas/<id>/
PUT    /api/consultas/<id>/
DELETE /api/consultas/<id>/
```

### Panel médico

```http
GET  /api/panel/consultas/
POST /api/panel/consultas/<id>/orden/
POST /api/panel/consultas/<id>/atendida/
POST /api/panel/consultas/<id>/categoria/
```

### Documentación

```http
GET /api/schema/
GET /api/docs/
```

---

## ▶️ Ejecución en local

Crear y activar el entorno virtual:

```bash
python -m venv venv
```

En Windows:

```bash
venv\Scripts\activate
```

Si el entorno virtual está una carpeta por encima del proyecto:

```powershell
..\venv\Scripts\Activate.ps1
```

Instalar dependencias:

```bash
pip install -r requirements.txt
```

Aplicar migraciones:

```bash
python manage.py migrate
```

Cargar categorías oficiales de triaje:

```bash
python manage.py seed_triage_categories
```

Crear superusuario:

```bash
python manage.py createsuperuser
```

Ejecutar servidor:

```bash
python manage.py runserver
```

Servidor local:

```text
http://127.0.0.1:8000/
```

Panel de administración:

```text
http://127.0.0.1:8000/admin/
```

Panel médico:

```text
http://127.0.0.1:8000/api/panel/consultas/
```

Swagger UI:

```text
http://127.0.0.1:8000/api/docs/
```

OpenAPI schema:

```text
http://127.0.0.1:8000/api/schema/
```

---

## ⚙️ Configuración de n8n

El backend necesita conocer la URL del webhook de n8n.

La configuración se realiza en `settings.py` o mediante variables de entorno, según el entorno de ejecución.

Variables/configuración recomendadas:

```text
N8N_TRIAGE_WEBHOOK_URL
N8N_TRIAGE_TIMEOUT_SECONDS
```

El webhook debe recibir un JSON con:

```json
{
  "consulta_id": 1,
  "paciente_id": 1,
  "motivo_consulta": "Texto del motivo"
}
```

Y debe devolver:

```json
{
  "prioridad_ia": 2,
  "recomendacion": "Texto de recomendación"
}
```

---

## 📱 Conexión con Android

Durante el desarrollo, la app Android se prueba con un emulador de Android Studio.

Desde Android no se usa:

```text
http://127.0.0.1:8000/
```

En su lugar se utiliza:

```text
http://10.0.2.2:8000/
```

Ejemplo:

```text
http://10.0.2.2:8000/api/auth/login/
```

Esto permite que el emulador Android se conecte al servidor Django que está ejecutándose en el ordenador.

En la app Android, la URL base del servidor está centralizada en la clase `ApiConfig.java`, para que no sea necesario cambiarla en varias activities si en el futuro se usa otra IP o un servidor desplegado.

---

## ✅ Pruebas realizadas

Durante el desarrollo se han probado los principales flujos del sistema:

- Registro de paciente.
- Login con JWT.
- Creación de consulta desde Android.
- Listado de consultas del paciente.
- Detalle de consulta.
- Actualización del motivo.
- Reclasificación automática con n8n.
- Cancelación lógica de consulta.
- Validación de DNI.
- Validación de motivo obligatorio.
- Prevención de duplicados recientes.
- Asignación automática de categoría.
- Registro de histórico de categorías.
- Cambio manual de categoría desde el panel médico.
- Marcado de consultas como atendidas.
- Filtro por estado en el panel médico.
- Documentación Swagger/OpenAPI.

---

## 📍 Mejoras futuras

- Preparar despliegue en servidor real.
- Sustituir SQLite por PostgreSQL.
- Configurar HTTPS.
- Gestionar variables sensibles mediante `.env`.
- Mejorar permisos y roles del panel médico.
- Añadir renovación automática de tokens JWT en Android.
- Mostrar histórico de categorías de forma más detallada en el panel médico.
- Añadir pruebas automáticas.
- Preparar despliegue con Docker.
- Sustituir polling del panel médico por WebSockets si se necesitase tiempo real más eficiente.
- Validar la clasificación IA con profesionales sanitarios.

---

## 👩‍💻 Autora

Proyecto desarrollado por **Marta Mariño Alvite** como parte del TFC del ciclo de **Desarrollo de Aplicaciones Multiplataforma**.