# Member-2 — Safe Route Engine (SlopeShield): The Complete Viva & Presentation Guide

> **Author:** Jahnvi Verma (Member 2 — DSA & Safe Route Engine Lead)  
> **Team:** The Debug Divas  
> **Project:** SlopeShield — Intelligent Landslide Risk & Safe Route System  
> **One-line summary to memorize:** *"I represent Uttarakhand's road network as a weighted graph with an adjacency list, design risk-based edge weights incorporating live landslide scores, implement a custom Min-Heap Priority Queue, and run Dijkstra's algorithm to compute the safest, hazard-avoiding routes for pilgrims and emergency responders."*

---

## 0. How to Read This Document

| Time | Path | What You Get |
|---|---|---|
| **5 minutes** | §1 (The Story) + §2 (Glossary) + §10 (Handoff) | High-level understanding of what you built. |
| **20 minutes** | §3 (Algorithm Walkthrough) + §6 (Weight Formula) + §12 (Viva Q&A) | Everything needed to ace your viva presentation. |
| **Full** | Complete guide (§1 to §13) in order | Mastery of all data structures, proofs, and code details. |

---

## 1. The Story in Plain Words (2 minutes)

### The Problem
Traditional navigation systems (such as Google Maps) calculate routes solely based on physical distance or traffic speed. In the fragile Himalayas, the shortest route is frequently the most dangerous: narrow gorges, shear rock faces, and cloudburst-triggered landslides can trap travellers.

### What Member 2 Does
Member 2 acts as the **brain of safe navigation**:
1. Takes the 11 pilgrimage nodes and connects them with Uttarakhand's actual mountain highways and bypasses.
2. Ingests Member 1's real-time landslide risk scores ($0–100$).
3. Inflates road segment traversal costs proportionally to landslide danger:
   $$\text{Cost} = \text{Distance} \times \left(1 + 1.5 \times \frac{\text{Edge Risk}}{100}\right) + \text{Critical Penalty}$$
4. Runs **Dijkstra's Algorithm** utilizing an in-house **Min-Heap Priority Queue** to compute the path that minimizes risk-weighted danger rather than pure distance.
5. Generates the frontend-ready JSON containing GPS coordinates and step-by-step segment warnings for Member 4's interactive Leaflet map.

```
+--------------------------+      +-------------------------+
| Member 1: Risk Scores    |      | Road Network Dataset    |
| (data/risk_scores.csv)   |      | (data/road_network.csv) |
+------------+-------------+      +------------+------------+
             \                                /
              \                              /
               v                            v
        +------------------------------------------+
        | Graph Data Structure (Adjacency List)    |
        | - Vertices = 11 Uttarakhand Locations    |
        | - Edges    = 14 Road Corridors           |
        +---------------------+--------------------+
                              |
                              v
        +------------------------------------------+
        | Risk-Based Edge Weight Engine            |
        | Multiplier + Active Hazard Barrier       |
        +---------------------+--------------------+
                              |
                              v
        +------------------------------------------+
        | Custom Min-Heap Priority Queue (CLRS)    |
        | Extract-Min in O(log V)                  |
        +---------------------+--------------------+
                              |
                              v
        +------------------------------------------+
        | Dijkstra's Algorithm                     |
        | Shortest Distance vs Safest Risk Routes  |
        +---------------------+--------------------+
                              |
                              v
        +------------------------------------------+
        | Output: data/route_output.json           |
        | Leaflet Polylines, Hazards & Comparisons|
        +------------------------------------------+
```

---

## 2. The glossary

- **Graph $G = (V, E)$:** A mathematical structure consisting of vertices $V$ (our 11 Uttarakhand locations) connected by edges $E$ (our 14 highway segments).
- **Adjacency List:** A memory-efficient graph representation where each vertex stores a list of its directly connected road segments. Storage complexity is $O(V + E)$, far superior to an $O(V^2)$ adjacency matrix for sparse mountain networks.
- **Min-Heap Priority Queue:** A complete binary tree stored in a contiguous array where the parent node is always $\le$ its child nodes (`parent(i) = (i-1)//2`). Guarantees $O(\log V)$ insertions and $O(\log V)$ extractions of the minimum cost vertex.
- **Edge Weight:** The numeric traversal cost of a road. In SlopeShield, edge weight is not just kilometers; it is risk-inflated cost.
- **Dijkstra's Algorithm:** A greedy graph traversal algorithm that discovers the single-source minimum-cost paths to all destinations in non-negative weighted graphs in $O((V + E) \log V)$ time.
- **Edge Relaxation:** The core step in Dijkstra's algorithm: checking if routing through a newly visited node $u$ offers a safer path to neighbor $v$ than previously known:
  $$\text{if } dist[u] + weight(u, v) < dist[v] \implies dist[v] = dist[u] + weight(u, v)$$
- **Critical Penalty ($P_{crit} = 1000.0$):** A deliberate mathematical barrier added to edges entering active landslide disaster sectors ($R \ge 75$), forcing Dijkstra to divert traffic through safe mountain passes.
- **Monotonicity:** The fundamental guarantee that increasing rainfall or mountain susceptibility on an edge will never lower its traversal cost.

---

## 3. Journey of a Route Computation (End-to-End Trace)

Let's follow a traveller wanting to go from **Rishikesh (`RISH`)** to **Kedarnath (`KEDN`)**:

1. **Graph Construction:** `RouteDataLoader` reads `data/locations_static.csv` to create 11 `Vertex` objects and `data/road_network.csv` to build 14 bidirectional road segments (`Edge` objects) in the adjacency list.
2. **Risk Score Ingestion:** The engine imports Member 1's real-time risk scores from `data/risk_scores.csv` (`RISH`: 21.74 Low, `RUDR`: 56.17 High, `UKHI`: 36.86 Moderate, `UTTK`: 38.57 Moderate).
3. **Weight Computation:** For each road segment:
   - Direct spine `RISH -> RUDR` (140 km): average risk $= (21.74 + 56.17)/2 = 38.96$. Multiplier $= 1 + 1.5 \times (38.96/100) = 1.584$. Cost $= 221.8$.
   - Mandakini highway `RUDR -> UKHI` (42 km): average risk $= (56.17 + 36.86)/2 = 46.52$. Multiplier $= 1.698$. Cost $= 71.3$.
   - Ascent to Kedarnath `UKHI -> KEDN` (51 km): average risk $= 42.09$. Multiplier $= 1.631$. Cost $= 83.2$.
   - Transverse bypass `RISH -> UTTK` (145 km) + `UTTK -> UKHI` (125 km).
4. **Dijkstra Execution:**
   - Under **normal weather**, direct path via Rudraprayag (`RISH -> RUDR -> UKHI -> KEDN`, 233 km, risk cost 376.3) is selected.
   - Under **cloudburst at Rudraprayag** (RUDR risk rises to 77.08 Critical):
     Entering RUDR incurs a $+1000.0$ penalty on `RISH-RUDR` and another $+1000.0$ on `RUDR-UKHI`. The direct path cost balloons to **$2382.4$**!
     Dijkstra's Min-Heap pops the bypass vertex `UTTK`, finding the route `RISH -> UTTK -> UKHI -> KEDN` with cost **$493.5$**.
     **Result:** The algorithm safely detours 88 km via Uttarkashi, bypassing the disaster zone!
5. **Frontend JSON Delivery:** The coordinates `[[lat, lon], ...]`, segment breakdowns, and safety improvement percentages are saved to `data/route_output.json`.

---

## 4. Graph Architecture & Adjacency List Design

### The 11 Vertices (Uttarakhand Nodes)
The graph models the entire Char Dham Yatra and emergency corridors:
1. `RISH` — Rishikesh (Gateway terminal)
2. `DEHR` — Dehradun (State capital, Shivalik foothills)
3. `MUSS` — Mussoorie (High-ridge hill station)
4. `RUDR` — Rudraprayag (Alaknanda-Mandakini river confluence)
5. `UKHI` — Ukhimath (Kedarnath winter seat & Chopta junction)
6. `KEDN` — Kedarnath (Mandakini valley shrine, 3,553 m)
7. `CHAM` — Chamoli / Gopeshwar (Alaknanda gorge commercial center)
8. `BADR` — Badrinath (Upper Alaknanda shrine, 3,100 m)
9. `UTTK` — Uttarkashi (Bhagirathi valley gateway)
10. `GANG` — Gangotri (Upper Bhagirathi shrine, 3,048 m)
11. `MALP` — Malpa (Eastern Pithoragarh border corridor)

### The 14 Road Network Edges (`data/road_network.csv`)
```
[R01] RISH <---> DEHR (45 km, NH-7)
[R02] DEHR <---> MUSS (34 km, Mussoorie Rd)
[R03] MUSS <---> UTTK (135 km, NH-707A via Suwakholi)
[R04] RISH <---> UTTK (145 km, NH-34 via Chamba)
[R05] UTTK <---> GANG (99 km, NH-34 via Harsil)
[R06] UTTK <---> RUDR (130 km, NH-107A via Tehri-Ghansali)
[R07] RISH <---> RUDR (140 km, NH-7 via Devprayag & Srinagar)
[R08] RUDR <---> UKHI (42 km, NH-107 via Kund)
[R09] UKHI <---> KEDN (51 km, NH-107 Kedarnath corridor)
[R10] RUDR <---> CHAM (68 km, NH-7 Alaknanda gorge)
[R11] UKHI <---> CHAM (65 km, NH-107A Chopta mountain pass)
[R12] CHAM <---> BADR (96 km, NH-7 via Joshimath)
[R13] CHAM <---> MALP (260 km, NH-107B / NH-9 Pithoragarh corridor)
[R14] UTTK <---> UKHI (125 km, SH-37 Chirbatiya-Mayali bypass)
```

### Why Adjacency List over Adjacency Matrix?
- **Sparse Connectivity:** With $V = 11$ and $E = 14$, the graph density is only $\frac{2 \times 14}{11 \times 10} \approx 25.5\%$.
- **Adjacency Matrix:** Requires $11 \times 11 = 121$ entries, wasting space on disconnected pairs and requiring $O(V)$ time to inspect neighbors.
- **Adjacency List:** Stores exactly $2 \times 14 = 28$ directed edge pointers. Iterating through neighbors takes $O(\text{deg}(u))$ time, enabling optimal Dijkstra execution.

---

## 5. Custom Min-Heap Priority Queue (DSA Requirement 4)

In accordance with CLRS (*Introduction to Algorithms*), the Min-Heap Priority Queue is implemented from fundamental principles without relying on third-party heap containers.

### Heap Invariant
For any element at index $i$:
- $\text{Parent Index} = \lfloor \frac{i - 1}{2} \rfloor$
- $\text{Left Child Index} = 2i + 1$
- $\text{Right Child Index} = 2i + 2$
- **Invariant:** $\text{Priority}(\text{parent}) \le \text{Priority}(\text{child})$

### Core Operations
1. **`push(priority, item)`:**
   - Appends element to the end of the array ($O(1)$).
   - Bubbles up via `_sift_up(i)` until heap invariant holds ($O(\log N)$).
2. **`pop()` (Extract-Min):**
   - Retrieves the root element at index $0$ ($O(1)$ minimum guaranteed).
   - Moves the last array element to index $0$ and removes the tail ($O(1)$).
   - Bubbles down via `_sift_down(0)` by swapping with the smaller child ($O(\log N)$).
3. **`peek()` / `top()`:** Returns the minimum element in $O(1)$ time.

---

## 6. Risk-Based Edge Weight Formula (Requirement 3)

The edge weight formula connects Member 1's scientific risk scores with Member 2's algorithmic routing engine.

### The Formulation
For road segment $e = (u, v)$ with physical distance $D$:
1. **Segment Composite Risk:**
   $$R_{edge} = \frac{R_u + R_v}{2}$$
2. **Risk Level Assignment:**
   - If $L_u == \text{"Critical"}$ or $L_v == \text{"Critical"}$ or $R_{edge} \ge 75.0$: **Critical**
   - Else if $L_u == \text{"High"}$ or $L_v == \text{"High"}$ or $R_{edge} \ge 50.0$: **High**
   - Else if $R_{edge} \ge 25.0$: **Moderate**
   - Else: **Low**
3. **Risk Multiplier ($\alpha = 1.5$):**
   $$\mu_{risk} = 1.0 + 1.5 \times \left(\frac{R_{edge}}{100.0}\right)$$
4. **Traversal Cost:**
   $$\text{Weight}(u, v) = D \times \mu_{risk} + \begin{cases} 1000.0 & \text{if } \text{Level} = \text{"Critical"} \\ 0.0 & \text{otherwise} \end{cases}$$

### Numerical Worked Example (Rudraprayag - Chamoli on NH-7)
- Distance $D = 68.0\text{ km}$
- $R_{RUDR} = 56.17$ (High), $R_{CHAM} = 35.80$ (Moderate)
- $R_{edge} = \frac{56.17 + 35.80}{2} = 45.98$
- Multiplier $\mu = 1.0 + 1.5 \times 0.4598 = 1.6897$
- Total Risk-Weighted Cost $= 68.0 \times 1.6897 = \mathbf{114.90}$
- Under dry conditions ($R_{edge} \approx 15$), cost is only $83.3$. Under cloudburst ($R_{edge} \ge 75$), cost becomes $68 \times 2.125 + 1000 = \mathbf{1144.50}$.

---

## 7. Dijkstra's Algorithm Implementation (Requirement 5)

### Algorithmic Steps
1. Initialize distance array `dist[v] = infinity` for all $v \in V$, and `dist[source] = 0`.
2. Initialize parent map `parent[v] = null` and `edge_used[v] = null`.
3. Push `(0.0, source)` into the custom `MinPriorityQueue`.
4. While `pq` is not empty:
   - Extract min `(curr_cost, u)`.
   - If $u$ has already been finalized (`visited`), skip.
   - If $u == \text{destination}$, terminate early.
   - For each outgoing `edge` in `adj[u]`:
     - Select weight: $w = \text{edge.risk\_cost}$ (for Safest mode) or $\text{edge.distance\_km}$ (for Shortest mode).
     - **Relaxation:** If `curr_cost + w < dist[v]`:
       - `dist[v] = curr_cost + w`
       - `parent[v] = u`
       - `edge_used[v] = edge`
       - `pq.push(dist[v], v)`
5. **Path Reconstruction:** Backtrack from `destination` to `source` using `parent` pointers and reverse the resulting list.

### Complexity Analysis
- **Time Complexity:** $O((V + E) \log V)$
  - With $V = 11$ and $E = 14$, total operations $\approx (11 + 14) \log_2(11) \approx 87$ operations (virtually instantaneous, $< 1\text{ ms}$).
- **Space Complexity:** $O(V + E)$ for graph adjacency list and distance tables.

---

## 8. Multi-Scenario Route Testing & Comparisons (Requirement 6)

The test suite in `tests/test_route.py` replays **8 distinct weather and hazard scenarios** from `tests/route_cases.csv`:

```
=========================================================================================================
Case ID                          | Source->Dest | Safest Path Got              | Safest Expected              | Verdict
=========================================================================================================
C01_baseline_dry_rish_badr       | RISH->BADR   | RISH->RUDR->CHAM->BADR       | RISH->RUDR->CHAM->BADR       | PASS
C02_baseline_dham_cross_kedn_badr | KEDN->BADR   | KEDN->UKHI->CHAM->BADR       | KEDN->UKHI->CHAM->BADR       | PASS
C03_baseline_rish_uttk           | RISH->UTTK   | RISH->UTTK                   | RISH->UTTK                   | PASS
C04_cloudburst_rudr_divert_kedn  | RISH->KEDN   | RISH->UTTK->UKHI->KEDN       | RISH->UTTK->UKHI->KEDN       | PASS
C05_cloudburst_rudr_divert_badr  | RISH->BADR   | RISH->UTTK->UKHI->CHAM->BADR | RISH->UTTK->UKHI->CHAM->BADR | PASS
C06_gorge_block_rudr_cham        | RUDR->BADR   | RUDR->UKHI->CHAM->BADR       | RUDR->UKHI->CHAM->BADR       | PASS
C07_narendra_nagar_block         | RISH->UTTK   | RISH->DEHR->MUSS->UTTK       | RISH->DEHR->MUSS->UTTK       | PASS
C08_monsoon_malpa_flank          | CHAM->MALP   | CHAM->MALP                   | CHAM->MALP                   | PASS
=========================================================================================================
```

### Key Detour Scenarios Explained:
1. **Case C04 & C05 (Cloudburst at Rudraprayag):**
   - Direct Char Dham highway through Rudraprayag becomes Critical ($77.08$).
   - Dijkstra automatically diverts travellers via `RISH -> UTTK -> UKHI`, bypassing Rudraprayag gorge completely!
2. **Case C06 (Alaknanda Gorge Landslide):**
   - Direct NH-7 segment between Rudraprayag and Chamoli is blocked.
   - Dijkstra automatically reroutes traffic via Ukhimath and the scenic **Chopta mountain pass** (`RUDR -> UKHI -> CHAM`), avoiding the blocked gorge.
3. **Case C07 (NH-34 Landslide near Narendra Nagar):**
   - Direct route to Uttarkashi blocked by rockfall.
   - Traffic is safely rerouted via the **Dehradun-Mussoorie ridge corridor** (`RISH -> DEHR -> MUSS -> UTTK`), saving travellers from entrapment.

---

## 9. Code & File Architecture

```
pblseme3/
├── data/
│   ├── locations_static.csv     # (Member 1) 11 Uttarakhand locations
│   ├── risk_scores.csv          # (Member 1) Live risk scores 0-100 & levels
│   ├── road_network.csv         # (Member 2) 14 highway edges & distances
│   └── route_output.json        # (Member 2) Frontend JSON for Leaflet map
├── scripts/
│   └── route_engine.py          # (Member 2) Python Route Engine & CLI
├── src/
│   └── route_engine.cpp         # (Member 2) C++17 OOP & DSA implementation
├── tests/
│   ├── route_cases.csv          # (Member 2) 8 Scenario test definitions
│   └── test_route.py            # (Member 2) Automated verification suite
└── MEMBER2.md                   # (Member 2) Complete Project & Viva Guide
```

---

## 10. Frontend Handoff Contract (To Member 4)

Member 4 can directly consume `data/route_output.json` to render the web map in Leaflet:

```javascript
// Example Member 4 Leaflet consumption
fetch('data/route_output.json')
  .then(res => res.json())
  .then(data => {
    const route = data.routes["RISH_to_BADR"].safest_route;
    
    // Draw route polyline directly from GPS coordinates
    const polyline = L.polyline(route.coordinates, {
      color: route.max_risk_level === "Critical" ? "red" : 
             route.max_risk_level === "High" ? "orange" : "blue",
      weight: 5
    }).addTo(map);

    // Render individual road segment popups
    route.segments.forEach(seg => {
      console.log(`Highway: ${seg.highway} | Risk: ${seg.edge_risk_level} | Cost: ${seg.risk_cost}`);
    });
  });
```

---

## 11. Steps to Run and Test (Terminal Commands)

Open PowerShell in the project directory (`pblseme3`):

### Step 1: Run the Safe Route Engine
```powershell
python scripts/route_engine.py
```
*Generates `data/route_output.json` and prints the Shortest vs Safest comparison table for all Char Dham corridors.*

### Step 2: Query an On-Demand Route
```powershell
python scripts/route_engine.py --source KEDN --dest BADR
```
*Computes and displays the optimal path between Kedarnath and Badrinath.*

### Step 3: Run the Complete Automated Test Suite
```powershell
python tests/test_route.py
```
*Runs all 5 test phases: MinPriorityQueue unit tests, Graph adjacency checks, Risk-weight monotonicity, Dijkstra optimality invariants, and all 8 scenario comparisons. (Output: `ALL MEMBER-2 ROUTE ENGINE TESTS PASSED (8/8)`).*

### Step 4: (Lab PC) Compile & Run C++ Engine
```powershell
g++ -std=c++17 src/route_engine.cpp -o route_engine
./route_engine
```
*Compiles the clean, standard C++17 OOP implementation and outputs the matching route table.*

---

