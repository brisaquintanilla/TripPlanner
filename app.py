from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from datetime import datetime
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import os
import random
import unicodedata
import requests
from tripplanner.data import (
    ACTIVITIES_DB,
    LOCAL_CITY_FALLBACKS,
    INTERESTS_DEF,
    FEATURED_DESTINATIONS,
)

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Needed for flash messages

# Initialize Geocoder
geolocator = Nominatim(user_agent="trip_planner_app")
TELEPORT_SEARCH_URL = "https://api.teleport.org/api/cities/"


def normalize_text(text):
    normalized = unicodedata.normalize('NFKD', text or '')
    stripped = ''.join(char for char in normalized if not unicodedata.combining(char))
    return stripped.lower().strip()


def fetch_cities(query, limit=5):
    if not query:
        return []

    # Usamos la versión sin acentos para mejorar resultados
    normalized_query = normalize_text(query)
    params = {"search": normalized_query, "limit": limit}
    try:
        response = requests.get(TELEPORT_SEARCH_URL, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        results = data.get("_embedded", {}).get("city:search-results", [])
        suggestions = []
        for result in results:
            full_name = result.get("matching_full_name")
            if full_name and full_name not in suggestions:
                suggestions.append(full_name)
        return suggestions
    except requests.RequestException:
        return []


# Datos movidos a tripplanner.data (ACTIVITIES_DB)

# Datos movidos a tripplanner.data (LOCAL_CITY_FALLBACKS)

# Datos movidos a tripplanner.data (INTERESTS_DEF)

# Datos movidos a tripplanner.data (FEATURED_DESTINATIONS)

def pick_featured(count=6):
    pool = FEATURED_DESTINATIONS[:]
    random.shuffle(pool)
    return pool[: min(count, len(pool))]

def validate_destination(destination):
    search_term = (destination or "").strip()
    normalized_search = normalize_text(search_term)
    matches = fetch_cities(search_term, limit=7)

    for match in matches:
        if normalized_search and normalized_search in normalize_text(match):
            return True, match

    if matches:
        # Return first suggestion if no close match but results exist
        return True, matches[0]

    # Intentar coincidir con la base de datos local
    for city in LOCAL_CITY_FALLBACKS:
        if normalized_search and normalized_search in normalize_text(city):
            return True, city

    try:
        location = geolocator.geocode(destination)
        if location:
            return True, location.address
    except (GeocoderTimedOut, GeocoderServiceError):
        pass  # Si el servicio externo falla, seguimos con fallback local

    # Fallback final: aceptar cualquier texto no vacío como destino válido
    if search_term:
        return True, search_term
    return False, None

@app.route('/')
def index():
    # Render inicial con el backend (menos JS/HTML en templates)
    initial_featured = pick_featured()
    return render_template('index.html', featured_destinations=initial_featured)

@app.route('/search_city')
def search_city():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])
    # Primero sugerencias locales (muy rápidas): preferimos coincidencias por prefijo
    normalized_query = normalize_text(query)
    prefix_matches = [city for city in LOCAL_CITY_FALLBACKS if normalized_query and normalize_text(city).startswith(normalized_query)]
    substring_matches = [city for city in LOCAL_CITY_FALLBACKS if normalized_query and (normalized_query in normalize_text(city)) and city not in prefix_matches]
    local_matches = prefix_matches + substring_matches

    # Si encontramos cualquier coincidencia local, devolverla inmediatamente para máxima velocidad
    if local_matches:
        return jsonify(local_matches[:10])

    # Intentar Teleport (más preciso) y si falla usar geocoding
    suggestions = fetch_cities(query, limit=7)
    if suggestions:
        return jsonify(suggestions)

    try:
        locations = geolocator.geocode(query, exactly_one=False, limit=5)
        if locations:
            return jsonify([loc.address for loc in locations])
    except (GeocoderTimedOut, GeocoderServiceError):
        pass

    # Fallback final: vacío si no encontramos nada
    return jsonify([])

@app.route('/plan', methods=['POST'])
def plan():
    destination = request.form.get('destination')
    start_date_str = request.form.get('start_date')
    end_date_str = request.form.get('end_date')

    if not destination or not start_date_str or not end_date_str:
        flash("Por favor completa todos los campos.", "error")
        return redirect(url_for('index'))

    # Date Validation
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        today = datetime.now().date()

        if start_date < today:
            flash("La fecha de inicio no puede ser en el pasado.", "error")
            return redirect(url_for('index'))
        
        if end_date < start_date:
            flash("La fecha de fin no puede ser anterior a la fecha de inicio.", "error")
            return redirect(url_for('index'))

    except ValueError:
        flash("Formato de fecha inválido.", "error")
        return redirect(url_for('index'))

    # Destination Validation
    is_valid_dest, address = validate_destination(destination)
    if not is_valid_dest:
        flash(f"No pudimos encontrar el destino '{destination}'. Por favor intenta con otro.", "error")
        return redirect(url_for('index'))

    # Store in session
    session['destination'] = address
    session['start_date'] = start_date_str
    session['end_date'] = end_date_str
    
    return redirect(url_for('interests'))

@app.route('/interests', methods=['GET', 'POST'])
def interests():
    if 'destination' not in session:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        selected_interests = request.form.getlist('interests')
        if not selected_interests:
            flash("Selecciona al menos un interés.", "error")
            return redirect(url_for('interests'))

        if len(selected_interests) > 3:
            flash("Elige máximo 3 intereses para mantener tu viaje enfocado. También añadiremos wildcards.", "error")
            return redirect(url_for('interests'))
        
        session['interests'] = selected_interests
        return redirect(url_for('swipe'))
        
    return render_template('interests.html', destination=session['destination'], interests_def=INTERESTS_DEF)

@app.route('/swipe')
def swipe():
    if not all(k in session for k in ('interests', 'start_date', 'end_date', 'destination')):
        return redirect(url_for('index'))
    start_date = datetime.strptime(session['start_date'], '%Y-%m-%d').date()
    end_date = datetime.strptime(session['end_date'], '%Y-%m-%d').date()
    duration = (end_date - start_date).days + 1
    min_activities = 3 * duration
    return render_template('swipe.html', destination=session['destination'], duration=duration, min_activities=min_activities)

@app.route('/get_activities')
def get_activities():
    if 'interests' not in session:
        return jsonify([])
    
    user_interests = session['interests']
    main_pool = []
    
    # Actividades según intereses del usuario
    for interest in user_interests:
        if interest in ACTIVITIES_DB:
            for activity in ACTIVITIES_DB[interest]:
                activity_copy = activity.copy()
                activity_copy['category'] = interest
                activity_copy['wildcard'] = False
                main_pool.append(activity_copy)

    # Wildcards: sugerencias fuera de sus intereses
    wildcard_pool = []
    other_categories = [c for c in ACTIVITIES_DB.keys() if c not in user_interests]
    for category in other_categories:
        for activity in ACTIVITIES_DB[category]:
            activity_copy = activity.copy()
            activity_copy['category'] = category
            activity_copy['wildcard'] = True
            wildcard_pool.append(activity_copy)

    random.shuffle(main_pool)
    random.shuffle(wildcard_pool)

    # Mezclamos algunas wildcards (máx 30% del total previsto)
    max_wildcards = max(1, len(main_pool) // 3) if main_pool else len(wildcard_pool)
    selected_wildcards = wildcard_pool[:max_wildcards]

    combined = main_pool + selected_wildcards
    random.shuffle(combined)
    return jsonify(combined)

@app.route('/finalize_itinerary', methods=['POST'])
def finalize_itinerary():
    data = request.get_json(silent=True) or {}
    liked_activities = data.get('liked_activities', [])
    
    if not liked_activities:
        # Fallback if user swiped left on everything
        liked_activities = [{"title": "Exploración libre de la ciudad", "icon": "fa-map", "category": "paseo"}]

    start_date = datetime.strptime(session['start_date'], '%Y-%m-%d').date()
    end_date = datetime.strptime(session['end_date'], '%Y-%m-%d').date()
    duration = (end_date - start_date).days + 1
    
    # Garantizar entre 3 y 4 actividades por día
    total_min = 3 * duration

    # Si el usuario eligió muy pocas, rellenamos repitiendo actividades
    if len(liked_activities) < total_min:
        base = liked_activities[:]  # copia
        idx = 0
        while len(liked_activities) < total_min and base:
            liked_activities.append(base[idx % len(base)])
            idx += 1

    # Distribuir 3-4 actividades por día
    itinerary = []
    base_per_day = 3
    total_for_base = base_per_day * duration
    remaining = max(0, len(liked_activities) - total_for_base)
    extra_days = min(duration, remaining)  # días que tendrán 4 actividades

    current_idx = 0
    for day in range(1, duration + 1):
        count = base_per_day + (1 if day <= extra_days else 0)
        day_activities = liked_activities[current_idx: current_idx + count]
        current_idx += count

        # Si por alguna razón no hay suficientes, agregamos genéricas
        if len(day_activities) < 3:
            while len(day_activities) < 3:
                day_activities.append({
                    "title": "Tiempo libre para explorar",
                    "icon": "fa-compass",
                    "category": "general",
                })

        itinerary.append({
            "day": day,
            "activities": day_activities
        })

    # Guardamos el itinerario en sesión y devolvemos URL de redirección
    session['itinerary'] = itinerary

    return jsonify({"redirect": url_for('itinerary_view')})


@app.route('/itinerary')
def itinerary_view():
    if not all(k in session for k in ("destination", "start_date", "end_date", "itinerary")):
        return redirect(url_for('index'))

    start_date = datetime.strptime(session['start_date'], '%Y-%m-%d').date()
    end_date = datetime.strptime(session['end_date'], '%Y-%m-%d').date()
    itinerary = session['itinerary']

    # Construir botones de búsqueda en mapas según intereses seleccionados
    interests = session.get('interests', [])
    dest = session.get('destination', '')

    mapping = {
        'comida': {'label': 'Ver restaurantes en mapa', 'query': f'restaurantes en {dest}', 'icon': 'fa-utensils', 'color': 'rose'},
        'cafes': {'label': 'Ver cafés en mapa', 'query': f'cafés en {dest}', 'icon': 'fa-mug-saucer', 'color': 'emerald'},
        'arte': {'label': 'Ver arte en mapa', 'query': f'galerías de arte en {dest}', 'icon': 'fa-palette', 'color': 'indigo'},
        'paseo': {'label': 'Ver sitios históricos en mapa', 'query': f'sitios históricos en {dest}', 'icon': 'fa-landmark', 'color': 'amber'},
        'vistas': {'label': 'Ver miradores en mapa', 'query': f'miradores en {dest}', 'icon': 'fa-binoculars', 'color': 'sky'},
        'museos': {'label': 'Ver museos en mapa', 'query': f'museos en {dest}', 'icon': 'fa-landmark', 'color': 'indigo'},
        'aventura': {'label': 'Ver actividades al aire libre', 'query': f'actividades al aire libre en {dest}', 'icon': 'fa-mountain', 'color': 'lime'},
        'nocturna': {'label': 'Ver rooftops y bares', 'query': f'rooftops y bares en {dest}', 'icon': 'fa-moon', 'color': 'violet'},
        'compras': {'label': 'Ver mercados y tiendas', 'query': f'mercados y tiendas en {dest}', 'icon': 'fa-shopping-bag', 'color': 'fuchsia'},
        'playa': {'label': 'Ver playas', 'query': f'playas en {dest}', 'icon': 'fa-umbrella-beach', 'color': 'cyan'},
        'bienestar': {'label': 'Ver spas y bienestar', 'query': f'spas y centros de bienestar en {dest}', 'icon': 'fa-leaf', 'color': 'emerald'},
    }

    map_buttons = []
    # Añadir botones únicos en el orden de intereses seleccionados
    seen = set()
    for it in interests:
        if it in mapping and it not in seen:
            seen.add(it)
            entry = mapping[it].copy()
            entry['query'] = mapping[it]['query']
            map_buttons.append(entry)

    # Fallback: si no hay intereses, mantener los botones anteriores por defecto
    if not map_buttons:
        map_buttons = [
            mapping['cafes'], mapping['comida'], mapping['museos'], mapping['vistas']
        ]

    return render_template(
        'itinerary.html',
        destination=session['destination'],
        start_date=start_date,
        end_date=end_date,
        itinerary=itinerary,
        map_buttons=map_buttons,
    )

@app.route('/itinerary/print')
def itinerary_print():
    if not all(k in session for k in ("destination", "start_date", "end_date", "itinerary")):
        return redirect(url_for('index'))

    start_date = datetime.strptime(session['start_date'], '%Y-%m-%d').date()
    end_date = datetime.strptime(session['end_date'], '%Y-%m-%d').date()
    itinerary = session['itinerary']

    return render_template(
        'itinerary_print.html',
        destination=session['destination'],
        start_date=start_date,
        end_date=end_date,
        itinerary=itinerary,
    )

@app.route('/api/featured')
def api_featured():
    return jsonify(pick_featured())

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, port=port)
