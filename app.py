"""
app.py - Flask application entry point for Eco-Logistics Planner
Production-ready: structured logging, health check, CORS-safe, Gunicorn-compatible.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone

from flask import (
    Flask,
    jsonify,
    make_response,
    render_template,
    request,
)
from dotenv import load_dotenv

# Load .env before importing config/utils
load_dotenv()

from config import Config, config_by_env
from models import RouteRequest, RouteResponse
from utils import calculate_all_modes, results_to_csv

# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

def create_app(env: str = "default") -> Flask:
    app = Flask(__name__)
    cfg = config_by_env.get(env, config_by_env["default"])
    app.config.from_object(cfg)

    # Logging
    log_level = getattr(logging, cfg.LOG_LEVEL.upper(), logging.INFO)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logger = logging.getLogger(__name__)
    logger.info("Eco-Logistics Planner starting (env=%s)", env)

    # -------------------------------------------------------------------------
    # Routes
    # -------------------------------------------------------------------------

    @app.route("/", methods=["GET"])
    def index():
        """Serve the main SPA page."""
        api_key_set = bool(app.config.get("GOOGLE_MAPS_API_KEY"))
        return render_template("index.html", api_key_set=api_key_set)

    @app.route("/api/calculate", methods=["POST"])
    def calculate():
        """
        POST /api/calculate
        Body (JSON): { "origin": str, "destination": str, "modes": [str] }
        Returns: RouteResponse JSON
        """
        logger = logging.getLogger("app.calculate")
        data = request.get_json(force=True, silent=True) or {}

        try:
            route_req = RouteRequest(
                origin=data.get("origin", ""),
                destination=data.get("destination", ""),
                modes=data.get("modes", []),
            )
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

        api_key = app.config.get("GOOGLE_MAPS_API_KEY", "")
        logger.info(
            "Calculate request: %s → %s (modes=%s)",
            route_req.origin,
            route_req.destination,
            route_req.modes or "all",
        )

        try:
            results = calculate_all_modes(
                origin=route_req.origin,
                destination=route_req.destination,
                api_key=api_key,
                selected_modes=route_req.modes or None,
            )
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 422
        except Exception as exc:
            logger.exception("Unexpected error during calculation")
            return jsonify({"error": "Internal server error. Please try again."}), 500

        best_mode = results[0].mode_key if results else ""
        response = RouteResponse(
            origin=route_req.origin,
            destination=route_req.destination,
            results=results,
            best_mode_key=best_mode,
            total_modes=len(results),
        )
        return jsonify(response.to_dict())

    @app.route("/api/export/csv", methods=["POST"])
    def export_csv():
        """
        POST /api/export/csv
        Same body as /api/calculate — returns CSV file download.
        """
        logger = logging.getLogger("app.export")
        data = request.get_json(force=True, silent=True) or {}

        try:
            route_req = RouteRequest(
                origin=data.get("origin", ""),
                destination=data.get("destination", ""),
                modes=data.get("modes", []),
            )
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

        api_key = app.config.get("GOOGLE_MAPS_API_KEY", "")

        try:
            results = calculate_all_modes(
                origin=route_req.origin,
                destination=route_req.destination,
                api_key=api_key,
                selected_modes=route_req.modes or None,
            )
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 422
        except Exception:
            logger.exception("Error generating CSV")
            return jsonify({"error": "Could not generate CSV."}), 500

        csv_content = results_to_csv(route_req.origin, route_req.destination, results)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"eco_logistics_{timestamp}.csv"

        response = make_response(csv_content)
        response.headers["Content-Type"] = "text/csv; charset=utf-8"
        response.headers["Content-Disposition"] = f"attachment; filename={filename}"
        logger.info("CSV exported: %s rows, file=%s", len(results), filename)
        return response

    @app.route("/health", methods=["GET"])
    def health():
        """Health check endpoint for load balancers / uptime monitors."""
        return jsonify({
            "status": "ok",
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "app": "Eco-Logistics Planner",
            "version": "1.0.0",
            "google_maps_configured": bool(app.config.get("GOOGLE_MAPS_API_KEY")),
        })

    @app.errorhandler(404)
    def not_found(exc):
        return jsonify({"error": "Endpoint not found."}), 404

    @app.errorhandler(405)
    def method_not_allowed(exc):
        return jsonify({"error": "Method not allowed."}), 405

    @app.errorhandler(500)
    def internal_error(exc):
        logging.getLogger("app").exception("Unhandled 500 error")
        return jsonify({"error": "Internal server error."}), 500

    return app


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

app = create_app(os.getenv("FLASK_ENV", "production"))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=app.config["DEBUG"])
