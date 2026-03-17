"""
utils.py - Core business logic for Eco-Logistics Planner
Handles Google Maps API calls, CO₂ calculations, Green Score, CSV export.
"""

from __future__ import annotations

import csv
import io
import logging
import math
from typing import Optional

import requests

from config import Config
from models import RoutePoint, TransportResult

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Google Maps helpers
# ---------------------------------------------------------------------------

GMAPS_DISTANCE_URL = "https://maps.googleapis.com/maps/api/distancematrix/json"
GMAPS_DIRECTIONS_URL = "https://maps.googleapis.com/maps/api/directions/json"
GMAPS_GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"


def _google_distance_matrix(
    origin: str,
    destination: str,
    api_key: str,
    mode: str = "driving",
) -> Optional[dict]:
    """
    Call Google Distance Matrix API.
    Returns dict with distance_m, duration_s or None on failure.
    mode: 'driving' | 'transit' | 'walking'
    """
    params = {
        "origins": origin,
        "destinations": destination,
        "mode": mode,
        "key": api_key,
        "language": "en",
        "units": "metric",
        "region": "in",
    }
    try:
        resp = requests.get(
            GMAPS_DISTANCE_URL,
            params=params,
            timeout=Config.MAPS_REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()

        if data.get("status") != "OK":
            logger.warning("Distance Matrix API status: %s", data.get("status"))
            return None

        element = data["rows"][0]["elements"][0]
        if element.get("status") != "OK":
            logger.warning("Element status: %s", element.get("status"))
            return None

        return {
            "distance_m": element["distance"]["value"],
            "duration_s": element["duration"]["value"],
        }
    except Exception as exc:
        logger.error("Distance Matrix API error: %s", exc)
        return None


def _google_directions(
    origin: str,
    destination: str,
    api_key: str,
    mode: str = "driving",
) -> Optional[dict]:
    """
    Call Google Directions API.
    Returns dict with polyline, origin_lat/lng, dest_lat/lng or None.
    """
    params = {
        "origin": origin,
        "destination": destination,
        "mode": mode,
        "key": api_key,
        "language": "en",
        "region": "in",
    }
    try:
        resp = requests.get(
            GMAPS_DIRECTIONS_URL,
            params=params,
            timeout=Config.MAPS_REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()

        if data.get("status") != "OK" or not data.get("routes"):
            return None

        route = data["routes"][0]
        polyline = route["overview_polyline"]["points"]
        leg = route["legs"][0]

        return {
            "polyline": polyline,
            "origin_lat": leg["start_location"]["lat"],
            "origin_lng": leg["start_location"]["lng"],
            "dest_lat": leg["end_location"]["lat"],
            "dest_lng": leg["end_location"]["lng"],
        }
    except Exception as exc:
        logger.error("Directions API error: %s", exc)
        return None


def _geocode(location: str, api_key: str) -> Optional[RoutePoint]:
    """Geocode a place name → RoutePoint."""
    params = {"address": location, "key": api_key, "region": "in"}
    try:
        resp = requests.get(
            GMAPS_GEOCODE_URL,
            params=params,
            timeout=Config.MAPS_REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") != "OK" or not data.get("results"):
            return None
        loc = data["results"][0]["geometry"]["location"]
        return RoutePoint(lat=loc["lat"], lng=loc["lng"])
    except Exception as exc:
        logger.error("Geocode error: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Haversine fallback (used when no API key)
# ---------------------------------------------------------------------------

def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate straight-line distance in km using Haversine formula."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# Major Indian city coordinates for demo fallback
INDIA_CITY_COORDS: dict[str, tuple[float, float]] = {
    "mumbai": (19.0760, 72.8777),
    "delhi": (28.6139, 77.2090),
    "new delhi": (28.6139, 77.2090),
    "bangalore": (12.9716, 77.5946),
    "bengaluru": (12.9716, 77.5946),
    "hyderabad": (17.3850, 78.4867),
    "chennai": (13.0827, 80.2707),
    "kolkata": (22.5726, 88.3639),
    "pune": (18.5204, 73.8567),
    "ahmedabad": (23.0225, 72.5714),
    "jaipur": (26.9124, 75.7873),
    "surat": (21.1702, 72.8311),
    "lucknow": (26.8467, 80.9462),
    "kanpur": (26.4499, 80.3319),
    "nagpur": (21.1458, 79.0882),
    "indore": (22.7196, 75.8577),
    "thane": (19.2183, 72.9781),
    "bhopal": (23.2599, 77.4126),
    "visakhapatnam": (17.6868, 83.2185),
    "pimpri-chinchwad": (18.6279, 73.7986),
    "patna": (25.5941, 85.1376),
    "vadodara": (22.3072, 73.1812),
    "ghaziabad": (28.6692, 77.4538),
    "ludhiana": (30.9010, 75.8573),
    "agra": (27.1767, 78.0081),
    "nashik": (20.0112, 73.7898),
    "faridabad": (28.4089, 77.3178),
    "meerut": (28.9845, 77.7064),
    "rajkot": (22.3039, 70.8022),
    "kalyan": (19.2403, 73.1305),
    "vasai-virar": (19.3919, 72.8397),
    "varanasi": (25.3176, 82.9739),
    "srinagar": (34.0837, 74.7973),
    "aurangabad": (19.8762, 75.3433),
    "dhanbad": (23.7957, 86.4304),
    "amritsar": (31.6340, 74.8723),
    "allahabad": (25.4358, 81.8463),
    "prayagraj": (25.4358, 81.8463),
    "ranchi": (23.3441, 85.3096),
    "howrah": (22.5958, 88.2636),
    "coimbatore": (11.0168, 76.9558),
    "vijayawada": (16.5062, 80.6480),
    "jodhpur": (26.2389, 73.0243),
    "madurai": (9.9252, 78.1198),
    "raipur": (21.2514, 81.6296),
    "kochi": (9.9312, 76.2673),
    "chandigarh": (30.7333, 76.7794),
    "guwahati": (26.1445, 91.7362),
    "solapur": (17.6854, 75.9044),
    "hubli": (15.3647, 75.1240),
    "mysuru": (12.2958, 76.6394),
    "tiruppur": (11.1085, 77.3411),
    "gurgaon": (28.4595, 77.0266),
    "gurugram": (28.4595, 77.0266),
    "noida": (28.5355, 77.3910),
    "tiruchirappalli": (10.7905, 78.7047),
    "bareilly": (28.3670, 79.4304),
    "aligarh": (27.8974, 78.0880),
    "moradabad": (28.8386, 78.7733),
    "jabalpur": (23.1815, 79.9864),
    "gwalior": (26.2183, 78.1828),
    "vijayawada": (16.5062, 80.6480),
    "jammu": (32.7266, 74.8570),
    "mangalore": (12.9141, 74.8560),
    "erode": (11.3410, 77.7172),
    "belgaum": (15.8497, 74.4977),
    "belagavi": (15.8497, 74.4977),
    "udaipur": (24.5854, 73.7125),
    "jamshedpur": (22.8046, 86.2029),
    "shimla": (31.1048, 77.1734),
    "dehradun": (30.3165, 78.0322),
    "pondicherry": (11.9416, 79.8083),
    "puducherry": (11.9416, 79.8083),
    "bhubaneswar": (20.2961, 85.8245),
    "cuttack": (20.4625, 85.8828),
    "thiruvananthapuram": (8.5241, 76.9366),
    "trivandrum": (8.5241, 76.9366),
    "calicut": (11.2588, 75.7804),
    "kozhikode": (11.2588, 75.7804),
}


def _fallback_coords(location: str) -> Optional[RoutePoint]:
    """Try to find coordinates from our local city dictionary."""
    key = location.lower().strip()
    # Direct match
    if key in INDIA_CITY_COORDS:
        lat, lng = INDIA_CITY_COORDS[key]
        return RoutePoint(lat=lat, lng=lng)
    # Partial match
    for city, (lat, lng) in INDIA_CITY_COORDS.items():
        if city in key or key in city:
            return RoutePoint(lat=lat, lng=lng)
    return None


# ---------------------------------------------------------------------------
# Main calculation engine
# ---------------------------------------------------------------------------

def get_route_data(
    origin: str,
    destination: str,
    api_key: str,
) -> dict:
    """
    Fetch distance/duration from Google Maps (driving mode for road,
    transit for rail/metro) and return base route data.
    Falls back to haversine + city lookup if API key absent or fails.
    Returns: {distance_km, duration_min, polyline, origin_point, dest_point}
    """
    api_available = bool(api_key)

    distance_m = None
    duration_s = None
    polyline = None
    origin_point = None
    dest_point = None

    if api_available:
        # Get real driving distance + duration
        dm_result = _google_distance_matrix(origin, destination, api_key, mode="driving")
        if dm_result:
            distance_m = dm_result["distance_m"]
            duration_s = dm_result["duration_s"]

        # Get polyline and exact coords
        dir_result = _google_directions(origin, destination, api_key, mode="driving")
        if dir_result:
            polyline = dir_result["polyline"]
            origin_point = RoutePoint(
                lat=dir_result["origin_lat"],
                lng=dir_result["origin_lng"],
            )
            dest_point = RoutePoint(
                lat=dir_result["dest_lat"],
                lng=dir_result["dest_lng"],
            )

    # Fallback: geocode from local dict + haversine
    if distance_m is None:
        logger.info("Using fallback distance calculation for %s → %s", origin, destination)

        op = None
        dp = None

        if api_available:
            op = _geocode(origin, api_key)
            dp = _geocode(destination, api_key)

        if op is None:
            op = _fallback_coords(origin)
        if dp is None:
            dp = _fallback_coords(destination)

        if op and dp:
            straight_km = _haversine_km(op.lat, op.lng, dp.lat, dp.lng)
            # Apply road-factor: ~1.35× for Indian road network
            road_km = straight_km * 1.35
            distance_m = int(road_km * 1000)
            # Estimate ~50 km/h average urban-inter-city mix
            duration_s = int(road_km / 50 * 3600)
            origin_point = op
            dest_point = dp
        else:
            # Last resort: raise so caller can return error
            raise ValueError(
                f"Could not determine distance for '{origin}' → '{destination}'. "
                "Please enter valid Indian city names or configure a Google Maps API key."
            )

    distance_km = distance_m / 1000
    duration_min = duration_s / 60

    return {
        "distance_km": distance_km,
        "duration_min": duration_min,
        "polyline": polyline,
        "origin_point": origin_point,
        "dest_point": dest_point,
    }


def get_transit_data(
    origin: str,
    destination: str,
    api_key: str,
    base_distance_km: float,
    base_duration_min: float,
) -> dict:
    """
    Attempt to get transit-specific distance/duration from Google Maps.
    Falls back to adjusted estimates based on road data.
    """
    if api_key:
        dm_result = _google_distance_matrix(origin, destination, api_key, mode="transit")
        if dm_result:
            return {
                "distance_km": dm_result["distance_m"] / 1000,
                "duration_min": dm_result["duration_s"] / 60,
            }

    # Estimate: rail/metro are more direct than roads
    return {
        "distance_km": base_distance_km * 0.92,  # Rail is ~8% more direct
        "duration_min": base_duration_min * 0.75,  # Faster due to fewer stops
    }


# ---------------------------------------------------------------------------
# Emission calculations
# ---------------------------------------------------------------------------

def calculate_co2(distance_km: float, emission_factor: float) -> float:
    """Calculate CO₂ in kg."""
    return round(distance_km * emission_factor, 3)


def calculate_fuel_energy(
    mode_key: str,
    distance_km: float,
    emission_factor: float,
) -> str:
    """Return human-readable fuel/energy consumption label."""
    if "electric" in mode_key:
        # ~14 kWh/100km for EV car, ~8 kWh/100km for e-bus
        if "car" in mode_key:
            kwh = distance_km * 0.14
        elif "bus" in mode_key:
            kwh = distance_km * 0.08
        else:
            kwh = distance_km * 0.05
        return f"Energy: {kwh:.1f} kWh"
    elif "rail" in mode_key or "metro" in mode_key:
        kwh = distance_km * emission_factor / 0.72  # reverse from grid emission factor
        return f"Electricity: {kwh:.2f} kWh/pax"
    elif "two_wheeler" in mode_key:
        litres = distance_km / 45  # ~45 km/L for 125cc
        return f"Fuel: {litres:.2f} L"
    elif "car" in mode_key:
        litres = distance_km / 15  # ~15 km/L petrol car
        return f"Fuel: {litres:.2f} L"
    elif "bus" in mode_key:
        litres = distance_km / 4.5  # bus fuel economy per km (full)
        return f"Fuel: {litres:.2f} L (shared)"
    elif "truck" in mode_key:
        litres = distance_km / 4.0
        return f"Fuel: {litres:.2f} L"
    return "N/A"


# ---------------------------------------------------------------------------
# Green Score
# ---------------------------------------------------------------------------

def calculate_green_score(
    mode_key: str,
    category: str,
    co2_kg: float,
    distance_km: float,
    duration_min: float,
    cost_inr: float,
    all_results: list[dict],
) -> float:
    """
    Compute Green Score (0-100) using weighted normalised metrics.
    Lower CO₂/distance/time/cost → higher score.
    Bonuses applied for rail, metro, electric modes.
    """
    weights = Config.GREEN_SCORE_WEIGHTS

    # Collect max values for normalisation (avoid div-by-zero)
    max_co2 = max((r["co2_kg"] for r in all_results), default=1) or 1
    max_dist = max((r["distance_km"] for r in all_results), default=1) or 1
    max_time = max((r["duration_min"] for r in all_results), default=1) or 1
    max_cost = max((r["cost_inr"] for r in all_results), default=1) or 1

    # Normalised "goodness" scores (1 = best / zero impact)
    co2_score    = 1 - (co2_kg / max_co2)
    dist_score   = 1 - (distance_km / max_dist)
    time_score   = 1 - (duration_min / max_time)
    cost_score   = 1 - (cost_inr / max_cost)

    raw = (
        weights["co2"]      * co2_score
        + weights["distance"] * dist_score
        + weights["time"]     * time_score
        + weights["cost"]     * cost_score
    )

    # Apply category bonus
    bonuses = Config.GREEN_SCORE_BONUSES
    bonus = 1.0
    if category == "metro":
        bonus = bonuses["metro"]
    elif category == "rail":
        bonus = bonuses["rail"]
    elif "electric" in mode_key:
        bonus = bonuses["electric"]

    score = raw * bonus * 100

    # Clamp to [0, 100]
    return round(max(0.0, min(100.0, score)), 1)


def calculate_trees_to_offset(co2_kg: float) -> float:
    """How many trees need to be planted for 1-year offset of co2_kg."""
    return round(co2_kg / Config.CO2_PER_TREE_KG_PER_YEAR, 2)


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------

def calculate_all_modes(
    origin: str,
    destination: str,
    api_key: str,
    selected_modes: Optional[list[str]] = None,
) -> list[TransportResult]:
    """
    Calculate eco-metrics for all (or selected) transport modes.
    Returns list of TransportResult sorted by green_score descending.
    """
    # Step 1: Get base road distance/time
    road_data = get_route_data(origin, destination, api_key)
    distance_km = road_data["distance_km"]
    duration_min = road_data["duration_min"]
    polyline = road_data.get("polyline")
    origin_point = road_data.get("origin_point")
    dest_point = road_data.get("dest_point")

    # Step 2: Get transit-specific distance/time
    transit_data = get_transit_data(
        origin, destination, api_key, distance_km, duration_min
    )

    modes = Config.TRANSPORT_MODES
    if selected_modes:
        modes = {k: v for k, v in modes.items() if k in selected_modes}

    # Step 3: Build preliminary results for normalisation
    raw_results: list[dict] = []
    for mode_key, mode_cfg in modes.items():
        cat = mode_cfg["category"]
        # Use transit distance for rail/metro
        if cat in ("rail", "metro"):
            d_km = transit_data["distance_km"]
            t_min = transit_data["duration_min"]
        else:
            # Road modes use actual road distance; adjust by avg speed
            d_km = distance_km
            # Re-estimate time based on mode speed
            t_min = (d_km / mode_cfg["avg_speed_kmh"]) * 60

        ef = Config.EMISSION_FACTORS[mode_cfg["emission_key"]]
        co2 = calculate_co2(d_km, ef)
        cost = round(d_km * mode_cfg["cost_per_km"], 2)

        raw_results.append({
            "mode_key": mode_key,
            "co2_kg": co2,
            "distance_km": d_km,
            "duration_min": t_min,
            "cost_inr": cost,
        })

    # Step 4: Calculate green scores with cross-mode normalisation
    transport_results: list[TransportResult] = []
    for raw, (mode_key, mode_cfg) in zip(raw_results, modes.items()):
        cat = mode_cfg["category"]
        d_km = raw["distance_km"]
        t_min = raw["duration_min"]
        co2 = raw["co2_kg"]
        cost = raw["cost_inr"]
        ef = Config.EMISSION_FACTORS[mode_cfg["emission_key"]]

        green_score = calculate_green_score(
            mode_key, cat, co2, d_km, t_min, cost, raw_results
        )

        trees = calculate_trees_to_offset(co2)
        fuel_label = calculate_fuel_energy(mode_key, d_km, ef)

        # Only road modes get the actual road polyline
        mode_polyline = polyline if cat == "road" else None

        transport_results.append(
            TransportResult(
                mode_key=mode_key,
                mode_name=mode_cfg["name"],
                mode_icon=mode_cfg["icon"],
                category=cat,
                color=mode_cfg["color"],
                distance_km=round(d_km, 2),
                duration_min=round(t_min, 1),
                co2_kg=co2,
                fuel_energy_label=fuel_label,
                cost_inr=cost,
                green_score=green_score,
                trees_to_offset=trees,
                polyline=mode_polyline,
                origin_point=origin_point,
                destination_point=dest_point,
            )
        )

    # Sort: highest green score first
    transport_results.sort(key=lambda r: r.green_score, reverse=True)
    return transport_results


# ---------------------------------------------------------------------------
# CSV Export
# ---------------------------------------------------------------------------

def results_to_csv(
    origin: str,
    destination: str,
    results: list[TransportResult],
) -> str:
    """Generate CSV string from transport results."""
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "Origin",
        "Destination",
        "Transport Mode",
        "Category",
        "Distance (km)",
        "Duration (min)",
        "CO₂ Emissions (kg)",
        "Fuel / Energy",
        "Cost (₹)",
        "Green Score (0-100)",
        "Trees to Offset (1 yr)",
    ])

    for r in results:
        writer.writerow([
            origin,
            destination,
            f"{r.mode_icon} {r.mode_name}",
            r.category.capitalize(),
            r.distance_km,
            round(r.duration_min, 1),
            r.co2_kg,
            r.fuel_energy_label,
            r.cost_inr,
            r.green_score,
            r.trees_to_offset,
        ])

    return output.getvalue()
