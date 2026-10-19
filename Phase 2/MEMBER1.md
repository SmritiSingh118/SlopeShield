# My Contribution — Smriti Singh (Member 1)

> **Student Name:** Smriti Singh  
> **Student ID:** 2510370445  
> **Role:** Member 1 — Data Collection & Processing, Risk Scoring, and Testing  
> **Team:** The Debug Divas  
> **Project:** SlopeShield — Intelligent Landslide Risk & Safe Route System  
> **Project Repository:** `pblseme3`

---

## 1. Role and Responsibilities

As **Member 1**, I was responsible for the environmental data and landslide-risk assessment module of SlopeShield. My work focuses on preparing location and terrain information, incorporating weather conditions, calculating location-level risk scores, and validating the scoring workflow. The resulting risk information is passed to the route-planning and backend components so that environmental hazards can be considered when comparing travel routes.

My key responsibilities were:

1. **Environmental Data Preparation:** Organizing static location and terrain attributes used to estimate baseline landslide susceptibility.
2. **Weather Integration:** Supporting live weather retrieval through OpenWeatherMap and mock weather data for offline demonstrations.
3. **Dynamic Feature Processing:** Preparing weather-related readings for the risk-assessment workflow.
4. **Weighted Risk Scoring:** Combining static environmental risk with dynamic weather risk using the project's configured 60/40 weighting approach.
5. **Risk Classification:** Assigning each calculated score to a risk category using the implemented thresholds.
6. **Testing and Validation:** Evaluating scoring behavior against predefined weather and terrain scenarios.
7. **Output Generation:** Producing risk results in CSV and JSON formats for use by the rest of the system.
8. **Module Integration:** Maintaining compatible risk outputs for the graph, route-planning, and backend pipeline.

---

## 2. Environmental Data Collection and Processing

SlopeShield uses static terrain information together with dynamic weather conditions to estimate landslide risk across its supported locations.

### Input data categories

- **Static features:** Location and terrain characteristics such as elevation, slope, and other susceptibility-related attributes.
- **Dynamic features:** Weather conditions that can change over time, including rainfall-related measurements and other available weather readings.

### Main data and configuration files

| File | Purpose |
| :--- | :--- |
| `data/locations_static.csv` | Stores static location and terrain attributes used in baseline risk assessment. |
| `data/dynamic_features.csv` | Stores processed dynamic environmental and weather features. |
| `data/live_weather.json` | Stores weather data produced by the weather-fetching workflow. |
| `config/risk_weights.json` | Defines the weights used by the risk-scoring process. |
| `data/risk_scores.csv` | Stores calculated location-level risk scores in tabular form. |
| `data/risk_output.json` | Stores risk-assessment results in JSON format for downstream modules. |

### Data-processing workflow

```text
Static Location and Terrain Data
                 |
                 v
         Static Feature Input
                 |
                 +--------------------------+
                                            |
Weather API / Mock Weather Data             |
                 |                          |
                 v                          |
       Dynamic Feature Processing           |
                 |                          |
                 +------------+-------------+
                              |
                              v
                      Risk Scoring Input
```

The prepared inputs are combined by the scoring pipeline to produce a risk score for each supported location.

---

## 3. Weather Data Integration

Weather is a dynamic component of landslide-risk assessment because rainfall and changing atmospheric conditions can influence slope stability. SlopeShield's weather workflow supports both live retrieval and mock mode.

### Live weather retrieval

The weather-fetching component uses OpenWeatherMap when live API access is configured. Retrieved readings are saved and prepared for use by the dynamic-feature and risk-scoring workflow.

### Mock weather mode

Mock mode supplies deterministic weather scenarios for offline demonstrations and repeatable testing. It allows the risk-scoring workflow to be exercised without relying on a live API request.

### Weather-processing workflow

```text
          OpenWeatherMap API
                   |
                   v
             Weather Fetcher <----- Mock Weather Mode
                   |
                   v
             Weather Readings
                   |
                   v
        Dynamic Feature Processing
                   |
                   v
             Risk Scoring Input
```

The resulting weather features contribute to the dynamic portion of the total risk score.

---

## 4. Risk Scoring Methodology

The scoring method combines **static environmental risk** and **dynamic weather risk** into a single score on a 0–100 scale. The configured weighting approach assigns 60% importance to static risk and 40% to dynamic risk.

### Weighted scoring formula

\[
\text{Total Risk Score} = 0.60 \times \text{Static Risk} + 0.40 \times \text{Dynamic Risk}
\]

Both component scores contribute to the final result, allowing the system to represent persistent terrain susceptibility alongside changing weather conditions.

### Risk classification

The calculated total score is mapped to one of four risk categories:

| Total risk score | Risk category |
| :--- | :--- |
| Below 25 | **Low** |
| 25 to below 50 | **Moderate** |
| 50 to below 75 | **High** |
| 75 to 100 | **Critical** |

### Scoring workflow

1. Load the static location and terrain data.
2. Retrieve live weather readings or use mock weather data.
3. Prepare the dynamic weather features.
4. Calculate static and dynamic risk components.
5. Combine both components using the configured 60/40 weighting.
6. Assign the risk category from the total score.
7. Write the results to the CSV and JSON output files.

```text
Static Risk Inputs          Dynamic Weather Inputs
        |                            |
        v                            v
 Static Risk Score           Dynamic Risk Score
        |                            |
        +-------------+--------------+
                      |
                      v
             60% / 40% Weighted Score
                      |
                      v
              Total Risk Score (0–100)
                      |
                      v
             Low / Moderate / High / Critical
                      |
                      v
             risk_scores.csv / risk_output.json
```

---

## 5. Scripts, Configuration, and Data Files

The Member 1 module is organized around weather retrieval, risk scoring, configuration, environmental datasets, and validation resources.

| File | Responsibility |
| :--- | :--- |
| `scripts/fetch_weather.py` | Retrieves weather readings and supports mock weather mode. |
| `scripts/risk_scorer.py` | Calculates risk scores from static and dynamic environmental inputs. |
| `config/risk_weights.json` | Stores the weights used by the scoring method. |
| `data/locations_static.csv` | Provides static location and terrain inputs. |
| `data/dynamic_features.csv` | Holds processed dynamic features. |
| `data/live_weather.json` | Stores weather output from the weather workflow. |
| `data/risk_scores.csv` | Stores the calculated risk scores in CSV format. |
| `data/risk_output.json` | Stores the risk-assessment output in JSON format. |
| `tests/test_risk.py` | Contains automated tests for the risk-scoring module. |
| `tests/risk_cases.csv` | Provides predefined scenarios for risk-scoring validation. |

Together, these files connect data preparation and weather processing to scoring, classification, testing, and downstream integration.

---

## 6. Risk Assessment Pipeline

The risk-assessment pipeline transforms static and dynamic environmental inputs into location-level scores that can be consumed by the route-planning engine.

```text
+--------------------------------------+
| Static Location / Terrain Data       |
+--------------------------------------+
                    |
                    v
+--------------------------------------+
| Weather Data: Live or Mock           |
+--------------------------------------+
                    |
                    v
+--------------------------------------+
| Dynamic Feature Processing           |
+--------------------------------------+
                    |
                    v
+--------------------------------------+
| Static + Dynamic Weighted Scoring    |
|             60% / 40%                |
+--------------------------------------+
                    |
                    v
+--------------------------------------+
| Risk Score (0–100) and Classification|
+--------------------------------------+
                    |
                    v
+--------------------------------------+
| risk_scores.csv / risk_output.json   |
+--------------------------------------+
```

The output files provide the interface between environmental assessment and the wider application. Consistent field names and data formats allow the backend to load risk profiles and pass the resulting risk information to the route-planning module.

---

## 7. Testing and Validation

The risk-scoring module is evaluated using predefined scenarios that combine different static-risk levels with weather conditions. These tests help verify both the numerical scoring behavior and the resulting risk classification.

### Validation scenarios

The risk test suite includes cases representing:

- **Dry winter conditions** — lower dynamic risk under dry weather.
- **Drizzle conditions** — a moderate change in weather-related risk.
- **Heavy rainfall** — increased dynamic risk due to stronger rainfall.
- **Cloudburst conditions** — a high-impact weather scenario that can produce a Critical overall score.
- **High static risk with little rainfall** — evaluates the contribution of terrain susceptibility.
- **Low static risk with heavy rainfall** — evaluates how severe dynamic conditions affect the combined score.

### Testing areas

1. **Input processing:** Checks that the scorer reads the required static and dynamic feature values.
2. **Weighted calculation:** Checks the combined risk score produced from static and dynamic components.
3. **Risk classification:** Checks that scores map to the expected categories.
4. **Weather workflow:** Exercises mock mode for repeatable offline testing.
5. **Output generation:** Checks the risk results written to CSV and JSON files.
6. **Integration compatibility:** Ensures risk outputs can be consumed by the backend and route-planning workflow.

The Member 1 test documentation records **6/6 risk scenarios passing**. The Phase-II progress report separately lists live OpenWeatherMap validation as pending.

### Commands

```bash
python scripts/fetch_weather.py --mock
python scripts/risk_scorer.py
python tests/test_risk.py
```

---

## 8. Integration with the Overall SlopeShield System

Member 1 supplies environmental data and risk scores that help the remaining modules account for landslide hazards when calculating and presenting routes.

```text
+--------------------------------------+
| Member 1: Environmental Data & Risk  |
| Weather Features and Risk Scores     |
+--------------------------------------+
                    |
                    v
+--------------------------------------+
| Member 2: Graph and Route Planning   |
| Risk-Aware Dijkstra Pathfinding      |
+--------------------------------------+
                    |
                    v
+--------------------------------------+
| Member 3: Backend and Integration    |
| Data Handling and Pipeline           |
+--------------------------------------+
                    |
                    v
+--------------------------------------+
| Member 4: Presentation Layer         |
| Map and Route Visualization          |
+--------------------------------------+
```

The risk scores are integrated into the backend's environmental-risk pipeline. The route engine uses risk information alongside road distances and graph weights to compare shortest-distance and safer route options. The presentation layer can then display route recommendations and associated risk information.

---

## 9. Integration with Teammates' Modules

### A. Integration with Member 2 — Graph and Route Planning

The risk-assessment module supplies location-level risk profiles used by the route-planning engine. The integrated pipeline applies these scores when evaluating road segments and comparing route alternatives, allowing environmental hazards to influence the safest-path calculation.

### B. Integration with Member 3 — Backend and Data Handling

The backend coordinates dataset loading, risk-score generation, graph construction, and route calculation. Member 1's scoring pipeline is integrated through the `WeightedRiskScorer`, and the resulting risk information is written to `data/risk_scores.csv` and `data/risk_output.json` for system-wide use.

### C. Integration with Member 4 — Presentation Layer

The presentation layer uses the integrated backend outputs to communicate location risk and route recommendations through the map interface. Structured CSV and JSON outputs provide a consistent hand-off between the environmental-risk module and the user-facing components.

---

## 10. Dependencies and Limitations

1. **Live weather access:** Live retrieval depends on network connectivity, a valid OpenWeatherMap API key, and service availability.
2. **Mock weather data:** Mock readings support offline demonstrations and repeatable testing but do not represent current live conditions.
3. **Input quality:** Risk estimates depend on the quality, completeness, and freshness of the available terrain and weather data.
4. **Scoring configuration:** Calculated results depend on the configured weights and the scoring logic used by the project.
5. **Data integration:** Downstream components rely on consistent risk-output fields and file formats.
6. **Terrain-data improvement:** The Phase-II progress report lists real DEM-based slope and elevation data as pending work for Member 1.
7. **Live-weather validation:** The Phase-II progress report lists live OpenWeatherMap validation as pending; the documented risk scenarios have been tested through the project test workflow.

---

## 11. Current Status

**Contribution area:** Environmental data preparation, weather integration, weighted risk scoring, and testing.

The Member 1 module provides the core environmental-risk inputs and scoring outputs required by the integrated SlopeShield pipeline.

- **Static data:** Location and terrain inputs are organized for risk assessment.
- **Weather workflow:** Supports live retrieval and mock mode.
- **Scoring:** Combines static and dynamic risk using the 60/40 weighting approach.
- **Classification:** Maps total scores to Low, Moderate, High, and Critical categories.
- **Output:** Generates CSV and JSON risk results for downstream modules.
- **Validation:** The documented risk-test results record 6/6 scenarios passing.
- **Integration:** Risk scores feed into the backend and risk-aware route-planning workflow.
- **Remaining work:** Real DEM-based terrain data and live-weather validation are listed as pending in the Phase-II progress report.

---

## 12. How to Run and Test My Work

Run the following commands from the root directory of `pblseme3`.

### 1. Fetch mock weather data

```bash
python scripts/fetch_weather.py --mock
```

This runs the weather workflow in mock mode for offline testing and demonstrations.

### 2. Run the risk scorer

```bash
python scripts/risk_scorer.py
```

This executes the scoring workflow and generates risk results from the available input data.

### 3. Run the risk tests

```bash
python tests/test_risk.py
```

This runs the automated tests for the risk-assessment module.

### 4. Run the integrated project test suite

```bash
python main.py --test
```

This runs the project's multi-module test workflow, including the Member 1 risk scenarios.

---

## 13. Summary

My contribution to SlopeShield centers on environmental data preparation, weather integration, dynamic-feature processing, weighted landslide-risk scoring, and validation. I organized the static location inputs and scoring configuration, supported live and mock weather workflows, and contributed the risk outputs used by the backend and route-planning modules.

The 60/40 weighted scoring approach combines baseline terrain susceptibility with changing weather conditions, while the Low, Moderate, High, and Critical classifications make the resulting scores easier for the integrated system to interpret. These outputs help SlopeShield incorporate environmental risk into route comparison and safe-route recommendations.
