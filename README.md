# 🏥 TFC Backend Triaje

Backend del proyecto **Sistema de triaje inteligente para urgencias**, desarrollado con **Django** como parte del TFC del ciclo de **Desarrollo de Aplicaciones Multiplataforma**.

Este backend actúa como servidor central del sistema. Se encarga de recibir las peticiones de la aplicación Android, gestionar los pacientes, guardar las consultas médicas y servir la información necesaria para el panel médico.

La idea final del proyecto es que las consultas enviadas por los pacientes puedan ser clasificadas mediante un flujo de **n8n** conectado a un agente de inteligencia artificial, para ayudar a ordenar los pacientes según prioridad de triaje.

---

## 🚀 Tecnologías utilizadas

- **Python**
- **Django**
- **SQLite**
- **HTML**
- **CSS**
- **Git / GitHub**
- **n8n** *(previsto para la integración con IA)*

---

## 📌 Estado actual del proyecto

Actualmente el backend permite:

- Registro de pacientes desde la app Android.
- Login de pacientes desde la app Android.
- Validación de usuarios existentes.
- Validación de contraseña incorrecta.
- Relación entre el modelo `Paciente` y el usuario de Django.
- Gestión de pacientes.
- Gestión básica de consultas.
- Modelo de categorías de triaje.
- Panel de administración con Django Admin.
- Panel web básico para el médico.
- Endpoints REST propios para registro, login y consultas.
- Conversión manual de objetos Django a JSON mediante serializadores propios.
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
      "dni": "12345678A",
      "email": "marta@test.com",
      "password": "123456"
    }

Respuesta esperada:

    {
      "message": "Usuario registrado correctamente",
      "paciente": {
        "id": 1,
        "nombre_completo": "Marta Garcia",
        "dni": "12345678A",
        "email": "marta@test.com",
        "fecha_registro": "2026-04-28T09:33:35.753639+00:00"
      }
    }

---

### Login de pacientes

El backend comprueba si el usuario existe y si la contraseña es correcta.

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
      "paciente": {
        "id": 1,
        "nombre_completo": "Marta Garcia",
        "dni": "12345678A",
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

Actualmente el modelo de consulta ya está preparado para guardar:

- Paciente asociado.
- Motivo de consulta.
- Estado.
- Categoría de triaje.
- Prioridad devuelta por IA.
- Observaciones.
- Orden manual.
- Fecha de creación.
- Fecha de actualización.

La conexión del envío de consultas desde Android está prevista como uno de los siguientes pasos.

---

### Panel médico

El backend incluye una vista web básica para que el personal médico pueda consultar las consultas registradas.

Endpoint:

    GET /api/panel/consultas/

La idea final es que este panel muestre las consultas ordenadas por prioridad de triaje, para facilitar al médico la revisión de los pacientes pendientes.

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
    │   ├── models.py         # Modelos Paciente, Consulta y CategoriaTriage
    │   ├── views.py          # Vistas y endpoints de la API
    │   ├── urls.py           # Rutas de la app triaje
    │   ├── serializers.py    # Validación y conversión manual a JSON
    │   ├── admin.py          # Registro de modelos en Django Admin
    │   ├── migrations/       # Migraciones de base de datos
    │   └── templates/        # Plantillas HTML del panel médico
    │
    ├── db.sqlite3            # Base de datos local de desarrollo
    ├── manage.py             # Comando principal de Django
    ├── requirements.txt      # Dependencias del proyecto
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

---

### Consulta

Representa el motivo por el que un paciente acude a urgencias.

Campos principales:

- `paciente`: paciente asociado a la consulta.
- `motivo`: texto escrito por el paciente.
- `categoria`: categoría de triaje asignada.
- `estado`: estado actual de la consulta.
- `prioridad_ia`: prioridad devuelta por la IA.
- `observaciones`: información adicional o resumen.
- `orden_manual`: ajuste manual para el orden de atención.
- `fecha_creacion`: fecha de creación.
- `fecha_actualizacion`: última modificación.

---

### CategoriaTriage

Representa una categoría de prioridad dentro del sistema de triaje.

Campos principales:

- `nombre`: nombre de la categoría.
- `prioridad`: valor numérico para ordenar la urgencia.

Ejemplo previsto:

    Rojo     -> prioridad 1
    Naranja  -> prioridad 2
    Amarillo -> prioridad 3
    Verde    -> prioridad 4
    Azul     -> prioridad 5

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

Instalar dependencias:

    pip install -r requirements.txt

Aplicar migraciones:

    python manage.py migrate

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

---

## 🤖 Integración prevista con n8n e IA

En una fase posterior, Django enviará a n8n el motivo de consulta del paciente.

Flujo previsto:

    Android --> Django --> n8n --> Agente de IA --> Clasificación de triaje --> Django

La IA devolverá una categoría o prioridad, y Django actualizará la consulta para que el médico pueda verla ordenada en el panel web.

---

## 📍 Próximos pasos

- Conectar el envío de consultas desde Android.
- Crear pantalla Android para ver el estado de la consulta.
- Permitir modificar o cancelar una consulta desde la app.
- Integrar Django con n8n mediante webhook.
- Clasificar consultas mediante IA.
- Mejorar el panel médico para mostrar consultas ordenadas por prioridad.
- Añadir documentación OpenAPI de la API REST.
- Preparar despliegue futuro con una base de datos más robusta.

---

## 👩‍💻 Autora

Proyecto desarrollado por **Marta Mariño Alvite** como parte del TFC del ciclo de **Desarrollo de Aplicaciones Multiplataforma**.
