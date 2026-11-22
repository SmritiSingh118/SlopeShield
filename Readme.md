
# SlopeShield: Intelligent Landslide Risk & Safe Route System

**College Problem-Based Learning (PBL) Project for DSA + OOP in C++ and Python**  
**Focus Region:** Uttarakhand Char Dham Pilgrimage Network & Disaster Corridors (Garhwal and Kumaon Himalayas)  
**Team:** The Debug Divas  
**Project Type:** Disaster-Resilient Navigation and Landslide Risk Assessment System

---

## 1. Project Overview

**SlopeShield** is an intelligent disaster-resilient navigation system designed to improve the safety of pilgrims, local residents, and emergency responders travelling through the mountainous regions of Uttarakhand.

During the monsoon season, heavy rainfall, cloudbursts, and unstable slopes can trigger landslides across important pilgrimage routes such as Rishikesh, Rudraprayag, Kedarnath, Badrinath, Gangotri, and other Himalayan corridors.

Traditional navigation systems generally prioritize shorter travel distances. However, the shortest route may pass through a high-risk landslide zone.

SlopeShield addresses this problem by:

1. Calculating landslide risk using static geographical features and dynamic weather conditions.
2. Assigning risk-based weights to road connections.
3. Applying heavy penalty barriers to Critical-risk areas.
4. Finding shortest and safest routes using Dijkstra's Algorithm.
5. Implementing a custom Min-Heap Priority Queue and Graph using DSA concepts.
6. Displaying road networks and routes through an interactive Leaflet dashboard.
7. Supporting live weather integration, hazard simulation, and automatic route recalculation.

### Key Technologies

| Area | Technology |
|---|---|
| Programming | Python, C++14 |
| Data Structures | Graph, Adjacency List, Min-Heap |
| Algorithms | Dijkstra's Algorithm |
| Backend | Python Standard Library HTTP Server |
| Frontend | HTML, CSS, JavaScript |
| Map Visualization | Leaflet, OpenStreetMap |
| Road Geometry | OSRM and local geometry fallback |
| Weather API | OpenWeatherMap |
| Data Storage | CSV and JSON |
| Testing | Python test suites, C++ test suites, Node.js syntax check |

---

## 2. Team Roles and Contributions

| Team Member | Role | Technical Contributions |
|---|---|---|
| **Member 1 – Smriti Singh** | Risk Formula and Weather API Lead | Multi-factor landslide risk formula, static and dynamic risk calculation, rainfall-based environmental features, OpenWeatherMap integration, calibrated mock weather dataset, and `tests/test_risk.py`. |
| **Member 2 – Jahnvi Verma** | DSA and Safe Route Engine Lead | Graph and adjacency list, custom Min-Heap Priority Queue, risk-weighted edge cost model, Dijkstra's Algorithm in C++ and Python, and route test cases. |
| **Member 3 – Anshika Gaur** | OOP Architecture and System Integration Lead | OOP domain models, CSV/JSON data handling, weather service integration layer, backend service facade, REST API server, master CLI, C++ data ingestion and JSON export workflow, and end-to-end integration testing. |
| **Member 4 – Sanya Verma** | Frontend and Geospatial Visualization Lead | Interactive web dashboard, Leaflet map integration, risk-colored location markers, road geometry visualization, hazard simulator interface, and route comparison tables. |

---

## 3. System Architecture

SlopeShield follows a modular architecture in which the frontend, backend, environmental risk assessment, route planning, and data-handling modules work together.

### Architecture Layers

1. **Presentation Layer**
   - Interactive Leaflet dashboard.
   - Location markers and risk indicators.
   - Route cards and shortest-versus-safest comparison.
   - Hazard simulation controls.

2. **Backend and Integration Layer**
   - `SlopeShieldBackend` service facade.
   - REST API server.
   - Master command-line interface.
   - Communication between project modules.

3. **Environmental Risk Layer**
   - Weather service.
   - Live OpenWeatherMap data or calibrated mock data.
   - Static and dynamic risk calculation.

4. **Route Planning Layer**
   - Road graph using adjacency lists.
   - Custom Min-Heap Priority Queue.
   - Dijkstra's shortest and safest route calculation.

5. **Data Handling Layer**
   - CSV and JSON readers and writers.
   - Data validation.
   - Risk and route output storage.

### Complete System Pipeline

```text
             STATIC PROJECT DATA
       CSV Files + JSON Files + Road Geometry
                       |
                       v
                 DataManager
                       |
                       v
              Domain Model Objects
          Location, Road, WeatherReading
                       |
                       v
                WeatherService
             /                 \
            /                   \
     Live Weather             Mock Weather
    OpenWeatherMap           Calibrated Data
            \                   /
             \                 /
                       |
                       v
               WeightedRiskScorer
                       |
                       v
                 Risk Calculation
       Total Risk = 0.60 * Static
                  + 0.40 * Dynamic
                       |
                       v
                 Road Graph
               Adjacency List
                       |
                       v
             Min-Heap + Dijkstra
                       |
                       v
              Route Comparison
              Shortest vs Safest
                       |
                       v
              Backend Service
              SlopeShieldBackend
                       |
                       v
                  REST API
                       |
                       v
             Frontend Dashboard
             Leaflet + JavaScript
                       |
                       v
             Interactive Map and
             Hazard Simulation
```

---

## 4. Landslide Risk Assessment

SlopeShield combines static geographical characteristics and dynamic environmental conditions to calculate the overall landslide risk.

### Risk Formula

```text
Total Risk = 0.60 * Static Risk
           + 0.40 * Dynamic Risk
```

- **Static Risk (60%):** Represents geographical and geological characteristics.
- **Dynamic Risk (40%):** Represents changing environmental conditions, especially rainfall-related factors.

### Risk Classification

| Risk Score | Risk Level |
|---|---|
| Below 25 | Low |
| 25 to below 50 | Moderate |
| 50 to below 75 | High |
| 75 and above | Critical |

### Risk-Based Road Cost

The road graph uses the following risk-weighted edge cost:

```text
R_edge = (R_u + R_v) / 2

W = D * (1 + 1.5 * R_edge / 100) + Penalty
```

Where:

- `D` = Physical distance of the road segment.
- `R_u` and `R_v` = Risk scores of the connected locations.
- `R_edge` = Average risk of the road segment.
- `Penalty` = Additional cost for Critical-risk zones.

A penalty of `1000.0` is applied to Critical danger zones.

This makes the route planner consider both distance and safety instead of selecting a route based only on physical distance.

---

## 5. Data Structures and Algorithms

### Graph

The road network is represented using an adjacency-list-based Graph.

Each location acts as a vertex, and each road connection acts as an edge.

### Min-Heap Priority Queue

A custom Min-Heap Priority Queue is implemented from scratch.

It helps Dijkstra's Algorithm efficiently select the next node having the minimum route cost.

### Dijkstra's Algorithm

Dijkstra's Algorithm calculates routes using the weighted road network.

SlopeShield uses it to compare:

- **Shortest Route:** Prioritizes lower physical distance.
- **Safest Route:** Considers both road distance and landslide risk.

The system can recalculate routes when a location's risk level changes during hazard simulation.

---

## 6. Geospatial Visualization and Road Geometry

SlopeShield uses Leaflet and OpenStreetMap to display the road network and route information on an interactive map.

### OSRM Road Geometry

The frontend uses OSRM (Open Source Routing Machine) to obtain road-following route geometry.

Instead of displaying a straight line between two locations, the application can display a route following the actual road network.

### Local Geometry Fallback

If OSRM geometry is unavailable, the application can use locally stored road geometry.

This helps maintain route visualization when the external geometry service cannot be reached.

### Geometry Representation

Road geometry is stored in:

```text
data/road_geometries.json
```

The application distinguishes between:

- Verified road geometry.
- Schematic or fallback geometry.

**Important:** OSRM is used for road-route geometry visualization. The project's risk-weighted route selection is performed by its own Graph and Dijkstra implementation.

---

## 7. Key Improvements and Implemented Features

### 7.1 Weather Integration

- Supports explicit live and mock weather modes.
- Uses OpenWeatherMap for live weather data.
- Uses calibrated mock data for offline testing and demonstrations.
- Handles missing API credentials through fallback behavior.
- Reports whether weather data is actually live-verified.

### 7.2 OOP Architecture

Core domain models are implemented in:

```text
core/models.py
```

The models represent locations, weather readings, risk profiles, road segments, and route results.

The architecture uses OOP principles such as:

- Encapsulation.
- Inheritance.
- Abstraction.
- Polymorphism.
- Validation and serialization.

### 7.3 CSV and JSON Data Handling

Implemented in:

```text
core/data_handlers.py
```

Features include:

- CSV reading and writing.
- JSON reading and writing.
- Column-header validation.
- Invalid and blank record handling.
- Safe file-writing operations using temporary files and `os.replace`, where implemented.
- Centralized data coordination through `DataManager`.

### 7.4 Backend Integration

The backend connects the project's modules through a central service facade.

Main file:

```text
backend/service.py
```

The `SlopeShieldBackend` class coordinates:

- Project initialization.
- Location and road data loading.
- Weather refresh.
- Risk score calculation.
- Graph preparation.
- Route planning.
- Route comparison.
- Hazard simulation.
- Simulation reset.
- Output generation.

### 7.5 REST API

The HTTP server is implemented in:

```text
backend/server.py
```

It uses Python's standard-library `http.server` module.

The frontend communicates with the backend through HTTP requests and JSON responses.

### 7.6 C++ DSA Implementation

The standalone C++ route engine preserves the DSA and OOP requirements.

It includes:

- Graph using adjacency lists.
- Custom Min-Heap Priority Queue.
- Dijkstra's Algorithm.
- CSV data loading.
- JSON export.
- Automated route test scenarios.

---

## 8. Member 3: OOP Architecture and Backend Integration

**Contribution:** Anshika Gaur  
**Role:** OOP Architecture and System Integration Lead

My contribution focuses on connecting the different project modules and providing a structured backend architecture.

### 8.1 OOP Domain Models

File:

```text
core/models.py
```

Important classes:

| Class | Responsibility |
|---|---|
| `BaseEntity` | Common base class for domain-model serialization |
| `RiskProfile` | Stores static risk, dynamic risk, total risk, and risk level |
| `WeatherReading` | Stores weather measurements |
| `Location` | Represents geographical locations and associated data |
| `RoadSegment` | Represents road connections, distance, and risk information |
| `RouteResult` | Stores calculated route information |
| `RouteComparison` | Stores shortest and safest route comparisons |

These classes provide a structured representation of the project's data.

### 8.2 CSV and JSON File Handling

File:

```text
core/data_handlers.py
```

Important components:

| Component | Responsibility |
|---|---|
| `BaseDataHandler` | Common file-handling interface |
| `CsvHandler` | CSV file operations |
| `JsonHandler` | JSON file operations |
| `DataManager` | Centralized loading, validation, and persistence |

The module supports structured data loading, validation, and safe output generation.

### 8.3 Weather Service Integration

File:

```text
core/weather_service.py
```

The WeatherService provides an integration layer between the weather data source and the risk-scoring workflow.

It supports:

- Live weather mode using OpenWeatherMap.
- Mock weather mode using calibrated data.
- Missing API key fallback.
- Passing weather readings to the risk-scoring pipeline.

### 8.4 Backend Service Facade

File:

```text
backend/service.py
```

The `SlopeShieldBackend` class acts as the central service layer.

Important operations include:

```text
initialize()
refresh_weather_and_scores()
plan_route()
compare_route()
plan_all_standard_corridors()
simulate_hazard()
reset_hazards()
```

It coordinates data loading, risk calculation, graph preparation, route planning, and output generation.

### 8.5 REST API Server

File:

```text
backend/server.py
```

The API server exposes backend functionality through HTTP endpoints.

It connects the frontend with the Python backend without requiring the frontend to directly access internal Python modules.

### 8.6 Master CLI

File:

```text
main.py
```

The master CLI provides commands for:

- Running the complete pipeline.
- Selecting live or mock weather mode.
- Querying a specific route.
- Starting the backend HTTP server.
- Running project workflows.

### 8.7 Integration Testing

File:

```text
tests/test_integration.py
```

The integration test suite checks whether the different modules work together correctly.

It covers:

1. OOP entities and domain models.
2. CSV and JSON file handling.
3. Backend processing pipeline.
4. Hazard simulation and route behavior.
5. Road geometry handling.
6. Weather fallback.
7. Graph edge cases.
8. REST API communication.

---

## 9. Backend and Frontend Integration

The frontend and backend communicate through HTTP requests.

### Integration Flow

```text
Frontend (HTML, CSS, JavaScript)
              |
              | HTTP Request
              v
       Python REST API
       backend/server.py
              |
              v
       SlopeShieldBackend
       backend/service.py
              |
              v
       Core Project Modules
       --------------------
       models.py
       data_handlers.py
       weather_service.py
       risk_scorer.py
       route_planner.py
              |
              v
       Processed Results
       CSV / JSON Responses
              |
              v
       REST API Response
              |
              v
       Frontend Dashboard
```

### Example Frontend API Request

```javascript
fetch("http://127.0.0.1:8000/api/locations")
  .then(response => response.json())
  .then(data => console.log(data))
  .catch(error => console.error(error));
```

The frontend sends an HTTP request to the backend.

The backend processes the request and returns the required information in JSON format.

The frontend then uses that information to update the dashboard and map.

### Example Workflow: Weather Refresh

1. The user triggers the weather refresh action on the dashboard.
2. The frontend sends a POST request to `/api/weather/refresh`.
3. The backend invokes the weather service.
4. Weather readings are obtained from the live API or mock source.
5. The risk-scoring module recalculates the risk scores.
6. Updated risk information is returned through the API.
7. The frontend updates the displayed risk information.

### Example Workflow: Hazard Simulation

1. The user selects a location for hazard simulation.
2. The frontend sends a simulation request.
3. The backend updates the simulated hazard state.
4. The route-planning module recalculates the affected routes.
5. The updated route information is returned.
6. The frontend displays the revised route and risk information.

---

## 10. C++ and Python Routing Architecture

For academic transparency, the C++ and Python implementations have separate runtime execution paths.

### Python Implementation

The running web application uses the Python implementation:

```text
core/route_planner.py
```

It performs graph construction, Min-Heap operations, and Dijkstra route calculation within the Python backend.

### C++ Implementation

The standalone C++ route engine is implemented in:

```text
src/route_engine.cpp
safe_route_planner.cpp
```

It independently implements:

- Graph using adjacency lists.
- Custom Min-Heap Priority Queue.
- Dijkstra's Algorithm.
- CSV loading.
- JSON export.

It can be compiled and executed separately through the command line.

### Integration Boundary

The Python web backend does not invoke the C++ executable through subprocess or FFI at runtime.

Both implementations use the same mathematical risk-cost model and project datasets.

They are maintained as separate execution paths, and their routing behavior is tested independently.

---

## 11. Project Data Files

Important data files include:

| File | Purpose |
|---|---|
| `locations_static.csv` | Static geographical information about monitored locations |
| `road_network.csv` | Road connections and distances |
| `road_geometries.json` | Road geometry information |
| `risk_weights.json` | Risk calculation weights |
| `risk_scores.csv` | Calculated risk scores |
| `risk_output.json` | Risk calculation output |
| `route_output.json` | Route planning output |

The project uses CSV and JSON file-based storage. It does not use a SQL database.

---

## 12. REST API Reference

**Base URL:**

```text
http://127.0.0.1:8000
```

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Serves the interactive Leaflet dashboard |
| GET | `/api/health` | Returns system health and initialization information |
| GET | `/api/locations` | Returns monitored locations and risk scores |
| GET | `/api/roads` | Returns road segments, distances, risk costs, and geometry status |
| GET | `/api/weather/status` | Returns weather mode and live-verification status |
| POST | `/api/weather/refresh` | Refreshes weather data and recalculates risk scores |
| GET | `/api/routes` | Returns precomputed shortest-versus-safest route comparisons |
| GET | `/api/route?source=RISH&dest=BADR` | Calculates a route between two locations |
| GET | `/api/simulate?override_type=NODE&target=RUDR&score=77.08&level=Critical` | Simulates a localized hazard |
| GET | `/api/simulate/reset` | Resets hazard simulation |

### Example API Testing

Open the following URL in a browser after starting the backend:

```text
http://127.0.0.1:8000/api/health
```

Other endpoints can be tested through a browser or an API testing tool, depending on the HTTP method required.

---

## 13. Setup and Installation

### Prerequisites

- Python 3.10 or above.
- C++ compiler supporting C++14 or higher.
- MinGW GCC or another compatible compiler on Windows.
- Modern web browser.

The base Python backend uses the standard library and does not require Flask.

### Clone the Repository

```bash
git clone https://github.com/SmritiSingh118/SlopeShield.git
cd SlopeShield
```

### Environment Configuration

Copy the example environment file:

```bash
cp .env.example .env
```

Edit the `.env` file:

```ini
OWM_API_KEY=your_openweathermap_api_key_here
WEATHER_MODE=mock
```

A valid OpenWeatherMap API key is required for live weather queries.

Without a valid key, the system can use calibrated mock weather data.

---

## 14. Execution and Verification Commands

Run the commands from the project root directory.

### A. Run the Complete Python Pipeline

```powershell
python main.py
```

### B. Run with Live Weather

```powershell
python main.py --live
```

A valid API key and network connection are required.

### C. Run a Specific Route

```powershell
python main.py --source RISH --dest KEDN
```

### D. Start the Backend Server

```powershell
python main.py --serve --port 8000
```

Open:

```text
http://127.0.0.1:8000
```

### E. Run Python Test Suites

```powershell
python tests/test_risk.py
python tests/test_route.py
python tests/test_integration.py
```

### F. Compile the C++ Route Engine

```powershell
g++ -std=c++14 -O2 src/route_engine.cpp -o src/route_engine.exe
```

### G. Run C++ Tests

```powershell
.\src\route_engine.exe --test
```

### H. Run a C++ Route Query

```powershell
.\src\route_engine.exe --source RISH --dest BADR
```

### I. Check Frontend JavaScript Syntax

```powershell
node --check frontend/app.js
```

---

## 15. Verified Test Results Summary

The following results are recorded in the project's test documentation.

| Test Suite | Component | Scenarios / Coverage | Recorded Result |
|---|---|---|---|
| `tests/test_risk.py` | Risk Scoring and Environmental Ingestion | 6 risk scenarios | PASS (6/6) |
| `tests/test_route.py` | Python Route Engine and Min-Heap | 8 route scenarios | PASS (8/8) |
| `src/route_engine.exe --test` | C++ Route Engine | 8 disaster scenarios | PASS (8/8) |
| `safe_route_planner.py --test` | Standalone Python Safe Planner | 8 scenarios | PASS (8/8) |
| `safe_route_planner.exe --test` | Standalone C++ Safe Planner | 8 scenarios | PASS (8/8) |
| `tests/test_integration.py` | End-to-End System Integration | 8 integration phases | PASS (8/8) |
| `node --check frontend/app.js` | Frontend JavaScript | Syntax validation | PASS (0 syntax errors) |

### Integration Test Coverage

The integration suite covers:

1. OOP entities and domain models.
2. CSV and JSON file handling.
3. Backend processing pipeline.
4. Hazard simulation and route behavior.
5. Road geometry handling.
6. Weather fallback.
7. Graph edge cases.
8. REST API communication.

These are the recorded results; rerun the test commands to verify the current state of the repository.

---

## 16. Known Operational Limitations

1. **Live Weather API:** Live weather queries require a valid `OWM_API_KEY` and network connectivity. If the key is missing or the live request fails, the configured fallback may use mock data.

2. **Weather Verification:** Mock fallback data must not be represented as a successful live API response. The system reports live-verification status separately.

3. **C++ and Python Runtime Separation:** The C++ route engine is a standalone implementation. The Python web backend uses the Python route planner.

4. **OSRM Availability:** External OSRM road geometry may be unavailable due to network or service issues. Locally stored geometry provides a fallback where available.

5. **Browser Local File Policy:** Opening `frontend/index.html` directly through `file://` may prevent browser requests to local resources. Run the project through the backend server or a suitable local development server.

6. **Physical Road Closures:** Road closures are demonstrated through hazard simulation. The project does not claim to have an automated live government road-closure feed.

7. **File-Based Storage:** The project uses CSV and JSON files rather than a database management system.

---

## 17. Future Scope

Possible future improvements include:

- Integration with verified government road-closure feeds.
- More comprehensive real-time environmental datasets.
- Improved landslide prediction using historical data and machine learning.
- Additional disaster-related risk factors.
- More extensive road-network coverage.
- Improved multilingual alerts and emergency communication.
- Deployment of the application on a cloud platform.

---

## 18. Conclusion

SlopeShield demonstrates how Data Structures, Algorithms, Object-Oriented Programming, environmental data, and web technologies can be combined to build a disaster-resilient navigation prototype.

By integrating risk-based route planning, weather information, a custom Min-Heap, Dijkstra's Algorithm, backend services, and interactive geospatial visualization, the project aims to make route selection more safety-aware in landslide-prone Himalayan regions.

The system demonstrates the importance of considering environmental risk alongside physical distance when planning routes.

---

## Authors

- **Smriti Singh**
- **Jahnvi Verma**
- **Anshika Gaur**
- **Sanya Verma**

**Team Name:** The Debug Divas  
**Project:** SlopeShield — Intelligent Landslide Risk & Safe Route System
