from flask import Flask, render_template, jsonify, request
import requests

app = Flask(__name__)


@app.route("/")
def index():
    trips = [
        {"destination": "París", "days": 5},
        {"destination": "Tokio", "days": 10},
        {"destination": "Ciudad de México", "days": 3},
    ]
    return render_template("index.html", trips=trips)


@app.get("/api/cities")
def city_suggestions():
    query = (request.args.get("q") or "").strip()
    if len(query) < 2:
        return jsonify([])

    try:
        response = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={
                "q": query,
                "format": "json",
                "addressdetails": 1,
                "limit": 7,
            },
            headers={
                # Cambia el email de contacto por uno válido antes de producción
                "User-Agent": "TripPlannerUniversityPrototype/1.0 (contact: change_this@example.com)",
            },
            timeout=5,
        )
        response.raise_for_status()
        results = response.json()
    except requests.RequestException:
        return jsonify([]), 502

    suggestions = []
    for item in results:
        address = item.get("address", {})
        city = (
            address.get("city")
            or address.get("town")
            or address.get("village")
            or address.get("hamlet")
        )
        country = address.get("country")
        if not city or not country:
            continue

        label = f"{city}, {country}"
        suggestions.append(
            {
                "label": label,
                "city": city,
                "country": country,
                "lat": item.get("lat"),
                "lon": item.get("lon"),
            }
        )

    return jsonify(suggestions)


if __name__ == "__main__":
    app.run(debug=True)
