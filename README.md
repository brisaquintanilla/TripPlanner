## TripPlanner – Prototipo Flask

Este es un prototipo universitario de una aplicación de planificación de viajes construida con **Flask**. La mayor parte de la lógica residirá en Python (backend), mientras que el frontend se mantiene ligero.

### Estructura del proyecto

- `app.py`: aplicación principal de Flask y rutas.
- `templates/index.html`: plantilla base que muestra la lista de viajes.
- `static/app.js`: lógica básica del lado del cliente.
- `requirements.txt`: dependencias de Python.

### Requisitos previos

- Python 3.9+ instalado.
- (Opcional pero recomendado) uso de entorno virtual `venv`.

### Instalación

```bash
cd TripPlanner

# Crear y activar entorno virtual (macOS / Linux)
python3 -m venv .venv
source .venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### Ejecutar la aplicación

```bash
python app.py
```

Luego abre en tu navegador:

- http://127.0.0.1:5000/

Deberías ver la página de **Planificador de Viajes** con algunos viajes de ejemplo generados desde Python.

### Próximos pasos sugeridos

- Mover la lista de viajes a una clase o módulo de servicios en Python.
- Agregar formularios en HTML para crear/editar/eliminar viajes.
- Implementar validaciones y almacenamiento (por ejemplo, SQLite).
