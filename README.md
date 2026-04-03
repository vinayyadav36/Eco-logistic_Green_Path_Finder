# 🌿 Eco-Logistics Green Path Finder

A **production-ready, full-stack** web application for eco-friendly route planning across India.  
Enter any two Indian cities and get real-time CO₂ emissions, cost, travel time, and an AI-powered **Green Score** for 8 transport modes.

---

## ✨ Features

| Feature | Details |
|---------|---------|
| 🗺️ **Real Route Data** | Google Maps Distance Matrix + Directions API (with haversine fallback) |
| 🚗🚆🚇 **8 Transport Modes** | Car (Petrol/Electric/CNG), Bus (Diesel/Electric), Express Train, Suburban Rail, Metro, Two-Wheeler |
| 💨 **CO₂ Emissions** | India 2026 well-to-wheel factors (MoRTH/IPCC AR6/CEEW) |
| 🌿 **AI Green Score** | Weighted (CO₂ 40%, time 20%, cost 25%, distance 15%) + rail/metro/EV bonuses |
| 🌳 **Carbon Offset** | Trees-to-plant calculator (21 kg CO₂/tree/year) |
| 📊 **Plotly Charts** | CO₂ bar, Green Score bar, Travel Time bar, Cost vs CO₂ scatter |
| 🗺️ **Interactive Map** | Leaflet.js with real route polyline + origin/destination markers |
| 📥 **CSV Export** | One-click download with all metrics |
| 📱 **Responsive UI** | Mobile-first, green-themed CSS |
| 🏥 **Health Check** | `GET /health` endpoint for monitoring |
| 🔒 **Production Ready** | Gunicorn-compatible, .env support, structured logging |

---

## 📁 Project Structure

```
eco-logistics-planner/
├── app.py              # Flask application (routes, factory)
├── models.py           # Data models (RouteRequest, TransportResult, etc.)
├── utils.py            # Google Maps integration, CO₂ calc, Green Score, CSV
├── config.py           # All emission factors, weights, transport modes
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variables template
├── Procfile            # Gunicorn deployment (Render/Heroku)
├── templates/
│   └── index.html      # Full responsive HTML SPA
├── static/
│   ├── style.css       # Modern green-themed CSS
│   ├── script.js       # Frontend JS (map, form, results)
│   └── charts.js       # Plotly chart rendering
└── README.md
```

---

## 🚀 Quick Start (Local)

### 1. Clone & install

```bash
git clone https://github.com/vinayyadav36/Eco-logistic_Green_Path_Finder.git
cd Eco-logistic_Green_Path_Finder
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and add your Google Maps API key
```

### 3. Run development server

```bash
python app.py
# → http://localhost:5000
```

### 4. Run with Gunicorn (production)

```bash
gunicorn app:app --workers 2 --bind 0.0.0.0:5000
```

---

## 🔑 Google Maps API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Create a new project (or select existing)
3. Enable these APIs:
   - **Distance Matrix API**
   - **Directions API**
   - **Geocoding API**
4. Create an API key → restrict to your server IP
5. Add to `.env`:  
   ```
   GOOGLE_MAPS_API_KEY=AIzaSy...
   ```

> **Without an API key**, the app uses a haversine-based fallback with a built-in city coordinate database covering 70+ major Indian cities. All features still work — distances will be approximate.

---

## 🌐 Deploy on Render (One-Click)

1. Fork this repo
2. Create a new **Web Service** on [Render](https://render.com)
3. Connect your GitHub repo
4. Settings:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app --workers 2 --bind 0.0.0.0:$PORT`
5. Add environment variables in Render dashboard:
   - `GOOGLE_MAPS_API_KEY` = your key
   - `SECRET_KEY` = random 32-char string
   - `FLASK_ENV` = `production`
6. Deploy! 🎉

---

## 🔧 Configuration

All emission factors, costs, and scoring weights are in `config.py`:

```python
# Change CO₂ emission factors (kg CO₂/km)
EMISSION_FACTORS = {
    "car_petrol":    0.195,
    "car_electric":  0.085,
    "metro":         0.008,
    # ...
}

# Change Green Score weights (must sum to 1.0)
GREEN_SCORE_WEIGHTS = {
    "co2":      0.40,
    "distance": 0.15,
    "time":     0.20,
    "cost":     0.25,
}
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Main application UI |
| POST | `/api/calculate` | Calculate eco-metrics for all modes |
| POST | `/api/export/csv` | Download results as CSV |
| GET | `/health` | Health check |

### POST `/api/calculate`

**Request:**
```json
{ "origin": "Mumbai", "destination": "Pune", "modes": [] }
```

**Response:**
```json
{
  "origin": "Mumbai",
  "destination": "Pune",
  "best_mode_key": "metro",
  "total_modes": 8,
  "results": [
    {
      "mode_key": "metro",
      "mode_name": "Metro Rail",
      "co2_kg": 0.593,
      "green_score": 87.3,
      "cost_inr": 148.0,
      "duration_min": 127,
      "trees_to_offset": 0.028,
      ...
    }
  ]
}
```

---

## 🌱 Emission Factors (India 2026)

| Mode | kg CO₂/km | Source |
|------|-----------|--------|
| Car (Petrol) | 0.195 | MoRTH + IPCC AR6 WTW |
| Car (Electric) | 0.085 | India grid ~0.72 kgCO₂/kWh |
| Bus (Diesel) | 0.055 | Per passenger, 60-pax full |
| Bus (Electric) | 0.025 | Per passenger |
| Express Train | 0.014 | Indian Railways electric traction |
| Suburban Rail | 0.010 | AC EMU |
| **Metro** | **0.008** | Fully electric |
| Two-Wheeler | 0.070 | 125cc petrol avg |

---

## 📜 License

MIT License — see [LICENSE](LICENSE)

---

*Built with ❤️ for a greener India 🇮🇳*