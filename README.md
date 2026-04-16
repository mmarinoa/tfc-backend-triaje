# 🏥 TFC Backend Triaje

Backend del proyecto de **triaje sanitario en urgencias**, desarrollado con **Django** como parte del TFC de Desarrollo de Aplicaciones Multiplataforma.

Este backend se encarga de:

- registrar pacientes
- almacenar consultas médicas
- exponer una API REST propia
- servir de base para la priorización por triaje
- centralizar los datos que consumirá la app Android y, si se implementa, el panel del médico

---

## 🚀 Tecnologías utilizadas

- **Python**
- **Django**
- **SQLite**
- **Git / GitHub**

---

## 📌 Estado actual del proyecto

Actualmente el backend permite:

- gestión de pacientes
- gestión de consultas
- modelo de categorías de triaje
- panel de administración con Django Admin
- endpoints REST básicos
- pruebas con datos reales en local

---

## 🗂️ Estructura del proyecto

```bash
backend-django/
├── backend/         # Configuración principal del proyecto Django
├── triaje/          # App principal del sistema
├── db.sqlite3       # Base de datos local
├── manage.py        # Comando principal de Django
├── requirements.txt # Dependencias del proyecto
└── README.md
