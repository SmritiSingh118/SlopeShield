
# MEMBER 3 — Individual Contribution Report

## SlopeShield: Intelligent Landslide Risk & Safe Route System

**Student:** Anshika Gaur  
**Role:** Member 3 — OOP Architecture, File Handling, Backend & Integration  
**Team:** The Debug Divas  
**Team ID:** T099  
**Repository:** [SmritiSingh118/SlopeShield](https://github.com/SmritiSingh118/SlopeShield)

---

## 1. Role and Responsibilities

My main responsibility was to build the software backbone that connects the different modules of SlopeShield. I worked on converting separate components into a unified, object-oriented backend and providing an API through which the frontend can communicate with the system.

My key responsibilities were:

1. **OOP Architecture:** Creating domain models and organizing the code into reusable classes and modules.
2. **CSV/JSON File Handling:** Implementing common file-reading and file-writing interfaces, validation, and safe data persistence.
3. **Backend Integration:** Connecting the risk-assessment module with the graph and route-planning module through a central backend service.
4. **REST API:** Providing HTTP endpoints that allow the frontend to retrieve locations, roads, routes, and simulation results.
5. **Project Orchestration and Testing:** Maintaining the master command-line entry point and contributing to end-to-end integration testing.

---

## 2. System Architecture

The backend follows a layered structure. The frontend communicates with the Python backend through HTTP requests and JSON responses. The backend coordinates data handling, risk assessment, and route planning.

```text
+-------------------------------------------------------------+
|                 PRESENTATION LAYER                          |
|          Leaflet Map · Interactive UI · Route Cards         |
+-------------------------------------------------------------+
                         |
                    HTTP / JSON
                         |
+-------------------------------------------------------------+
|              BACKEND & INTEGRATION LAYER                    |
|       SlopeShieldBackend · REST API · Master CLI             |
+-------------------------------------------------------------+
              |                              |
+-----------------------------+  +----------------------------+
|    ENVIRONMENTAL RISK       |  |      ROUTE PLANNING        |
|    Weather and Risk Scoring |  | Graph · Min-Heap ·         |
|    Static + Dynamic Risk    |  | Dijkstra Algorithm         |
+-----------------------------+  +----------------------------+
              |                              |
+-------------------------------------------------------------+
|              DATA HANDLING & PERSISTENCE                    |
|       BaseDataHandler · CsvHandler · JsonHandler             |
|             CSV / JSON datasets and outputs                 |
+-------------------------------------------------------------+
```

### Main Architectural Components

- **Domain Models:** Represent locations, roads, weather readings, risk profiles, and route results.
- **Data Handling Layer:** Loads and saves CSV and JSON data.
- **Backend Service:** Coordinates risk scoring, graph updates, route planning, simulation, and output persistence.
- **REST API Server:** Exposes backend functionality to the frontend.

### Design Patterns and Principles

1. **Facade Pattern:** `SlopeShieldBackend` provides a central interface to operations that would otherwise require several modules to be called separately.
2. **Abstract Base Classes:** Common interfaces are defined for data handlers, risk scorers, and route planners.
3. **Polymorphism:** Concrete classes implement common interfaces, allowing implementations to be replaced without changing the code that uses those interfaces.
4. **Separation of Concerns:** Data models, file handling, risk scoring, route planning, and HTTP communication are kept in separate modules.

---

## 3. OOP Implementation

The following classes are part of the project architecture.

| Class | File | Responsibility |
|---|---|---|
| `BaseEntity` | `core/models.py` | Common base class for model serialization |
| `RiskProfile` | `core/models.py` | Stores static, dynamic, and total risk scores and risk level |
| `WeatherReading` | `core/models.py` | Stores weather measurements used by the risk module |
| `Location` | `core/models.py` | Represents a geographical location and its associated risk/weather data |
| `RoadSegment` | `core/models.py` | Represents a road connection and its distance/risk information |
| `RouteResult` | `core/models.py` | Stores the result of a route calculation |
| `RouteComparison` | `core/models.py` | Stores comparison information for shortest and safest routes |
| `BaseDataHandler` | `core/data_handlers.py` | Abstract interface for file reading and writing |
| `CsvHandler` | `core/data_handlers.py` | Reads and writes CSV data |
| `JsonHandler` | `core/data_handlers.py` | Reads and writes JSON data |
| `DataManager` | `core/data_handlers.py` | Coordinates loading, validation, and persistence |
| `BaseRiskScorer` | `core/risk_scorer.py` | Base interface for risk-scoring implementations |
| `WeightedRiskScorer` | `core/risk_scorer.py` | Implements weighted risk-scoring logic |
| `MinPriorityQueue` | `core/route_planner.py` | Custom Min-Heap priority queue |
| `RoadGraph` | `core/route_planner.py` | Represents the road network using an adjacency list |
| `BaseRoutePlanner` | `core/route_planner.py` | Base interface for route-planning implementations |
| `DijkstraRoutePlanner` | `core/route_planner.py` | Calculates routes using Dijkstra's algorithm |
| `SlopeShieldBackend` | `backend/service.py` | Coordinates the complete backend workflow |
| `SlopeShieldApiHandler` | `backend/server.py` | Handles HTTP API requests |

### A. Encapsulation

Encapsulation keeps an object's internal data controlled through its methods and properties.

For example, `RiskProfile` stores risk values in attributes such as `_total_score` and `_risk_level`. Its score-update method updates the values and derives the corresponding risk category.

The project uses the following risk categories:

- Low: Score below 25
- Moderate: Score from 25 to below 50
- High: Score from 50 to below 75
- Critical: Score of 75 or above

### B. Inheritance

Abstract base classes define common methods that their child classes implement:

- `BaseEntity` → Domain model classes
- `BaseDataHandler` → `CsvHandler` and `JsonHandler`
- `BaseRiskScorer` → `WeightedRiskScorer`
- `BaseRoutePlanner` → `DijkstraRoutePlanner`

### C. Polymorphism

The backend can use common interfaces such as `read()`, `write()`, and route-planning methods while the concrete implementation handles the specific operation.

For example, CSV and JSON handlers provide different implementations of the common data-handler interface.

---

## 4. CSV and JSON File Handling

I worked on the data-handling layer in `core/data_handlers.py`.

Its responsibilities include:

1. **Reading Datasets:** Loading location, road-network, configuration, and generated output files.
2. **Validation:** Checking required fields and handling blank or malformed records.
3. **Data Conversion:** Converting numeric values into the required data types before creating or updating objects.
4. **CSV Handling:** Reading and writing tabular data through `CsvHandler`.
5. **JSON Handling:** Reading and writing structured data through `JsonHandler`.
6. **Safe Writes:** JSON output is written to a temporary file before replacement, reducing the chance of leaving a partially written output file.
7. **Central Coordination:** `DataManager` manages data paths and coordinates loading and saving.

### Project Data Files

- `locations_static.csv`
- `road_network.csv`
- `risk_weights.json`
- `risk_scores.csv`
- `risk_output.json`
- `route_output.json`

**Note:** The project uses CSV and JSON file-based storage. It does not use an SQL database.

---

## 5. Backend Integration

The main integration work is coordinated by the `SlopeShieldBackend` class in `backend/service.py`.

### Integrated Processing Flow

```text
Location and Road CSV / JSON Files
              |
              v
         DataManager
              |
              v
     Location and Road Objects
              |
              v
       Risk Scoring Module
              |
              v
      Updated Location Risks
              |
              v
          RoadGraph
              |
              v
       Min-Heap + Dijkstra
              |
              v
       Shortest / Safest Routes
              |
              v
       Save CSV / JSON Outputs
              |
              v
           REST API
              |
              v
        Frontend Map UI
```

### Main Backend Operations

| Operation | Purpose |
|---|---|
| `initialize()` | Loads and validates datasets and prepares the graph |
| `refresh_weather_and_scores()` | Runs the risk-scoring pipeline and updates risk outputs |
| `plan_route()` | Calculates a route for the requested source, destination, and mode |
| `compare_route()` | Compares shortest and safest route results |
| `plan_all_standard_corridors()` | Calculates route results for configured standard corridors |
| `simulate_hazard()` | Applies a simulated hazard and updates risk/route calculations |
| `reset_hazards()` | Restores the normal baseline after simulation |

### Risk and Route Integration

The backend passes the risk information produced by the risk module into the road-network and route-planning workflow. The route planner can then compare routes using distance and risk-related costs rather than relying only on physical distance.

The risk-scoring design uses:

\[
\text{Total Risk} = 0.6 \times \text{Static Risk}
+ 0.4 \times \text{Dynamic Risk}
\]

This allows weather-related changes to influence the risk values used by route planning.

---

## 6. REST API — Backend to Frontend Communication

I worked on the lightweight HTTP server in `backend/server.py`. It uses Python's built-in `http.server` module and returns JSON responses for API requests.

### Main API Endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/health` | GET | Returns system health/status information |
| `/api/locations` | GET | Returns location data, coordinates, and risk information |
| `/api/roads` | GET | Returns road-network information |
| `/api/routes` | GET | Returns prepared route comparisons |
| `/api/route` | GET | Calculates a route for the requested source, destination, and mode |
| `/api/refresh` | GET/POST, as supported by the running server | Refreshes weather/risk data |
| `/api/simulate` | GET/POST | Applies a hazard simulation |
| `/api/simulate/reset` | GET/POST | Resets the hazard simulation |
| `/` | GET | Serves the backend's map preview where configured |

### API Base Address

```text
http://127.0.0.1:8000
```

### Example Frontend API Request

```javascript
fetch("http://127.0.0.1:8000/api/locations")
  .then(response => response.json())
  .then(data => {
    console.log(data);
  });
```

The API acts as the communication bridge between the Python backend and the frontend. The frontend requests processed results from the backend and uses the returned information to update the map and route details.

---

## 7. Integration with Team Members

My work connected the modules developed by the team.

### A. Risk Assessment Module

- Integrated the risk-scoring workflow into the central backend service.
- Connected location and weather data with the risk profiles used by the system.
- Ensured updated risk information could be passed to route planning.

### B. Route Planning Module

- Connected the road graph and Dijkstra route planner with the backend service.
- Made route results available through backend operations and API responses.
- Supported comparison between shortest-distance and safest-route results.

### C. Frontend and Map Module

- Provided API endpoints for the frontend to retrieve locations, roads, and routes.
- Returned structured JSON data for map markers and route information.
- Connected simulation and reset operations to the frontend workflow.

### Python and C++ Integration Note

The Python backend and C++ route-engine source files are maintained as separate implementations. The C++ programs can be compiled and tested independently. The Python backend should not be described as invoking the C++ executable at runtime unless that connection has been separately implemented and verified.

---

## 8. Files and Modules Worked On

| File | Contribution |
|---|---|
| `core/models.py` | Domain models and object-oriented data structures |
| `core/data_handlers.py` | CSV/JSON handlers and data coordination |
| `core/risk_scorer.py` | Risk-scoring class structure and integration |
| `core/route_planner.py` | Graph, Min-Heap, and route-planning class structure |
| `core/__init__.py` | Core package interface |
| `backend/service.py` | Central backend service/facade |
| `backend/server.py` | HTTP REST API server |
| `backend/__init__.py` | Backend package interface |
| `main.py` | Master command-line entry point |
| `tests/test_integration.py` | Backend and module integration tests |
| `src/route_engine.cpp` | C++ portability/refactoring work |
| `safe_route_planner.cpp` | C++ portability/refactoring work |
| `MEMBER3.md` | Individual contribution documentation |

---

## 9. Testing and Validation

The project test suite covers risk scoring, route planning, and backend integration.

### Latest Recorded Test Summary

| Test Group | Passed |
|---|---:|
| Risk Assessment Tests | 6/6 |
| Route Engine Tests | 8/8 |
| Backend Integration Tests | 6/6 |
| **Total** | **20/20** |

### Test Coverage

- Risk-score calculations and risk-level classification.
- Min-Heap and graph operations.
- Risk-based route costs and Dijkstra route results.
- OOP models and CSV/JSON file handling.
- Backend pipeline integration.
- REST API communication.
- Hazard simulation and reset behavior.

### Run the Test Suite

```powershell
python main.py --test
```

**Testing Note:** A passing test suite verifies the tested software behavior. It should not, by itself, be presented as proof that a real OpenWeatherMap request succeeded. Live weather operation must be confirmed separately from a successful API response or a backend result identifying the live data source.

---

## 10. Weather Data Modes and Limitations

The project supports a mock-data path for demonstrations and a live-weather path when a valid OpenWeatherMap API key is configured.

- **Mock Mode:** Uses prepared readings so that the workflow can be demonstrated without depending on a live API request.
- **Live Mode:** Requests weather information from OpenWeatherMap when the API key and network connection are available.
- **Fallback Behavior:** If a live request cannot be completed, the application may use its configured fallback behavior. Fallback data must not be labelled as live weather.

### Other Limitations

1. The current location and road dataset covers a limited set of locations and corridors.
2. Soil moisture is estimated using weather-related inputs rather than direct sensor measurements.
3. Hazard simulation currently changes the server's in-memory state; it demonstrates how risk and routes respond to changed conditions.
4. Live data availability depends on the external weather service, network connection, and a valid API key.

---

## 11. How to Run and Test the Backend

Run these commands from the project's backend/root directory.

### 1. Open the Project Directory

```powershell
cd "C:\path\to\Landslide_SlopeShield"
```

Replace the example path with the actual location of the project on your computer.

### 2. Run the Complete Test Suite

```powershell
python main.py --test
```

### 3. Run the Backend Server

```powershell
python main.py --serve --port 8000
```

Keep this terminal open while using the application.

### 4. Open the Backend Health Endpoint

```text
http://127.0.0.1:8000/api/health
```

The frontend can use the backend API at:

```text
http://127.0.0.1:8000
```

### 5. Run a Route Query from the Command Line

```powershell
python main.py --route --source RISH --dest BADR --mode safest
```

### 6. Run a Hazard Simulation

```powershell
python main.py --simulate --target RUDR --score 77.08 --level Critical
```

### 7. Compile and Test the Standalone C++ Route Engine

```powershell
g++ -std=c++14 -O2 src/route_engine.cpp -o route_engine.exe
.\route_engine.exe --test
```

The C++ command is a separate compile-and-test workflow. It is not a command to start the Python REST API.

---

## 12. Learning Outcomes

Through this contribution, I gained practical experience in:

- Designing a modular object-oriented software architecture.
- Applying encapsulation, inheritance, abstraction, and polymorphism.
- Working with CSV and JSON file handling.
- Building a Python HTTP server and REST API.
- Integrating multiple software modules through a central backend service.
- Connecting risk-assessment results with graph-based route planning.
- Testing backend workflows and debugging integration issues.
- Collaborating with teammates to connect separate modules into one working prototype.

---

## 13. Summary of Individual Contribution

My contribution focused on the backend foundation of SlopeShield. I worked on the OOP structure, data-handling layer, central backend service, REST API, and integration/testing workflow. These components allow the risk-assessment and route-planning modules to work together and make their results available to the frontend.

**In one line:** I connected the project's data, risk-assessment, route-planning, and frontend modules through a modular Python backend and REST API.
