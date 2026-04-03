"""
models.py - Data models for Eco-Logistics Planner
Pure Python dataclasses (no ORM needed for this stateless API).
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class RoutePoint:
    """Represents a geographic point on the route."""
    lat: float
    lng: float


@dataclass
class TransportResult:
    """
    Holds the complete eco-analysis result for a single transport mode.
    All distances in km, times in minutes, costs in INR (₹), CO₂ in kg.
    """
    mode_key: str           # Internal mode identifier
    mode_name: str          # Human-friendly name (e.g. "Express Train")
    mode_icon: str          # Emoji icon
    category: str           # road | rail | metro
    color: str              # Hex colour for charts

    # Route data
    distance_km: float
    duration_min: float

    # Eco metrics
    co2_kg: float
    fuel_energy_label: str   # "Fuel: X L" or "Energy: X kWh" or "Electricity: X kWh"
    cost_inr: float
    green_score: float       # 0–100

    # Offset
    trees_to_offset: float   # Trees needed for 1-year offset

    # Polyline (Google encoded polyline, road modes only)
    polyline: Optional[str] = None

    # Origin / destination (lat/lng for Leaflet markers)
    origin_point: Optional[RoutePoint] = None
    destination_point: Optional[RoutePoint] = None

    def to_dict(self) -> dict:
        d = asdict(self)
        return d


@dataclass
class RouteRequest:
    """Validated incoming request parameters."""
    origin: str
    destination: str
    modes: list[str] = field(default_factory=list)  # selected mode keys; empty = all

    def __post_init__(self):
        self.origin = self.origin.strip()
        self.destination = self.destination.strip()
        if not self.origin:
            raise ValueError("Origin location is required.")
        if not self.destination:
            raise ValueError("Destination location is required.")
        if self.origin.lower() == self.destination.lower():
            raise ValueError("Origin and destination must be different.")


@dataclass
class RouteResponse:
    """API response wrapper for the calculate endpoint."""
    origin: str
    destination: str
    results: list[TransportResult]
    best_mode_key: str        # Mode with highest green score
    total_modes: int

    def to_dict(self) -> dict:
        return {
            "origin": self.origin,
            "destination": self.destination,
            "results": [r.to_dict() for r in self.results],
            "best_mode_key": self.best_mode_key,
            "total_modes": self.total_modes,
        }
