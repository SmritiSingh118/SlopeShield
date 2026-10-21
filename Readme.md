# SlopeShield: Intelligent Landslide Risk & Safe Route System

**College Problem-Based Learning (PBL) Project for DSA + OOP in C++ and Python**  
**Focus Region:** Uttarakhand Char Dham Pilgrimage Network & Disaster Corridors (Garhwal & Kumaon Himalayas)  
**Team:** The Debug Divas

---

## 1. Project Overview

**SlopeShield** is an intelligent disaster-resilient navigation system engineered to safeguard pilgrims, locals, and emergency responders navigating the fragile Himalayan corridors of Uttarakhand. During the monsoon season, cloudbursts and torrential rainfall frequently trigger severe landslides across key pilgrimage arteries (Rishikesh, Rudraprayag, Kedarnath, Badrinath, Gangotri, Malpa).

Traditional navigation systems (such as Google Maps) prioritize shortest physical road kilometers, frequently directing traffic straight into active landslide hazard zones or blocked river gorges. **SlopeShield** solves this critical safety challenge by:
1. Evaluating multi-factor scientific landslide hazard scores (60% static geophysical features + 40% dynamic rainfall features).
2. Weighting road edges according to landslide risk and applying heavy penalty barriers (+1000.0) to Critical danger zones.
3. Executing Dijkstra's algorithm powered by a custom Min-Heap Priority Queue implemented from scratch (CLRS design) in both C++ and Python.
4. Rendering true OpenStreetMap mountain highway curves rather than straight-line approximations.
5. Providing an interactive Leaflet dashboard with live hazard simulation and automatic detour recalculation.

---

## 2. Team Roles & Contribution Breakdown

| Team Member | Role | Assigned Modules & Technical Contributions |
| :--- | :--- | :--- |
| **Member 1<br>(Smriti Singh)** | **Risk Formula & Weather API Lead** | • Multi-factor scientific landslide hazard formula (static geophysical 60%, dynamic precipitation 40%).<br>• Dynamic feature calculation (current rain, 24h accumulated rainfall, antecedent soil moisture, storm duration).<br>• OpenWeatherMap API live integration & calibrated mock monsoon dataset.<br>• Risk test suite (`tests/test_risk.py`). |
| **Member 2<br>(Jahnvi Verma)** | **DSA & Safe Route Engine Lead** | • Road network Graph data structure and Adjacency List representation.<br>• Custom Min-Heap Priority Queue (`MinPriorityQueue`) built from scratch (CLRS complete binary tree array).<br>• Risk-weighted edge cost model: $W = D \times (1 + 1.5 \times R_{\text{edge}}/100) + \text{Penalty}$.<br>• Dijkstra's Algorithm implementation for single-source shortest and safest routes in both C++ (`src/route_engine.cpp`, `safe_route_planner.cpp`) and Python (`safe_route_planner.py`, `scripts/route_engine.py`).<br>• 8-scenario disaster test suite (`tests/test_route.py`, `tests/route_cases.csv`). |
| **Member 3<br>(Anshika Gaur)** | **OOP Architecture & System Integration Lead** | • Core Object-Oriented domain modeling (`core/models.py`) with encapsulation, inheritance, validation, and JSON serialization.<br>• Robust CSV and JSON file handlers (`core/data_handlers.py`) featuring atomic write safety (`.tmp` + `os.replace`) and strict column header validation.<br>• Weather service integration layer (`core/weather_service.py`) supporting seamless live/mock switching and missing-key fallback.<br>• High-level Backend Service facade (`backend/service.py`) and HTTP REST server (`backend/server.py`).<br>• Master CLI orchestrator (`main.py`) with `--serve` and `--live` flags.<br>• C++ data ingestion and JSON export integration.<br>• Comprehensive 8-phase end-to-end integration test suite (`tests/test_integration.py`). |
| **Member 4<br>(Sanya Verma)** | **Frontend & Geospatial Visualization Lead** | • Interactive web dashboard (`frontend/index.html`, `frontend/app.js`, `frontend/style.css`).<br>• Leaflet map integration displaying risk-colored town markers, elevation, and real-time tooltips.<br>• True road geometry polyline rendering with OpenStreetMap/OSRM alignment.<br>• Visual distinction between verified highway geometry and schematic fallbacks.<br>• Interactive Cloudburst Hazard Simulator and emergency corridor comparison tables. |

---

## 3. System Architecture & Pipeline Order

SlopeShield operates strictly in a deterministic, five-phase pipeline:

```
[1. Static Data & Geometry]
    locations_static.csv, road_network.csv, road_geometries.json
                     │
                     ▼
[2. Dynamic Environmental Sensing]
    WeatherService (OpenWeatherMap API or Calibrated Mock Data)
                     │
                     ▼
[3. Scientific Risk Scoring]
    WeightedRiskScorer: Total Risk = 0.60 * Static + 0.40 * Dynamic
    Classifications: Low (<25), Moderate (25-50), High (50-75), Critical (>=75)
                     │
                     ▼
[4. DSA Graph & Cost Modeling]
    Graph Adjacency List: R_edge = (R_u + R_v) / 2
    Cost = Distance * (1 + 1.5 * R_edge / 100) + (1000.0 if Critical else 0.0)
                     │
                     ▼
[5. Route Optimization & Presentation]
    Custom Min-Heap + Dijkstra's Algorithm (C++ & Python)
    -> Shortest vs Safest Path Comparison
    -> Traversal-Order Geometry Concatenation
    -> Frontend JSON Export (data/route_output.json) & Leaflet Map Rendering
```

---

## 4. Key Improvements & Fixes Implemented

1. **High-Fidelity Road Visualization**:
   - Replaced straight-line node connections that cut through mountain terrain with real highway geometry (NH-7, NH-107, NH-108) cached in `data/road_geometries.json` (~150m waypoint spacing).
   - Dijkstra router concatenates segment coordinates in forward traversal order, eliminating duplicate junction coordinates.
   - Explicitly flags verified geometry vs schematic fallbacks (`has_verified_geometry`, `is_schematic`).

2. **Weather Integration Pipeline**:
   - Structured `WeatherService` with support for explicit `--live` or `--mock` modes.
   - If `OWM_API_KEY` is not present, the system gracefully falls back to calibrated mock data and reports `is_live_verified: false` rather than failing or inventing API responses.

3. **OOP Domain Models & Data Integrity**:
   - Enforced validation bounds on coordinates, elevations, slope angles, and risk scores in `core/models.py`.
   - `CsvHandler` and `JsonHandler` implement atomic write operations via temporary files (`.tmp` + `os.replace`) to prevent file corruption during crashes.
   - Strict header validation with descriptive exceptions on missing columns.

4. **Preserved C++ DSA + OOP Requirements**:
   - Preserved C++14 MinGW compatibility for `src/route_engine.cpp` and `safe_route_planner.cpp`.
   - Adjacency list representation, custom binary Min-Heap priority queue from scratch (CLRS), and Dijkstra path search.
   - Implemented dependency-free C++ JSON parsing to load cached road geometry directly in C++.

---

## 5. C++ DSA vs. Python Routing Architecture — Verification Notice

To ensure complete academic transparency for PBL evaluation:
- **Running Web Application (`backend/server.py` & `main.py`)**: Uses the pure Python DSA implementation (`core/route_planner.py`). It builds the weighted adjacency graph, custom priority queue, and Dijkstra path relaxation entirely in native Python for zero-dependency web execution across any OS.
- **Standalone C++ Route Engine (`src/route_engine.cpp` & `safe_route_planner.cpp`)**: A complete, self-contained C++14 implementation of all DSA requirements (Graph Adjacency List, custom Min-Heap Priority Queue from scratch using CLRS binary heap array, Dijkstra algorithm, CSV loader, and JSON exporter). It runs independently via command line (`--test`, `--source`, `--dest`) and can generate `data/route_output.json`.
- **Integration Boundary**: The Python web backend **does not invoke the C++ binary via subprocess or foreign function interface (FFI)** at runtime. Both implementations share the exact same mathematical risk-cost formula ($W = D \times (1 + 1.5 \times R_{\text{edge}}/100) + \text{Penalty}$), identical datasets, and produce identical routing results across all 8 multi-scenario test cases. We document this separation honestly rather than falsely claiming Python runtime invocation of C++.

---

## 6. Setup & Compilation Instructions

### Prerequisites
- Python 3.10+ (Standard library only; no external package dependencies required for base system).
- C++ Compiler: `g++` supporting C++14 or higher (e.g. MinGW GCC on Windows).

### Environment Configuration
Copy `.env.example` to `.env` to configure optional live weather credentials:
```bash
cp .env.example .env
```
Edit `.env`:
```ini
OWM_API_KEY=your_openweathermap_api_key_here
WEATHER_MODE=mock
```
*(If no API key is provided, SlopeShield operates 100% offline using calibrated monsoon data).*

---

## 7. Execution & Verification Commands

### A. Run C++ Route Engine
Compile and run the C++ DSA route engine:
```bash
# Compile with C++14 optimization
g++ -std=c++14 -O2 src/route_engine.cpp -o src/route_engine.exe

# Run 8-scenario automated disaster test suite
./src/route_engine.exe --test

# Query specific corridor (e.g. Rishikesh to Badrinath)
./src/route_engine.exe --source RISH --dest BADR

# Generate default route output JSON and print comparison table
./src/route_engine.exe
```

### B. Run Python Test Suites
Execute each independent test suite:
```bash
# Member 1: Risk Scoring Tests (6 scenarios)
python tests/test_risk.py

# Member 2: Route Engine & Dijkstra Tests (8 scenarios)
python tests/test_route.py

# Member 3: Full End-to-End System Integration Tests (8 phases)
python tests/test_integration.py
```

### C. Run Master Orchestration Pipeline
```bash
# Run complete pipeline in deterministic mock mode
python main.py

# Run complete pipeline with live weather (if API key configured)
python main.py --live

# Query custom corridor
python main.py --source RISH --dest KEDN
```

### D. Run Web Server & Interactive Dashboard
Launch the unified HTTP REST backend and Leaflet map server:
```bash
python main.py --serve --port 8000
```
Open your browser at **`http://127.0.0.1:8000`**.

---

## 8. REST API Reference

The backend HTTP server provides the following endpoints:

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Serves interactive Leaflet frontend dashboard (`frontend/index.html`). |
| `GET` | `/api/health` | System health check, initialization status, and location counts. |
| `GET` | `/api/locations` | All 11 monitored locations with geophysical attributes and risk scores. |
| `GET` | `/api/roads` | All 14 road segments with distances, risk costs, and geometry status. |
| `GET` | `/api/weather/status` | Current weather ingestion mode, live verification status, and timestamp. |
| `POST` | `/api/weather/refresh`| Triggers weather ingestion and recalculates all landslide risk scores. |
| `GET` | `/api/routes` | Pre-computed Shortest vs. Safest comparison for all 7 standard corridors. |
| `GET` | `/api/route?source=RISH&dest=BADR` | Dynamic Dijkstra route computation between any two valid nodes. |
| `GET` | `/api/simulate?override_type=NODE&target=RUDR&score=77.08&level=Critical` | Simulates localized disaster and triggers detour recalculation. |
| `GET` | `/api/simulate/reset` | Resets all hazard simulations and restores normal baseline conditions. |

---

## 9. Verified Test Results Summary

| Test Suite | Component | Scenarios Tested | Status |
| :--- | :--- | :--- | :--- |
| `tests/test_risk.py` | Risk Scorer & Environmental Ingestion | 6 scenarios (Dry winter, Drizzle, Heavy rain, Cloudburst, High-static no-rain, Low-static heavy) | **PASS (6/6)** |
| `tests/test_route.py` | Python Route Engine & Min-Heap | 8 scenarios (Dry baseline, Dham cross-links, Cloudburst bypasses, Gorge blockages) | **PASS (8/8)** |
| `src/route_engine.exe --test` | C++ Route Engine & CLRS Min-Heap | 8 disaster scenarios in C++14 compiled binary | **PASS (8/8)** |
| `safe_route_planner.py --test` | Standalone Python Safe Planner | 8 disaster scenarios with verified geometry | **PASS (8/8)** |
| `safe_route_planner.exe --test`| Standalone C++ Safe Planner | 8 disaster scenarios in C++14 compiled binary | **PASS (8/8)** |
| `tests/test_integration.py` | Full Member 3 System Integration | 8 phases: OOP entities, file handling, backend pipeline, hazard isolation, road geometry, weather fallback, edge cases, REST API | **PASS (8/8)** |
| `node --check frontend/app.js` | Frontend JavaScript Syntax | Client-side Leaflet application syntax | **PASS (0 syntax errors)** |

---

## 10. Known Operational Limitations

1. **Live Weather Key Requirement**: Live weather queries require a valid `OWM_API_KEY` in `.env`. If omitted, the system falls back to calibrated monsoon data and marks results as unverified (`is_live_verified: false`, `source: mock_no_api_key`) to maintain evaluation integrity.
2. **C++ and Python Separation**: As detailed in Section 5, the C++ route engine operates as a standalone compiled tool and CLI; it is not called directly by the Python HTTP server at runtime.
3. **Browser Local File Policy (CORS)**: When opening `frontend/index.html` via double-click (`file://` protocol), browsers block reading local JSON files. Running via `python main.py --serve --port 8000` or VS Code Live Server is required.
4. **Road Blockages**: Physical road closures (e.g. from the Border Roads Organisation) are simulated dynamically via the interactive Hazard Simulator controls or `/api/simulate` endpoint rather than an automated live government webhook.

## Authors

- Smriti Singh
- Jahnvi Verma
- Anshika Gaur
- Sanya Verma
