from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from datetime import datetime
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import os
import random
import unicodedata
import requests

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


# Mock Database of Activities
ACTIVITIES_DB = {
    "comida": [
        {"title": "Tour de comida callejera", "icon": "fa-utensils", "image": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=800&q=80"},
        {"title": "Cena en restaurante local", "icon": "fa-utensils", "image": "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=800&q=80"},
        {"title": "Clase de cocina tradicional", "icon": "fa-utensils", "image": "https://images.unsplash.com/photo-1525351484163-7529414344d8?auto=format&fit=crop&w=1200&q=80"},
        {"title": "Mercado gastronómico", "icon": "fa-utensils", "image": "https://images.unsplash.com/photo-1533777857889-4be7c70b33f7?auto=format&fit=crop&w=800&q=80"}
    ],
    "arte": [
        {"title": "Museo de Arte Moderno", "icon": "fa-palette", "image": "https://www.moma.org/assets/visit/entrance-image--museum-crop-7516b01003659172f2d9dbc7a6c2e9d9.jpg"},
        {"title": "Galería de arte contemporáneo", "icon": "fa-palette", "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b4/Alte_Nationalgalerie_abends_%28Zuschnitt%29.jpg/1200px-Alte_Nationalgalerie_abends_%28Zuschnitt%29.jpg"},
        {"title": "Tour de Street Art", "icon": "fa-spray-can", "image": "https://bogota.gov.co/sites/default/files/styles/1050px/public/eventos/2024-06/distrito-grafiti-bienvenidos.png"},
        {"title": "Teatro Histórico", "icon": "fa-masks-theater", "image": "https://images.adsttc.com/media/images/5899/d0b6/e58e/cead/d600/0167/newsletter/CC0_Public_Domain_opera-594592.jpg?1486475429"}
    ],
    "paseo": [
        {"title": "Caminata por el centro histórico", "icon": "fa-person-walking", "image": "https://images.unsplash.com/photo-1505761671935-60b3a7427bad?auto=format&fit=crop&w=800&q=80"},
        {"title": "Paseo en bicicleta", "icon": "fa-bicycle", "image": "https://images.prismic.io/peopleforbikes/aa9565ca-37cf-4116-98d8-9cfef0d78744_bigger-street-1024x768.jpg?auto=compress,format"},
        {"title": "Jardín Botánico", "icon": "fa-leaf", "image": "https://images.unsplash.com/photo-1466692476868-aef1dfb1e735?auto=format&fit=crop&w=800&q=80"},
        {"title": "Parque Central", "icon": "fa-tree", "image": "https://images.unsplash.com/photo-1496347646636-ea47f7d6b37b?auto=format&fit=crop&w=800&q=80"}
    ],
    "vistas": [
        {"title": "Mirador Panorámico", "icon": "fa-binoculars", "image": "https://images.unsplash.com/photo-1506953823976-52e1fdc0149a?auto=format&fit=crop&w=800&q=80"},
        {"title": "Atardecer en la playa/río", "icon": "fa-sun", "image": "https://images.unsplash.com/photo-1472120435266-53107fd0c44a?auto=format&fit=crop&w=800&q=80"},
        {"title": "Torre de observación", "icon": "fa-tower-observation", "image": "https://images.unsplash.com/photo-1486325212027-8081e485255e?auto=format&fit=crop&w=800&q=80"}
    ],
    "cafes": [
        {"title": "Cafetería Histórica", "icon": "fa-mug-hot", "image": "https://images.unsplash.com/photo-1509042239860-f550ce710b93?auto=format&fit=crop&w=800&q=80"},
        {"title": "Cata de café", "icon": "fa-mug-saucer", "image": "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?auto=format&fit=crop&w=800&q=80"},
        {"title": "Brunch con vista", "icon": "fa-utensils", "image": "https://images.unsplash.com/photo-1504754524776-8f4f37790ca0?auto=format&fit=crop&w=1200&q=80"}
    ],
    "museos": [
        {"title": "Museo de Historia", "icon": "fa-landmark", "image": "https://images.unsplash.com/photo-1566127444979-b3d2b654e3d7?auto=format&fit=crop&w=800&q=80"},
        {"title": "Museo de Ciencias", "icon": "fa-flask", "image": "https://images.unsplash.com/photo-1532094349884-543bc11b234d?auto=format&fit=crop&w=800&q=80"},
        {"title": "Planetario", "icon": "fa-star", "image": "https://images.unsplash.com/photo-1444703686981-a3abbc4d4fe3?auto=format&fit=crop&w=800&q=80"}
    ],
    "aventura": [
        {"title": "Trekking a mirador", "icon": "fa-mountain", "image": "https://bogota.gov.co/sites/default/files/2022-08/la-aguadora.jpg"},
        {"title": "Tour en kayak", "icon": "fa-water", "image": "https://media-cdn.tripadvisor.com/media/attractions-splice-spp-674x446/0b/25/fe/ab.jpg"},
        {"title": "Ruta en globo aerostático", "icon": "fa-location-arrow", "image": "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1200&q=80"}
    ],
    "nocturna": [
        {"title": "Bar de cocteles de autor", "icon": "fa-champagne-glasses", "image": "https://media.ooka.com/media/magefan_blog/dubaiatnight.jpg"},
        {"title": "Club de jazz íntimo", "icon": "fa-music", "image": "https://images.unsplash.com/photo-1511379938547-c1f69419868d?auto=format&fit=crop&w=800&q=80"},
        {"title": "Noche de rooftop con vista", "icon": "fa-moon", "image": "https://images.unsplash.com/photo-1477959858617-67f85cf4f1df?auto=format&fit=crop&w=800&q=80"}
    ],
    "compras": [
        {"title": "Mercado de diseño local", "icon": "fa-shopping-bag", "image": "https://byfood.b-cdn.net/api/public/assets/9299/content"},
        {"title": "Barrio de boutiques", "icon": "fa-tag", "image": "https://images.unsplash.com/photo-1441986300917-64674bd600d8?auto=format&fit=crop&w=800&q=80"},
        {"title": "Outlet de marcas", "icon": "fa-store", "image": "https://images.unsplash.com/photo-1523475472560-d2df97ec485c?auto=format&fit=crop&w=800&q=80"}
    ],
    "playa": [
        {"title": "Día de playa y snorkel", "icon": "fa-umbrella-beach", "image": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=800&q=80"},
        {"title": "Paseo en velero al atardecer", "icon": "fa-ship", "image": "https://images.unsplash.com/photo-1500375592092-40eb2168fd21?auto=format&fit=crop&w=800&q=80"},
        {"title": "Clase de surf para principiantes", "icon": "fa-person-swimming", "image": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=800&q=80"}
    ],
    "bienestar": [
        {"title": "Sesión de spa y sauna", "icon": "fa-leaf", "image": "https://images.unsplash.com/photo-1515377905703-c4788e51af15?auto=format&fit=crop&w=800&q=80"},
        {"title": "Clase de yoga al amanecer", "icon": "fa-heart", "image": "https://images.unsplash.com/photo-1506126613408-eca07ce68773?auto=format&fit=crop&w=800&q=80"},
        {"title": "Baños termales naturales", "icon": "fa-water", "image": "https://images.unsplash.com/photo-1468413253725-0d5181091126?auto=format&fit=crop&w=800&q=80"}
    ]
}

# Pequeña base de datos local de ciudades para autocompletar y fallback
LOCAL_CITY_FALLBACKS = [
    # América del Norte
    "Nueva York, Estados Unidos",
    "Los Ángeles, Estados Unidos",
    "San Francisco, Estados Unidos",
    "Chicago, Estados Unidos",
    "Miami, Estados Unidos",
    "Nueva Orleans, Estados Unidos",
    "Toronto, Canadá",
    "Vancouver, Canadá",
    "Montreal, Canadá",
    "Ciudad de México, México",
    "Guadalajara, México",
    "Monterrey, México",

    # América del Sur
    "Buenos Aires, Argentina",
    "Córdoba, Argentina",
    "Rosario, Argentina",
    "Santiago, Chile",
    "Valparaíso, Chile",
    "Lima, Perú",
    "Cusco, Perú",
    "La Paz, Bolivia",
    "São Paulo, Brasil",
    "Río de Janeiro, Brasil",
    "Brasilia, Brasil",
    "Bogotá, Colombia",
    "Medellín, Colombia",
    "Quito, Ecuador",

    # Europa Occidental
    "Londres, Reino Unido",
    "Manchester, Reino Unido",
    "Edimburgo, Reino Unido",
    "Dublín, Irlanda",
    "París, Francia",
    "Lyon, Francia",
    "Marsella, Francia",
    "Madrid, España",
    "Barcelona, España",
    "Valencia, España",
    "Sevilla, España",
    "Lisboa, Portugal",
    "Oporto, Portugal",
    "Ámsterdam, Países Bajos",
    "Bruselas, Bélgica",
    "Ginebra, Suiza",
    "Zúrich, Suiza",

    # Europa Central y del Este
    "Berlín, Alemania",
    "Múnich, Alemania",
    "Hamburgo, Alemania",
    "Viena, Austria",
    "Praga, República Checa",
    "Budapest, Hungría",
    "Varsovia, Polonia",
    "Cracovia, Polonia",
    "Atenas, Grecia",
    "Santorini, Grecia",
    "Dubrovnik, Croacia",

    # Asia
    "Tokio, Japón",
    "Kioto, Japón",
    "Osaka, Japón",
    "Seúl, Corea del Sur",
    "Busan, Corea del Sur",
    "Pekín, China",
    "Shanghái, China",
    "Hong Kong, China",
    "Singapur, Singapur",
    "Bangkok, Tailandia",
    "Chiang Mai, Tailandia",
    "Hanoi, Vietnam",
    "Ciudad Ho Chi Minh, Vietnam",
    "Nueva Delhi, India",
    "Mumbai, India",
    "Jaipur, India",
    "Bali, Indonesia",
    "Dubái, Emiratos Árabes Unidos",

    # Oceanía y otros
    "Sídney, Australia",
    "Melbourne, Australia",
    "Brisbane, Australia",
    "Auckland, Nueva Zelanda",
    "Queenstown, Nueva Zelanda",

    # América del Norte adicionales
    "Boston, Estados Unidos",
    "Filadelfia, Estados Unidos",
    "Washington D. C., Estados Unidos",
    "Atlanta, Estados Unidos",
    "Dallas, Estados Unidos",
    "Houston, Estados Unidos",
    "Austin, Estados Unidos",
    "Denver, Estados Unidos",
    "Seattle, Estados Unidos",
    "Portland, Estados Unidos",
    "Phoenix, Estados Unidos",
    "San Diego, Estados Unidos",
    "Las Vegas, Estados Unidos",
    "Orlando, Estados Unidos",
    "Tampa, Estados Unidos",
    "Salt Lake City, Estados Unidos",
    "San Antonio, Estados Unidos",
    "Baltimore, Estados Unidos",
    "Detroit, Estados Unidos",
    "Cleveland, Estados Unidos",
    "Pittsburgh, Estados Unidos",
    "Charlotte, Estados Unidos",
    "Nashville, Estados Unidos",
    "Memphis, Estados Unidos",
    "Minneapolis, Estados Unidos",
    "Kansas City, Estados Unidos",
    "Saint Louis, Estados Unidos",
    "Albuquerque, Estados Unidos",
    "Santa Fe, Estados Unidos",
    "Boise, Estados Unidos",
    "Anchorage, Estados Unidos",
    "Honolulu, Estados Unidos",
    "Kahului, Estados Unidos",
    "Lihue, Estados Unidos",
    "Quebec, Canadá",
    "Ottawa, Canadá",
    "Calgary, Canadá",
    "Edmonton, Canadá",
    "Winnipeg, Canadá",
    "Halifax, Canadá",
    "Cancún, México",
    "Tijuana, México",
    "Puebla, México",
    "Mérida, México",
    "Oaxaca, México",
    "San Luis Potosí, México",
    "Toluca, México",
    "San José, Costa Rica",
    "Panamá, Panamá",
    "Santo Domingo, República Dominicana",
    "San Juan, Puerto Rico",
    "La Habana, Cuba",
    "Kingston, Jamaica",
    "Nassau, Bahamas",

    # América del Sur adicionales
    "Montevideo, Uruguay",
    "Punta del Este, Uruguay",
    "Asunción, Paraguay",
    "Cartagena, Colombia",
    "Barranquilla, Colombia",
    "Cali, Colombia",
    "Guayaquil, Ecuador",
    "Cuenca, Ecuador",
    "Arequipa, Perú",
    "Iquitos, Perú",
    "Manaos, Brasil",
    "Salvador, Brasil",
    "Fortaleza, Brasil",
    "Recife, Brasil",
    "Belo Horizonte, Brasil",
    "Curitiba, Brasil",
    "Porto Alegre, Brasil",
    "Florianópolis, Brasil",

    # Europa Occidental adicionales
    "Florencia, Italia",
    "Nápoles, Italia",
    "Milán, Italia",
    "Turín, Italia",
    "Bolonia, Italia",
    "Pisa, Italia",
    "Venecia, Italia",
    "Verona, Italia",
    "Niza, Francia",
    "Cannes, Francia",
    "Burdeos, Francia",
    "Toulouse, Francia",
    "Lille, Francia",
    "Estrasburgo, Francia",
    "Frankfurt, Alemania",
    "Colonia, Alemania",
    "Düsseldorf, Alemania",
    "Stuttgart, Alemania",
    "Núremberg, Alemania",
    "Dresde, Alemania",
    "Leipzig, Alemania",
    "Copenhague, Dinamarca",
    "Oslo, Noruega",
    "Bergen, Noruega",
    "Estocolmo, Suecia",
    "Gotemburgo, Suecia",
    "Helsinki, Finlandia",
    "Tallin, Estonia",
    "Riga, Letonia",
    "Vilna, Lituania",
    "Bucarest, Rumanía",
    "Sofía, Bulgaria",
    "Belgrado, Serbia",
    "Sarajevo, Bosnia y Herzegovina",
    "Skopje, Macedonia del Norte",
    "Liubliana, Eslovenia",
    "Zagreb, Croacia",
    "Zadar, Croacia",
    "Split, Croacia",

    # Turquía y Eurasia
    "Estambul, Turquía",
    "Ankara, Turquía",
    "Antalya, Turquía",
    "Esmirna, Turquía",
    "Göreme, Turquía",
    "Tiflis, Georgia",
    "Ereván, Armenia",
    "Bakú, Azerbaiyán",

    # Oriente Medio y África
    "Tel Aviv, Israel",
    "Jerusalén, Israel",
    "Amán, Jordania",
    "Doha, Catar",
    "Kuwait, Kuwait",
    "Mascate, Omán",
    "Marrakech, Marruecos",
    "Casablanca, Marruecos",
    "El Cairo, Egipto",
    "Luxor, Egipto",
    "Nairobi, Kenia",
    "Kampala, Uganda",
    "Addis Abeba, Etiopía",
    "Dar es Salaam, Tanzania",
    "Ciudad del Cabo, Sudáfrica",
    "Johannesburgo, Sudáfrica",
    "Dakar, Senegal",
    "Accra, Ghana",

    # Asia adicionales
    "Taipéi, Taiwán",
    "Kaohsiung, Taiwán",
    "Taichung, Taiwán",
    "Manila, Filipinas",
    "Cebú, Filipinas",
    "Kuala Lumpur, Malasia",
    "Penang, Malasia",
    "Malaca, Malasia",
    "Phnom Penh, Camboya",
    "Siem Riep, Camboya",
    "Vientián, Laos",
    "Luang Prabang, Laos",
    "Yangón, Birmania",
    "Mandalay, Birmania",
    "Katmandú, Nepal",
    "Pokhara, Nepal",
    "Colombo, Sri Lanka",
    "Malé, Maldivas",
    "Almaty, Kazajistán",
    "Astana, Kazajistán",
    "Taskent, Uzbekistán",
    "Samarcanda, Uzbekistán",
    "Biskek, Kirguistán",
    "Ulán Bator, Mongolia",
    "Islamabad, Pakistán",
    "Lahore, Pakistán",
    "Karachi, Pakistán",
    "Daca, Bangladés",
    "Chittagong, Bangladés",

    # Oceanía adicionales
    "Wellington, Nueva Zelanda",
    "Christchurch, Nueva Zelanda",
    "Gold Coast, Australia",
    "Perth, Australia",
    "Adelaida, Australia",
    "Hobart, Australia",
    "Darwin, Australia",
    "Cairns, Australia",
    "Suva, Fiyi",
    "Papeete, Polinesia Francesa",
]

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
    return render_template('index.html')

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
        
    return render_template('interests.html', destination=session['destination'])

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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, port=port)
