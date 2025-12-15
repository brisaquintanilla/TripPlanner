TripPlanner

![Python](https://img.shields.io/badge/Python-3.10%2B-blue) ![Flask](https://img.shields.io/badge/Flask-2.x-lightgrey) ![Status](https://img.shields.io/badge/Status-Activo-success)

## Descripción
- Genera itinerarios de viaje rápidos a partir de un destino y fechas. Elige hasta 3 intereses y desliza tarjetas para curar actividades. Incluye un buscador de ciudades optimizado, UI moderna con Tailwind, y un itinerario final en formato línea de tiempo vertical.


## Características
- Plan en 3 pasos: destino/fechas → intereses → swipe de actividades.
- Itinerario final con 3–4 actividades por día, con botones rápidos para búsquedas en Google Maps.
- Wildcards: mezcla sugerida fuera de tus intereses para descubrir más.
- UI con Tailwind CDN y Font Awesome; animaciones suaves y diseño responsive.
 - Impresión/Exportación: vista de impresión lista para "Guardar como PDF" desde el navegador.

## Requisitos
- Python 3.10+ (recomendado)
- macOS / Linux / Windows

## Dependencias principales
- Flask, requests, geopy

## Instalación
```zsh
# Crear entorno virtual
python -m venv .venv
source .venv/bin/activate  # en macOS/Linux

# Instalar dependencias
pip install flask requests geopy
```

## Ejecución
```zsh
# Opción 1: Puerto por defecto 5000
python app.py

# Opción 2: Puerto custom (ej. 5001) con venv
PORT=5001 .venv/bin/python app.py
```

## Ejecutar desde GitHub
```zsh
# 1) Clonar el repo
git clone https://github.com/brisaquintanilla/TripPlanner.git
cd TripPlanner

# 2) Crear y activar entorno virtual
python -m venv .venv
source .venv/bin/activate  # macOS/Linux

# 3) Instalar dependencias
pip install flask requests geopy

# 4) Ejecutar (si 5000/5001 están ocupados, usa 5002)
.venv/bin/python app.py              # puerto 5000
PORT=5002 .venv/bin/python app.py   # puerto alterno

# 5) Abrir en el navegador
# http://localhost:5000   (o el puerto usado)
```

Sugerencias de solución de problemas
- Si ves "Address already in use": prueba `PORT=5002` o libera el puerto con `lsof -nP -iTCP:<puerto>` y cierra el proceso.
- Si ves `Exit Code: 127`: asegúrate de usar `.venv/bin/python` o activar el venv.
- En Windows, usa `venv\Scripts\activate` y ejecuta `python app.py`.

## Uso
1) En la portada, ingresa destino y fechas. El autocompletado responde rápido con coincidencias locales. Al enviar, verás un spinner indicando carga.
2) Selecciona hasta 3 intereses (comida, museos, arte, aventura, etc.).
3) Desliza tarjetas (drag/swipe) para “like”/“nope”.
4) Genera el itinerario en formato vertical con miniaturas circulares laterales. Abre búsquedas en mapas con un clic.
5) Para guardar como PDF: desde el itinerario, abre la vista de impresión (`/itinerary/print`), presiona Cmd/Ctrl+P y elige "Guardar como PDF".


## Enlaces útiles
- Flask: https://flask.palletsprojects.com/
- Tailwind CSS: https://tailwindcss.com/docs/installation/play-cdn
- Font Awesome: https://fontawesome.com/docs/web/setup/hosted
- Teleport API (Cities): https://developers.teleport.org/api/
- Nominatim (OpenStreetMap): https://nominatim.org/release-docs/latest/

## Optimización de lenguajes (GitHub)
- Para que el proyecto aparezca predominantemente en Python en GitHub, se incluye `.gitattributes` marcando `templates/**` y `static/**` como `linguist-vendored`. Esto excluye HTML/CSS/JS y assets del cómputo de lenguajes, elevando el porcentaje de Python sin cambiar la funcionalidad.

## Comandos útiles (git)
```zsh
# Agregar cambios, commitear y hacer push a main 
git add .
git commit -m "UI polish: hero centrado, navbar, spinner; timeline vertical; búsqueda local-first; imágenes actualizadas"
git push origin main
```

## Licencia
- Uso educativo/demostrativo. Si compartes públicamente, agrega un archivo `LICENSE` (por ejemplo MIT) o enlaza a la licencia correspondiente.

