"""
config.py - Central configuration for Eco-Logistics Planner
All emission factors, cost rates, scoring weights, and app settings.
Based on India 2026 real-world values (well-to-wheel where noted).
"""

import os


class Config:
    # ---------------------------------------------------------------------------
    # Flask core
    # ---------------------------------------------------------------------------
    SECRET_KEY: str = os.getenv("SECRET_KEY", "eco-logistics-dev-secret-2026")
    DEBUG: bool = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    TESTING: bool = False

    # ---------------------------------------------------------------------------
    # Google Maps API
    # ---------------------------------------------------------------------------
    GOOGLE_MAPS_API_KEY: str = os.getenv("GOOGLE_MAPS_API_KEY", "")
    MAPS_REQUEST_TIMEOUT: int = 10  # seconds

    # ---------------------------------------------------------------------------
    # CO₂ Emission Factors  (kg CO₂ per km per vehicle, India 2026)
    # Source: MoRTH, IPCC AR6, CEEW India transport sector analysis
    # ---------------------------------------------------------------------------
    EMISSION_FACTORS: dict = {
        # Well-to-wheel (WTW) for fuels; includes upstream extraction/refining
        "car_petrol":    0.195,   # kg CO₂/km  (average sedan, WTW)
        "car_diesel":    0.175,   # kg CO₂/km  (average sedan, WTW)
        "car_electric":  0.085,   # kg CO₂/km  (India grid avg 2026 ~0.72 kgCO2/kWh; 14 kWh/100km)
        "car_cng":       0.155,   # kg CO₂/km
        "bus_diesel":    0.055,   # kg CO₂/km per passenger (60-pax full)
        "bus_electric":  0.025,   # kg CO₂/km per passenger
        "rail_express":  0.014,   # kg CO₂/km per passenger (Indian Railways electric traction)
        "rail_suburban": 0.010,   # kg CO₂/km per passenger (AC EMU)
        "metro":         0.008,   # kg CO₂/km per passenger (fully electric)
        "two_wheeler_petrol": 0.070,  # kg CO₂/km (125cc avg)
        "two_wheeler_electric": 0.035,  # kg CO₂/km
        "truck_diesel":  0.900,   # kg CO₂/km (heavy freight 15-20 t)
    }

    # ---------------------------------------------------------------------------
    # Transport modes shown to users
    # Each mode: display name, emission factor key, speed (km/h), base cost
    # ---------------------------------------------------------------------------
    TRANSPORT_MODES: dict = {
        "car_petrol": {
            "name": "Car (Petrol)",
            "icon": "🚗",
            "emission_key": "car_petrol",
            "avg_speed_kmh": 50,
            "cost_per_km": 6.5,   # ₹/km (fuel + depreciation)
            "category": "road",
            "color": "#ef4444",
        },
        "car_electric": {
            "name": "Car (Electric)",
            "icon": "⚡",
            "emission_key": "car_electric",
            "avg_speed_kmh": 55,
            "cost_per_km": 2.2,   # ₹/km (electricity ~₹7/kWh, 14 kWh/100km)
            "category": "road",
            "color": "#f59e0b",
        },
        "bus_diesel": {
            "name": "Bus (Diesel)",
            "icon": "🚌",
            "emission_key": "bus_diesel",
            "avg_speed_kmh": 45,
            "cost_per_km": 1.2,   # ₹/km per passenger (MSRTC avg)
            "category": "road",
            "color": "#8b5cf6",
        },
        "bus_electric": {
            "name": "Bus (Electric)",
            "icon": "🔋",
            "emission_key": "bus_electric",
            "avg_speed_kmh": 45,
            "cost_per_km": 0.9,
            "category": "road",
            "color": "#06b6d4",
        },
        "rail_express": {
            "name": "Express Train",
            "icon": "🚆",
            "emission_key": "rail_express",
            "avg_speed_kmh": 80,
            "cost_per_km": 0.7,   # ₹/km (sleeper class avg Indian Railways)
            "category": "rail",
            "color": "#10b981",
        },
        "rail_suburban": {
            "name": "Suburban Rail",
            "icon": "🚉",
            "emission_key": "rail_suburban",
            "avg_speed_kmh": 60,
            "cost_per_km": 0.5,
            "category": "rail",
            "color": "#3b82f6",
        },
        "metro": {
            "name": "Metro Rail",
            "icon": "🚇",
            "emission_key": "metro",
            "avg_speed_kmh": 35,
            "cost_per_km": 2.0,   # ₹/km (Delhi/Mumbai metro avg)
            "category": "metro",
            "color": "#22c55e",
        },
        "two_wheeler_petrol": {
            "name": "Two-Wheeler (Petrol)",
            "icon": "🏍️",
            "emission_key": "two_wheeler_petrol",
            "avg_speed_kmh": 45,
            "cost_per_km": 2.5,
            "category": "road",
            "color": "#f97316",
        },
    }

    # ---------------------------------------------------------------------------
    # Green Score weights (must sum to 1.0)
    # ---------------------------------------------------------------------------
    GREEN_SCORE_WEIGHTS: dict = {
        "co2":      0.40,   # CO₂ contribution dominates
        "distance": 0.15,   # Shorter is greener
        "time":     0.20,   # Faster = less idling = greener
        "cost":     0.25,   # Proxy for efficiency
    }

    # Bonus multipliers for eco-friendly categories
    GREEN_SCORE_BONUSES: dict = {
        "metro":     1.30,   # 30% bonus for metro
        "rail":      1.25,   # 25% bonus for rail
        "electric":  1.15,   # 15% bonus for electric vehicles
    }

    # ---------------------------------------------------------------------------
    # Carbon offset
    # ---------------------------------------------------------------------------
    # Average tropical tree sequesters ~21 kg CO₂/year
    CO2_PER_TREE_KG_PER_YEAR: float = 21.0

    # ---------------------------------------------------------------------------
    # CSV Export
    # ---------------------------------------------------------------------------
    CSV_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"

    # ---------------------------------------------------------------------------
    # Logging
    # ---------------------------------------------------------------------------
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False


# Active config selector
config_by_env = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
