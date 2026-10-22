# My Contribution — Anshika Gaur (Member 3)

> **Student Name:** Anshika Gaur  
> **Student ID:** 2510014858  
> **Role:** Member 3 — OOP Architecture, File Handling, Backend & Integration
> **Team:** The Debug Divas  
> **Project:** SlopeShield — Intelligent Landslide Risk & Safe Route System  
> **Project Repository:** `pblseme3`  

---

## 1. Role and Responsibilities

As **Member 3**, my assigned mandate was to construct the unified engineering backbone of SlopeShield. While Member 1 focused on environmental data and risk science, and Member 2 focused on graph theory and algorithmic pathfinding, my responsibility was to convert isolated scripts into an extensible, production-ready, object-oriented software system:

1. **OOP Architecture:** Designing domain models, enforcing encapsulation, and applying appropriate inheritance and polymorphism across the codebase.
2. **CSV/JSON File Handling:** Building a centralized, polymorphic, and robust data persistence layer to parse and serialize tabular and hierarchical datasets with schema validation and error tolerance.
3. **Backend Integration:** Implementing a centralized Backend Facade controller (`SlopeShieldBackend`) that pipelines Member 1's scientific risk scoring directly into Member 2's DSA route engine.
4. **Backend $\rightarrow$ Frontend Connection:** Designing a zero-dependency REST API server (`backend/server.py`) with full CORS support and a clean JSON schema contract to serve Member 4's interactive Leaflet map.
5. **Team Integration & Orchestration:** Building the master CLI (`main.py`), ensuring backwards-compatible C++ compilation under college lab environments, and creating the end-to-end integration test suite (`tests/test_integration.py`).

---

## 2. OOP Implementation & Architecture

I restructured the system from procedural scripts into a **4-Layer Object-Oriented Architecture**:

```
+-----------------------------------------------------------------------------------+
|                           PRESENTATION LAYER (Member 4)                           |
|       Leaflet.js Map  ·  Interactive UI  ·  Hazard Simulator  ·  Route Cards       |
+-----------------------------------------------------------------------------------+
                                         ▲
                         HTTP / REST API │ (JSON over HTTP)
                                         ▼
+-----------------------------------------------------------------------------------+
|                    BACKEND & INTEGRATION FACADE (Member 3 - YOU)                   |
|   SlopeShieldBackend  ·  HTTP APIServer  ·  Pipeline Controller  ·  Master CLI     |
+-----------------------------------------------------------------------------------+
                         ▲                                   ▲
                         │                                   │
+------------------------┴----------+     +------------------┴----------------------+
|     ENVIRONMENTAL RISK LAYER      |     |           DSA ROUTE ENGINE              |
|           (Member 1)              |     |              (Member 2)                 |
|  - WeatherFetcher (Live / Mock)   |     |  - Graph (Adjacency List)               |
|  - BaseScorer -> WeightedScorer   |     |  - Custom Min-Heap Priority Queue (CLRS)|
|  - RiskProfile & Classifications  |     |  - BaseRouter -> DijkstraRouter         |
+-----------------------------------+     +-----------------------------------------+
                         ▲                                   ▲
                         │                                   │
+------------------------┴-----------------------------------┴----------------------+
|                      DATA INGESTION & PERSISTENCE LAYER (Member 3)                 |
|   BaseDataHandler  ───►  CsvHandler  ·  JsonHandler  ·  Validation & Schemas      |
|   Locations CSV · Roads CSV · Weather JSON · Risk Scores CSV · Route Output JSON   |
+-----------------------------------------------------------------------------------+
```

### Design Patterns Applied:
1. **Facade Pattern (`SlopeShieldBackend`)**: Hides the multi-step complexity of dataset ingestion, dynamic weather processing, risk calculation, adjacency graph construction, and Dijkstra pathfinding behind clean, high-level method calls (`initialize()`, `refresh_weather_and_scores()`, `plan_route()`, `simulate_hazard()`).
2. **Strategy Pattern (`BaseRoutePlanner` / `RoutingMode`)**: Allows runtime swapping of routing strategies between *Shortest Distance* (minimizing physical road kilometers) and *Safest Path* (minimizing hazard-weighted costs).
3. **Template / Polymorphic Handler Pattern (`BaseDataHandler`)**: Defines standard abstract interfaces for file I/O, implemented specifically for CSV (tabular data) and JSON (nested hierarchical documents).

---

## 3. Classes and Objects Used

All domain models and operational engines were built inside the `core/` and `backend/` packages:

| Class | File Location | Responsibility & Behavior |
| :--- | :--- | :--- |
| **`BaseEntity`** | `core/models.py` | Abstract Base Class enforcing standardized dictionary serialization (`to_dict()`). |
| **`RiskProfile`** | `core/models.py` | Encapsulates static, dynamic, and total risk scores (0–100) and automatically derives the categorical risk level (`Low`, `Moderate`, `High`, `Critical`). |
| **`WeatherReading`** | `core/models.py` | Encapsulates current rainfall, 24h forecast, humidity, 3-day antecedent rainfall, and temperature metrics. |
| **`Location`** | `core/models.py` | Encapsulates geographical pilgrimage nodes (coordinates, elevation, slope, soil, landuse, lithology, past history) and embeds its own `RiskProfile` and `WeatherReading` instances. |
| **`RoadSegment`** | `core/models.py` | Encapsulates highway edges, physical distances, and calculates traversal weights with critical safety penalties. |
| **`RouteResult`** | `core/models.py` | Encapsulates Dijkstra traversal output: node path, path names, Leaflet GPS coordinates `[[lat, lon], ...]`, distance, cost, and segment breakdowns. |
| **`RouteComparison`** | `core/models.py` | Encapsulates the side-by-side comparison of Shortest vs Safest routes, calculating detour distance and risk reduction percentage. |
| **`BaseDataHandler`** | `core/data_handlers.py` | Abstract Base Class defining standard `read()` and `write()` interfaces for file I/O. |
| **`CsvHandler`** | `core/data_handlers.py` | Concrete CSV handler with whitespace trimming, empty line filtering, and schema validation. |
| **`JsonHandler`** | `core/data_handlers.py` | Concrete JSON handler with UTF-8 encoding, indent formatting, and atomic temporary writes. |
| **`DataManager`** | `core/data_handlers.py` | High-level dataset coordinator managing paths, model hydration, validation, and file persistence. |
| **`BaseRiskScorer`** | `core/risk_scorer.py` | Abstract Base Class defining the contract for environmental scoring models. |
| **`WeightedRiskScorer`**| `core/risk_scorer.py` | Concrete risk scorer implementing Member 1's scientific 60% static / 40% dynamic formula. |
| **`MinPriorityQueue`** | `core/route_planner.py` | Custom Min-Heap priority queue implemented from scratch (CLRS complete binary tree mechanics). |
| **`RoadGraph`** | `core/route_planner.py` | Space-efficient Adjacency List graph storing `Location` vertices and `RoadSegment` edges. |
| **`BaseRoutePlanner`** | `core/route_planner.py` | Abstract Base Class defining pathfinding algorithms. |
| **`DijkstraRoutePlanner`**| `core/route_planner.py` | Concrete Dijkstra router computing single-source paths and detour comparisons. |
| **`SlopeShieldBackend`**| `backend/service.py` | Unified Facade controller orchestrating the entire end-to-end data and execution pipeline. |
| **`SlopeShieldApiHandler`**| `backend/server.py` | HTTP Request Handler implementing REST endpoints and serving the Leaflet map preview. |

---

## 4. Encapsulation, Inheritance & Polymorphism

### A. Encapsulation
Every domain class encapsulates its internal variables using private attributes (e.g., `self._total_score`, `self._risk_level`, `self._distance_km`) and exposes controlled access through read-only `@property` decorators:

```python
# From core/models.py
class RiskProfile(BaseEntity):
    def __init__(self, static_score: float = 0.0, dynamic_score: float = 0.0, 
                 total_score: float = 0.0, risk_level: str = "Low"):
        self._static_score: float = float(static_score)
        self._dynamic_score: float = float(dynamic_score)
        self._total_score: float = float(total_score)
        self._risk_level: str = str(risk_level)

    @property
    def total_score(self) -> float:
        return self._total_score

    @property
    def risk_level(self) -> str:
        return self._risk_level

    def update_scores(self, static_score: float, dynamic_score: float, total_score: float):
        """Enforces that risk_level can NEVER contradict total_score."""
        self._static_score = round(float(static_score), 2)
        self._dynamic_score = round(float(dynamic_score), 2)
        self._total_score = round(float(total_score), 2)
        
        # Invariant enforcement
        if self._total_score < 25.0:   self._risk_level = "Low"
        elif self._total_score < 50.0: self._risk_level = "Moderate"
        elif self._total_score < 75.0: self._risk_level = "High"
        else:                          self._risk_level = "Critical"
```

### B. Inheritance
I created clean abstract base classes (`ABC`) to declare architectural contracts that concrete subclasses inherit and fulfill:
- `BaseEntity` $\rightarrow$ Inherited by `Location`, `RoadSegment`, `RiskProfile`, `WeatherReading`, `RouteResult`, `RouteComparison`.
- `BaseDataHandler` $\rightarrow$ Inherited by `CsvHandler` and `JsonHandler`.
- `BaseRiskScorer` $\rightarrow$ Inherited by `WeightedRiskScorer`.
- `BaseRoutePlanner` $\rightarrow$ Inherited by `DijkstraRoutePlanner`.

```python
# From core/data_handlers.py
class BaseDataHandler(ABC):
    @abstractmethod
    def read(self, file_path: str) -> Any:
        pass

    @abstractmethod
    def write(self, file_path: str, data: Any) -> bool:
        pass

class CsvHandler(BaseDataHandler):
    def read(self, file_path: str) -> List[Dict[str, str]]:
        # Concrete implementation for tabular data
        ...

class JsonHandler(BaseDataHandler):
    def read(self, file_path: str) -> Any:
        # Concrete implementation for hierarchical JSON
        ...
```

### C. Polymorphism
The backend interacts with abstract interfaces rather than concrete implementations:
- The backend relies on `BaseDataHandler.read()` and `BaseDataHandler.write()`, allowing file formats to be substituted without altering business logic.
- Route calculation invokes `BaseRoutePlanner.find_path()`, allowing future algorithms (such as $A^*$ or Bellman-Ford) to be introduced polymorphically without changing the service facade.

---

## 5. CSV/JSON File Handling

File operations in `core/data_handlers.py` were built to prevent runtime crashes, malformed records, and data corruption:

1. **Schema & Header Verification:**
   - Automatically cleans leading/trailing whitespace from fieldnames and values.
   - Filters out blank rows and verifies essential columns before instantiating objects.
2. **Type Coercion & Clamping:**
   - Numerical fields are converted to `float` or `int` with safety bounding (e.g., negative rainfall is clamped to `0.0`, slope is capped at `70.0°`).
3. **Atomic File Writes (Safe Persistence):**
   - When writing JSON files (such as `route_output.json`), `JsonHandler` writes to a temporary file (`.tmp`) first and performs an atomic file replacement (`os.replace`). If an unexpected crash occurs during writing, the existing file remains uncorrupted.
4. **Central Data Coordinator (`DataManager`):**
   - Coordinates paths relative to project root (`BASE_DIR`).
   - Loads `locations_static.csv` $\rightarrow$ returns hydrated `Dict[str, Location]`.
   - Loads `road_network.csv` $\rightarrow$ returns hydrated `List[RoadSegment]`.
   - Loads `risk_weights.json` $\rightarrow$ returns configuration dictionary.
   - Persists [risk_scores.csv](file:///c:/Users/asus/Downloads/jahnvi/data/risk_scores.csv), [risk_output.json](file:///c:/Users/asus/Downloads/jahnvi/data/risk_output.json), and [route_output.json](file:///c:/Users/asus/Downloads/jahnvi/data/route_output.json).

---

## 6. Backend Integration

In `backend/service.py`, I implemented `SlopeShieldBackend`, which unifies the entire multi-member system into an automated pipeline:

```
[Raw CSV Datasets & Config]
           │
           ▼
[DataManager (Member 3)] ──► Hydrates Location & RoadSegment Objects
           │
           ▼
[WeightedRiskScorer (Member 1)] ──► Computes Static & Dynamic Scores (0-100)
           │
           ▼
[Location.set_risk()] ──► Updates Encapsulated RiskProfile on all 11 Nodes
           │
           ▼
[RoadGraph (Member 2)] ──► Updates Edge Weights (Distance * Multiplier + Penalty)
           │
           ▼
[DijkstraRoutePlanner (Member 2)] ──► Computes Shortest vs Safest Paths
           │
           ▼
[DataManager (Member 3)] ──► Saves data/risk_scores.csv & data/route_output.json
           │
           ▼
[REST API Server (Member 3)] ──► Serves Endpoints to Frontend (Member 4)
```

### Core Operations Provided by `SlopeShieldBackend`:
- `initialize()`: Validates input datasets, builds the `RoadGraph`, and sets baseline weights.
- `refresh_weather_and_scores(use_mock=True)`: Executes Member 1's risk engine across all 11 locations and persists the output.
- `plan_route(source_id, dest_id, mode)`: Queries single-source Dijkstra routes.
- `compare_route(source_id, dest_id)`: Generates detailed comparison metrics between Shortest and Safest paths.
- `plan_all_standard_corridors()`: Evaluates all 7 standard Char Dham corridors and exports `data/route_output.json`.
- `simulate_hazard(override_type, target, score, level)`: Dynamically injects disaster conditions (e.g. cloudburst at Rudraprayag) and updates graph traversal costs in real time.
- `reset_hazards()`: Restores graph weights back to normal weather baseline.

---

## 7. Backend $\rightarrow$ Frontend Communication

In `backend/server.py`, I built a **zero-dependency, lightweight HTTP REST API server** utilizing Python's built-in `http.server`:

### REST API Endpoints:

| Endpoint | HTTP Method | Purpose | Response Format |
| :--- | :--- | :--- | :--- |
| `/api/health` | `GET` | Health check, system status, entity counts | JSON status |
| `/api/locations` | `GET` | All 11 locations with GPS coordinates & risk levels | JSON array for Leaflet markers |
| `/api/roads` | `GET` | All 14 road corridors with distance & risk costs | JSON array for road network |
| `/api/routes` | `GET` | Precomputed comparisons for all standard corridors | Complete `route_output.json` |
| `/api/route` | `GET` | On-demand path query: `?source=RISH&dest=BADR&mode=safest` | Waypoints, distance, cost, detour advice |
| `/api/simulate` | `GET` / `POST` | Injects hazard: `?override_type=NODE&target=RUDR&score=77.08` | Real-time reroute confirmation |
| `/api/simulate/reset`| `GET` / `POST` | Restores standard baseline weights | JSON status |
| `/` | `GET` | Serves interactive Leaflet.js HTML dashboard | HTML page with live interactive map |

### Frontend JSON Schema Contract (for Member 4's Leaflet Map):
```json
{
  "source_id": "RISH",
  "dest_id": "KEDN",
  "is_identical": false,
  "distance_diff_km": 88.0,
  "risk_reduction_pct": 79.8,
  "recommendation": "Safest route takes +88.0 km detour to reduce risk cost by 79.8% (avoids active landslide hazards).",
  "safest_route": {
    "total_distance_km": 321.0,
    "total_risk_cost": 486.3,
    "max_risk_level": "Moderate",
    "path": ["RISH", "UTTK", "UKHI", "KEDN"],
    "coordinates": [
      [30.0869, 78.2676],
      [30.7298, 78.4434],
      [30.5100, 79.0900],
      [30.7346, 79.0669]
    ]
  }
}
```

---

## 8. Integration with Teammates' Modules

### A. Integration with Smriti's Risk Assessment Module (Member 1)
- Smriti created `locations_static.csv`, `risk_weights.json`, and the 60/40 scoring formulas.
- I encapsulated her scoring logic inside `WeightedRiskScorer` and integrated her weather reading formats into `WeatherReading`.
- My `SlopeShieldBackend` automatically runs her scoring pipeline, applies her threshold cutoffs (<25 Low, <50 Moderate, <75 High, $\ge 75$ Critical), and writes the contract files `risk_scores.csv` and `risk_output.json`.

### B. Integration with Jahnvi's Graph & Dijkstra Module (Member 2)
- Jahnvi built the road network topology (`road_network.csv`), custom Min-Heap Priority Queue, and Dijkstra algorithm.
- I encapsulated her graph structure inside `RoadGraph` and her pathfinding logic inside `DijkstraRoutePlanner`.
- My backend connects Smriti's risk scores directly to Jahnvi's edge weights:
  $$\text{Edge Weight} = \text{Distance} \times \left(1 + 1.5 \times \frac{\text{Edge Risk}}{100}\right) + \text{Critical Penalty}$$
- I also updated Jahnvi's C++ implementations (`src/route_engine.cpp` and `safe_route_planner.cpp`) to replace compiler-specific C++17 structured bindings and `gmtime_s` with portable C++14 constructs, allowing her C++ engine to compile and pass 8/8 tests on college lab MinGW GCC 6.3 compilers.

### C. Integration with Sanya's Presentation Module (Member 4)
- Sanya is responsible for the presentation layer.
- I established the backend bridge so her frontend has zero blockers:
  1. She can fetch real-time data dynamically via `http://127.0.0.1:8000/api/route`.
  2. She can consume precomputed offline data directly from `data/route_output.json`.
- I implemented an embedded test dashboard inside `backend/server.py` at `GET /` that demonstrates Leaflet map markers, colored polylines, and interactive detour buttons.

---

## 9. Files I Worked On

| File | Status | Description of Work Performed |
| :--- | :--- | :--- |
| `core/models.py` | **Created** | Encapsulated OOP domain models (`BaseEntity`, `Location`, `RoadSegment`, `RiskProfile`, `WeatherReading`, `RouteResult`, `RouteComparison`). |
| `core/data_handlers.py`| **Created** | Standardized file handling layer (`BaseDataHandler`, `CsvHandler`, `JsonHandler`, `DataManager`) with schema validation and atomic writes. |
| `core/risk_scorer.py` | **Created** | OOP hierarchy (`BaseRiskScorer` $\rightarrow$ `WeightedRiskScorer`) wrapping Member 1's formula. |
| `core/route_planner.py`| **Created** | OOP hierarchy (`BaseRoutePlanner` $\rightarrow$ `DijkstraRoutePlanner`, `RoadGraph`, `MinPriorityQueue`) wrapping Member 2's DSA. |
| `core/__init__.py` | **Created** | Core package interface. |
| `backend/service.py` | **Created** | `SlopeShieldBackend` Facade controller orchestrating the entire integration pipeline. |
| `backend/server.py` | **Created** | Lightweight REST API server with CORS and embedded Leaflet verification dashboard. |
| `backend/__init__.py` | **Created** | Backend package interface. |
| `main.py` | **Created** | Master CLI orchestrator providing `--serve`, `--route`, `--simulate`, and `--test` options. |
| `tests/test_integration.py`| **Created** | 5-phase end-to-end integration test suite verifying OOP models, file I/O, pipeline, detours, and HTTP API. |
| `src/route_engine.cpp` | **Refactored**| Fixed C++17 structured binding and `gmtime_s` errors for portability on MinGW GCC 6.3. |
| `safe_route_planner.cpp`| **Refactored**| Fixed C++17 structured binding and `gmtime_s` errors for portability on MinGW GCC 6.3. |
| `MEMBER3.md` | **Created** | Comprehensive individual contribution report for viva and project evaluation. |

---

## 10. Testing Performed

All components were verified using automated test suites and live runtime verification:

### Test Suite Execution Summary (`python main.py --test`):

```
==================================================================
 EXECUTING SLOPESHIELD COMPLETE MULTI-MEMBER TEST SUITE
==================================================================

[Phase 1/3] Running Member 1 Risk Tests (tests/test_risk.py)...
  dry_winter_RUDR          74.9     2.4   45.9 Moderate Moderate  PASS
  drizzle_DEHR             37.2     9.1   26.0 Moderate Moderate  PASS
  heavy_MUSS               49.8    60.4   54.0     High     High  PASS
  cloudburst_RUDR          74.9    80.4   77.1 Critical Critical  PASS
  highstatic_norain_MALP   69.9     2.8   43.0 Moderate Moderate  PASS
  lowstatic_heavy_DEHR     37.2    83.7   55.8     High     High  PASS
  >> ALL TESTS PASSED (6/6)

[Phase 2/3] Running Member 2 Route Engine Tests (tests/test_route.py)...
  [1/5] MinPriorityQueue Unit Tests: PASSED
  [2/5] Graph & Adjacency List Tests: PASSED
  [3/5] Risk-Based Edge Weight Design & Monotonicity: PASSED
  [4/5] Dijkstra Optimality & Invariant Checks: PASSED
  [5/5] Replaying Multi-Scenario Route Comparisons: PASSED (8/8)
  >> ALL MEMBER-2 ROUTE ENGINE TESTS PASSED (8/8)

[Phase 3/3] Running Member 3 Integration Tests (tests/test_integration.py)...
  [Phase 1] Validating OOP Architecture & Domain Models: PASSED
  [Phase 2] Validating CSV and JSON File Handlers: PASSED
  [Phase 3] Validating Backend Integration Pipeline: PASSED
  [Phase 4] Validating Hazard Detour Routing: PASSED
  [Phase 5] Validating Backend -> Frontend HTTP API Communication: PASSED
  >> ALL MEMBER 3 INTEGRATION TESTS PASSED (5/5)

==================================================================
 >> ALL PROJECT TESTS PASSED ACROSS ALL MODULES (19/19)!
==================================================================
```

### Detailed Verifications:
1. **OOP Encapsulation & Domain Models:** Verified that updating scores in `RiskProfile` automatically sets the correct classification level and cannot disagree with the numeric score.
2. **File Handler Safety:** Verified `CsvHandler` and `JsonHandler` read/write cycles on scratch files, verified whitespace cleaning, and verified atomic replacement.
3. **Hazard Detour Routing (Case C04):** Verified that under normal weather, `RISH -> KEDN` traverses via Rudraprayag (`RISH -> RUDR -> UKHI -> KEDN`, 233 km). When a cloudburst is simulated on Rudraprayag (score: 77.08 Critical), Dijkstra automatically detours via Uttarkashi (`RISH -> UTTK -> UKHI -> KEDN`, 321 km), avoiding the hazard and reducing risk cost by 79.8%.
4. **Live HTTP REST Communication:** Verified that a local server listening on port 8765 responds to `GET /api/health`, `GET /api/locations`, `GET /api/route`, and `GET /api/simulate` with `200 OK` and valid JSON structures.
5. **C++ Compilation Test:** Compiled `src/route_engine.cpp` with `g++ -std=c++14 -O2 src/route_engine.cpp -o route_engine.exe` and verified `.\route_engine.exe --test` passed 8/8 tests.

---

## 11. Current Status

- **Member 3 Assigned Responsibilities:** **100% Complete and Fully Verified.**
- **Backend & Core Engine:** 100% functional, operational, and running locally.
- **REST API Server:** Running on `http://127.0.0.1:8000/`.

---

## 12. Dependencies and Remaining Limitations

1. **Member 4's Standalone UI Deliverable:**  
   The backend API and data contracts are complete. Sanya can directly consume the API (`/api/route`) or disk output (`data/route_output.json`) when delivering her final standalone presentation frontend.
2. **OpenWeatherMap Live vs Mock Mode:**  
   The system runs offline by default using realistic, deterministic mock readings so that college viva demonstrations function without an active internet connection or API key. Live pulls are available whenever an OpenWeatherMap API key is supplied.
3. **Single Active Simulation:**  
   The current in-memory hazard simulation affects graph edge weights globally on the server; future enhancements could maintain per-session simulation contexts.

---

## 13. How to Run and Test My Work

### 1. Execute the Complete Pipeline End-to-End:
```powershell
python main.py
```
*Loads datasets, runs the risk engine, updates the graph, calculates all 7 Char Dham corridors, persists `data/route_output.json`, and prints the Shortest vs Safest comparison table.*

### 2. Run the Full Multi-Member Automated Test Suite (19/19 Tests):
```powershell
python main.py --test
```

### 3. Launch the REST API Server & Leaflet Map Dashboard:
```powershell
python main.py --serve --port 8000
```
*Open your web browser and navigate to: `http://127.0.0.1:8000/`*

### 4. Query an On-Demand Route via CLI:
```powershell
python main.py --route --source RISH --dest BADR --mode safest
```

### 5. Demonstrate an Active Hazard Simulation (Detour Rerouting):
```powershell
python main.py --simulate --target RUDR --score 77.08 --level Critical
```
*Demonstrates that Dijkstra detects the critical hazard at Rudraprayag and automatically diverts the path via Uttarkashi.*

### 6. Compile and Run the Portable C++ Twin:
```powershell
g++ -std=c++14 -O2 src/route_engine.cpp -o route_engine.exe
.\route_engine.exe --test
```
