"""
================================================================================
SlopeShield: Intelligent Landslide Risk & Safe Route System
REST API Server & Frontend Connection Bridge (Member 3: Frontend Integration)
Author: Anshika Gaur (Member 3)
================================================================================

This module connects SlopeShield backend output with Member 4's presentation layer:
- Provides a zero-dependency HTTP REST API built using standard library http.server.
- Enables CORS for local web browsers and Leaflet map clients.
- Serves static assets for the official Leaflet frontend (index.html, app.js, style.css).
- Exposes dynamic query endpoints (/api/locations, /api/roads, /api/route, /api/routes, /api/weather/status, /api/weather/refresh, /api/simulate).
- Provides an embedded testing dashboard on /dashboard.
"""

import os
import json
import mimetypes
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, Any, Optional

from backend.service import SlopeShieldBackend


class SlopeShieldApiHandler(BaseHTTPRequestHandler):
    """HTTP Request Handler routing REST API endpoints to SlopeShieldBackend."""

    backend: Optional[SlopeShieldBackend] = None
    frontend_dir: Optional[str] = None

    def _set_headers(self, status: int = 200, content_type: str = "application/json"):
        self.send_response(status)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_OPTIONS(self):
        """Handle CORS pre-flight requests."""
        self._set_headers(200)

    def do_GET(self):
        """Route GET requests to API endpoints or static frontend files."""
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query_params = urllib.parse.parse_qs(parsed_url.query)

        if not self.backend:
            self._send_json(500, {"error": "Backend service not initialized"})
            return

        try:
            if path == "/api/health":
                weather_status = self.backend.get_weather_status()
                response = {
                    "status": "healthy",
                    "system": "SlopeShield Intelligent Safe Route System",
                    "author": "The Debug Divas (Integration: Anshika Gaur - Member 3)",
                    "locations_count": len(self.backend.locations),
                    "roads_count": len(self.backend.roads),
                    "weather_status": weather_status
                }
                self._send_json(200, response)

            elif path == "/api/weather/status":
                status = self.backend.get_weather_status()
                self._send_json(200, status)

            elif path == "/api/weather/refresh":
                mode = query_params.get("mode", ["mock"])[0].lower()
                api_key = query_params.get("api_key", [None])[0]
                res = self.backend.refresh_weather_and_scores(mode=mode, api_key=api_key)
                self._send_json(200, res)

            elif path == "/api/locations":
                locs = self.backend.get_locations_summary()
                self._send_json(200, {"locations": locs})

            elif path == "/api/roads":
                roads = self.backend.get_roads_summary()
                self._send_json(200, {"roads": roads})

            elif path == "/api/routes":
                payload = self.backend.plan_all_standard_corridors()
                self._send_json(200, payload)

            elif path == "/api/route":
                source = query_params.get("source", ["RISH"])[0].upper()
                dest = query_params.get("dest", ["BADR"])[0].upper()

                if source not in self.backend.locations or dest not in self.backend.locations:
                    self._send_json(400, {
                        "error": f"Invalid location: source '{source}' or destination '{dest}' not recognized.",
                        "valid_locations": list(self.backend.locations.keys())
                    })
                    return

                comparison = self.backend.compare_route(source, dest)
                self._send_json(200, comparison.to_dict())

            elif path == "/api/simulate":
                ov_type = query_params.get("override_type", ["NODE"])[0].upper()
                target = query_params.get("target", ["RUDR"])[0].upper()
                try:
                    score = float(query_params.get("score", [77.08])[0])
                except ValueError:
                    self._send_json(400, {"error": "Invalid score parameter, must be a float."})
                    return
                level = query_params.get("level", ["Critical"])[0]

                res = self.backend.simulate_hazard(ov_type, target, score, level)
                self._send_json(200, res)

            elif path == "/api/simulate/reset":
                self.backend.reset_hazards()
                self._send_json(200, {"status": "hazards_reset_to_baseline"})

            elif path == "/dashboard":
                self._serve_embedded_dashboard()

            # Static asset serving for Member 4's frontend
            elif path in ["/", "/index.html"]:
                self._serve_static_file("index.html", "text/html")

            elif path in ["/app.js", "/frontend/app.js"]:
                self._serve_static_file("app.js", "application/javascript")

            elif path in ["/style.css", "/frontend/style.css"]:
                self._serve_static_file("style.css", "text/css")

            elif path in ["/data/route_output.json", "/frontend/data/route_output.json"]:
                data_path = os.path.join(self.backend.data_manager.base_dir, "data", "route_output.json")
                if os.path.exists(data_path):
                    with open(data_path, "rb") as f:
                        self._set_headers(200, "application/json")
                        self.wfile.write(f.read())
                else:
                    self._send_json(404, {"error": "data/route_output.json not found"})

            else:
                self._send_json(404, {"error": f"Endpoint '{path}' not found."})

        except Exception as ex:
            self._send_json(500, {"error": f"Internal Server Error: {str(ex)}"})

    def do_POST(self):
        """Route POST requests for route calculation, weather refresh, and simulations."""
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        if not self.backend:
            self._send_json(500, {"error": "Backend service not initialized"})
            return

        content_length = int(self.headers.get("Content-Length", 0))
        body_bytes = self.rfile.read(content_length) if content_length > 0 else b"{}"

        try:
            body = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
        except json.JSONDecodeError:
            self._send_json(400, {"error": "Invalid JSON request body"})
            return

        try:
            if path == "/api/route":
                source = body.get("source", "RISH").upper()
                dest = body.get("dest", "BADR").upper()
                if source not in self.backend.locations or dest not in self.backend.locations:
                    self._send_json(400, {
                        "error": f"Invalid location: source '{source}' or destination '{dest}' not recognized.",
                        "valid_locations": list(self.backend.locations.keys())
                    })
                    return
                comparison = self.backend.compare_route(source, dest)
                self._send_json(200, comparison.to_dict())

            elif path == "/api/simulate":
                ov_type = body.get("override_type", "NODE").upper()
                target = body.get("target", "RUDR").upper()
                score = float(body.get("score", 77.08))
                level = body.get("level", "Critical")

                res = self.backend.simulate_hazard(ov_type, target, score, level)
                self._send_json(200, res)

            elif path == "/api/simulate/reset":
                self.backend.reset_hazards()
                self._send_json(200, {"status": "hazards_reset_to_baseline"})

            elif path == "/api/weather/refresh":
                mode = body.get("mode")
                if mode is None:
                    # check boolean use_mock
                    use_mock = body.get("use_mock", True)
                    mode = "mock" if use_mock else "live"
                api_key = body.get("api_key")
                res = self.backend.refresh_weather_and_scores(mode=mode, api_key=api_key)
                self._send_json(200, res)

            else:
                self._send_json(404, {"error": f"POST endpoint '{path}' not found."})

        except Exception as ex:
            self._send_json(500, {"error": f"Internal Server Error: {str(ex)}"})

    def _serve_static_file(self, filename: str, content_type: str):
        """Serves a static file from frontend/ directory."""
        base_dir = self.backend.data_manager.base_dir if self.backend else os.path.dirname(os.path.dirname(__file__))
        file_path = os.path.join(base_dir, "frontend", filename)

        if not os.path.exists(file_path):
            self._send_json(404, {"error": f"File {filename} not found at {file_path}"})
            return

        try:
            with open(file_path, "rb") as f:
                content = f.read()
            self._set_headers(200, content_type)
            self.wfile.write(content)
        except Exception as e:
            self._send_json(500, {"error": f"Error reading file: {str(e)}"})

    def _send_json(self, status: int, data: Dict[str, Any]):
        self._set_headers(status, "application/json")
        self.wfile.write(json.dumps(data, indent=2).encode("utf-8"))

    def _serve_embedded_dashboard(self):
        """Serves a clean HTML test dashboard to verify frontend-backend communication."""
        html = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>SlopeShield — Safe Route Engine Dashboard</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 0; padding: 0; background: #0f172a; color: #f8fafc; }
    header { background: #1e293b; padding: 16px 24px; border-bottom: 1px solid #334155; display: flex; justify-content: space-between; align-items: center; }
    h1 { margin: 0; font-size: 20px; font-weight: 600; color: #38bdf8; }
    .status-badge { background: #059669; color: white; padding: 4px 10px; border-radius: 9999px; font-size: 12px; font-weight: bold; }
    .container { display: flex; height: calc(100vh - 65px); }
    #sidebar { width: 420px; background: #1e293b; padding: 20px; overflow-y: auto; border-right: 1px solid #334155; box-sizing: border-box; }
    #map { flex: 1; height: 100%; background: #020617; }
    .card { background: #0f172a; border: 1px solid #334155; border-radius: 8px; padding: 16px; margin-bottom: 16px; }
    h3 { margin-top: 0; margin-bottom: 12px; font-size: 15px; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.5px; }
    label { display: block; font-size: 13px; color: #cbd5e1; margin-bottom: 6px; }
    select, button { width: 100%; padding: 10px; border-radius: 6px; border: 1px solid #475569; background: #334155; color: white; font-size: 14px; margin-bottom: 12px; box-sizing: border-box; }
    button { background: #0284c7; font-weight: 600; cursor: pointer; border: none; transition: 0.2s; }
    button:hover { background: #0369a1; }
    .btn-secondary { background: #475569; margin-top: 4px; }
    .btn-secondary:hover { background: #334155; }
    .result-box { background: #1e293b; border-left: 4px solid #38bdf8; padding: 12px; font-size: 13px; line-height: 1.5; border-radius: 4px; }
    .pill { display: inline-block; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 11px; }
    .pill-Critical { background: #dc2626; color: white; }
    .pill-High { background: #ea580c; color: white; }
    .pill-Moderate { background: #ca8a04; color: white; }
    .pill-Low { background: #16a34a; color: white; }
  </style>
</head>
<body>
  <header>
    <div>
      <h1>SlopeShield: Intelligent Landslide Risk & Safe Route System</h1>
      <small style="color: #94a3b8;">Char Dham Yatra & Emergency Corridors (Member 3 API Integration)</small>
    </div>
    <div class="status-badge" id="api-status">API Connected</div>
  </header>
  <div class="container">
    <div id="sidebar">
      <div class="card">
        <h3>Route Planning</h3>
        <label>Origin:</label>
        <select id="sel-src">
          <option value="RISH" selected>RISH - Rishikesh (Gateway)</option>
          <option value="DEHR">DEHR - Dehradun</option>
          <option value="MUSS">MUSS - Mussoorie</option>
          <option value="RUDR">RUDR - Rudraprayag</option>
          <option value="UKHI">UKHI - Ukhimath</option>
          <option value="KEDN">KEDN - Kedarnath Shrine</option>
          <option value="CHAM">CHAM - Chamoli</option>
          <option value="BADR">BADR - Badrinath Shrine</option>
          <option value="UTTK">UTTK - Uttarkashi</option>
          <option value="GANG">GANG - Gangotri Shrine</option>
          <option value="MALP">MALP - Malpa (Border)</option>
        </select>
        <label>Destination:</label>
        <select id="sel-dst">
          <option value="BADR" selected>BADR - Badrinath Shrine</option>
          <option value="KEDN">KEDN - Kedarnath Shrine</option>
          <option value="GANG">GANG - Gangotri Shrine</option>
          <option value="UTTK">UTTK - Uttarkashi</option>
          <option value="MALP">MALP - Malpa</option>
        </select>
        <button id="btn-calc" onclick="calculateRoute()">Compute Safest Route (Dijkstra)</button>
      </div>

      <div class="card">
        <h3>Hazard Simulation (What-If Analysis)</h3>
        <p style="font-size: 12px; color: #94a3b8;">Simulate cloudburst or rockfall to test algorithmic detours:</p>
        <button onclick="simulateHazard('NODE', 'RUDR', 77.08, 'Critical')">Simulate Cloudburst at Rudraprayag</button>
        <button onclick="simulateHazard('EDGE', 'R10', 82.00, 'Critical')">Simulate Alaknanda Gorge Block</button>
        <button class="btn-secondary" onclick="resetHazards()">Reset to Normal Weather</button>
      </div>

      <div class="card">
        <h3>Routing Recommendation</h3>
        <div id="result-container" class="result-box">
          Select origin and destination to query backend...
        </div>
      </div>
    </div>
    <div id="map"></div>
  </div>

  <script>
    const map = L.map('map').setView([30.45, 79.1], 9);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 18,
      attribution: '© OpenStreetMap contributors'
    }).addTo(map);

    let polylineLayer = null;
    let markersLayer = L.layerGroup().addTo(map);

    async function loadLocations() {
      try {
        const res = await fetch('/api/locations');
        const data = await res.json();
        markersLayer.clearLayers();
        data.locations.forEach(loc => {
          const color = loc.risk_level === 'Critical' ? '#dc2626' :
                        loc.risk_level === 'High' ? '#ea580c' :
                        loc.risk_level === 'Moderate' ? '#ca8a04' : '#16a34a';

          const marker = L.circleMarker([loc.lat, loc.lon], {
            radius: 8,
            fillColor: color,
            color: '#fff',
            weight: 2,
            opacity: 1,
            fillOpacity: 0.9
          }).addTo(markersLayer);

          marker.bindPopup(`<b>${loc.name} (${loc.location_id})</b><br>` +
                           `Risk Score: <b>${loc.risk_score}</b> <span class="pill pill-${loc.risk_level}">${loc.risk_level}</span><br>` +
                           `Elevation: ${loc.elevation_m}m | Slope: ${loc.slope_deg}°`);
        });
      } catch (e) {
        document.getElementById('api-status').innerText = 'API Disconnected';
        document.getElementById('api-status').style.background = '#dc2626';
      }
    }

    async function calculateRoute() {
      const src = document.getElementById('sel-src').value;
      const dst = document.getElementById('sel-dst').value;
      const box = document.getElementById('result-container');
      box.innerHTML = 'Computing optimal paths with Min-Heap Dijkstra...';

      try {
        const res = await fetch(`/api/route?source=${src}&dest=${dst}`);
        const data = await res.json();
        const safest = data.safest_route;
        const shortest = data.shortest_route;

        box.innerHTML = `<b>Recommendation:</b> ${data.recommendation}<br><br>` +
                        `<b>Safest Path:</b> ${safest.path.join(' ➔ ')}<br>` +
                        `Distance: <b>${safest.total_distance_km} km</b> | Risk Cost: <b>${safest.total_risk_cost}</b><br>` +
                        `Max Hazard Encountered: <span class="pill pill-${safest.max_risk_level}">${safest.max_risk_level}</span><br><br>` +
                        `<b>Shortest Path:</b> ${shortest.path.join(' ➔ ')} (${shortest.total_distance_km} km, cost: ${shortest.total_risk_cost})`;

        if (polylineLayer) map.removeLayer(polylineLayer);
        const polylineCoords = safest.coordinates.map(c => [c[0], c[1]]);
        polylineLayer = L.polyline(polylineCoords, {
          color: safest.max_risk_level === 'Critical' ? '#dc2626' : '#38bdf8',
          weight: 6,
          opacity: 0.85
        }).addTo(map);

        map.fitBounds(polylineLayer.getBounds(), { padding: [40, 40] });
      } catch (err) {
        box.innerHTML = `<span style="color: #ef4444;">Error: ${err.message}</span>`;
      }
    }

    async function simulateHazard(type, target, score, level) {
      await fetch(`/api/simulate?override_type=${type}&target=${target}&score=${score}&level=${level}`);
      await loadLocations();
      await calculateRoute();
    }

    async function resetHazards() {
      await fetch('/api/simulate/reset');
      await loadLocations();
      await calculateRoute();
    }

    window.onload = () => {
      loadLocations();
      calculateRoute();
    };
  </script>
</body>
</html>"""
        self._set_headers(200, "text/html")
        self.wfile.write(html.encode("utf-8"))


def run_server(port: int = 8000, base_dir: Optional[str] = None):
    """Start the SlopeShield REST API and Frontend Bridge Server."""
    backend = SlopeShieldBackend(base_dir)
    backend.initialize()
    backend.refresh_weather_and_scores(mode="mock")

    SlopeShieldApiHandler.backend = backend
    server_address = ("127.0.0.1", port)
    httpd = HTTPServer(server_address, SlopeShieldApiHandler)

    print(f"==================================================================")
    print(f" SlopeShield REST API Server running on http://127.0.0.1:{port}")
    print(f" Full Interactive Frontend Map: http://127.0.0.1:{port}/")
    print(f" Embedded Test Dashboard:      http://127.0.0.1:{port}/dashboard")
    print(f"==================================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.server_close()
