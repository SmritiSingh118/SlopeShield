
 * Project: SlopeShield — Intelligent Landslide Risk & Safe Route System
 * Member 2 Implementation: Safe Route Engine (C++ OOP & Data Structures)
 * Author: Jahnvi Verma (Member 2 — DSA & Safe Route Engine Lead)
 * ==============================================================================================
 * 
 * Complete implementation of all 7 assigned responsibilities using C++ OOP and DSA concepts:
 *   1. Graph Data Structure: Encapsulated Vertex, Edge, and Graph classes.
 *   2. Adjacency Representation: Space-efficient Adjacency List (std::unordered_map<string, vector<Edge>>).
 *   3. Risk-Based Edge Weight Design: Formula integrating Member 1's scientific risk scores and
 *      Critical safety penalties: Weight = Distance * (1 + 1.5 * Risk/100) + Critical_Penalty.
 *   4. Priority Queue: Custom Min-Heap Priority Queue (MinPriorityQueue<T>) implemented from
 *      scratch using CLRS complete binary tree array representation (O(log V) push/pop).
 *   5. Dijkstra's Algorithm: DijkstraRouter finding the single-source safest and shortest paths.
 *   6. Route Testing & Comparison: RouteTester evaluating 8 scenarios under different risk conditions
 *      (e.g., cloudburst at Rudraprayag, gorge blockages, Chopta bypass, Mussoorie detour).
 *   7. Route Output: JsonExporter generating frontend-ready JSON (data/route_output.json) for Leaflet.
 * 
 * Compilation (C++17):
 *   g++ -std=c++17 safe_route_planner.cpp -o safe_route_planner
 *   ./safe_route_planner
 *   ./safe_route_planner --source RISH --dest BADR
 *   ./safe_route_planner --test
 * ==============================================================================================
 */

#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include <unordered_map>
#include <unordered_set>
#include <map>
#include <algorithm>
#include <iomanip>
#include <cmath>
#include <limits>
#include <stdexcept>
#include <chrono>
#include <ctime>

namespace SlopeShieldConfig {
    constexpr double DEFAULT_ALPHA = 1.5;             // Risk multiplier scaling factor
    constexpr double CRITICAL_PENALTY = 1000.0;        // Penalty barrier for active critical danger zones
    constexpr double CRITICAL_THRESHOLD = 75.0;       // Risk score threshold for Critical level
    constexpr double HIGH_THRESHOLD = 50.0;           // Risk score threshold for High level
    constexpr double MODERATE_THRESHOLD = 25.0;       // Risk score threshold for Moderate level
}

// ==============================================================================
// UTILITY: String & CSV Parsing Helpers
// ==============================================================================
namespace Utils {
    static inline std::string trim(const std::string& s) {
        size_t start = s.find_first_not_of(" \t\r\n\"");
        if (start == std::string::npos) return "";
        size_t end = s.find_last_not_of(" \t\r\n\"");
        return s.substr(start, end - start + 1);
    }

    static inline std::vector<std::string> parseCsvLine(const std::string& line) {
        std::vector<std::string> tokens;
        std::string current;
        bool inQuotes = false;
        for (char ch : line) {
            if (ch == '"') {
                inQuotes = !inQuotes;
            } else if (ch == ',' && !inQuotes) {
                tokens.push_back(trim(current));
                current.clear();
            } else {
                current += ch;
            }
        }
        tokens.push_back(trim(current));
        return tokens;
    }

    static inline std::string getIsoTimestamp() {
        auto now = std::chrono::system_clock::now();
        std::time_t now_c = std::chrono::system_clock::to_time_t(now);
        std::tm tm_buf{};
#if defined(_WIN32) || defined(_WIN64)
        gmtime_s(&tm_buf, &now_c);
#else
        gmtime_r(&now_c, &tm_buf);
#endif
        std::ostringstream ss;
        ss << std::put_time(&tm_buf, "%Y-%m-%dT%H:%M:%SZ");
        return ss.str();
    }
}

// ==============================================================================
// RESPONSIBILITY 4: CUSTOM MIN-HEAP PRIORITY QUEUE (From Scratch - CLRS Design)
// ==============================================================================
/**
 * @brief Custom Min-Heap Priority Queue implementation from scratch.
 * Conforms to CLRS (Introduction to Algorithms) array-based complete binary tree:
 *   Parent(i)      = (i - 1) / 2
 *   LeftChild(i)   = 2 * i + 1
 *   RightChild(i)  = 2 * i + 2
 * 
 * Provides O(log V) insertion (push) and O(log V) extraction of minimum (pop).
 */
template <typename T>
class MinPriorityQueue {
private:
    struct HeapNode {
        double priority;
        size_t sequence;
        T item;
    };

    std::vector<HeapNode> heap_;
    size_t counter_ = 0;

    void siftUp(size_t index) {
        while (index > 0) {
            size_t parentIdx = (index - 1) / 2;
            if (heap_[index].priority < heap_[parentIdx].priority) {
                std::swap(heap_[index], heap_[parentIdx]);
                index = parentIdx;
            } else {
                break;
            }
        }
    }

    void siftDown(size_t index) {
        size_t n = heap_.size();
        while (true) {
            size_t smallest = index;
            size_t leftChild = 2 * index + 1;
            size_t rightChild = 2 * index + 2;

            if (leftChild < n && heap_[leftChild].priority < heap_[smallest].priority) {
                smallest = leftChild;
            }
            if (rightChild < n && heap_[rightChild].priority < heap_[smallest].priority) {
                smallest = rightChild;
            }

            if (smallest != index) {
                std::swap(heap_[index], heap_[smallest]);
                index = smallest;
            } else {
                break;
            }
        }
    }

public:
    MinPriorityQueue() = default;

    void push(double priority, const T& item) {
        heap_.push_back({priority, counter_++, item});
        siftUp(heap_.size() - 1);
    }

    std::pair<double, T> pop() {
        if (heap_.empty()) {
            throw std::underflow_error("Extraction from empty MinPriorityQueue.");
        }
        HeapNode minNode = heap_[0];
        heap_[0] = heap_.back();
        heap_.pop_back();
        if (!heap_.empty()) {
            siftDown(0);
        }
        return {minNode.priority, minNode.item};
    }

    const T& peek() const {
        if (heap_.empty()) {
            throw std::underflow_error("Peek into empty MinPriorityQueue.");
        }
        return heap_[0].item;
    }

    bool isEmpty() const { return heap_.empty(); }
    size_t size() const { return heap_.size(); }
    void clear() { heap_.clear(); counter_ = 0; }
};

// ==============================================================================
// RESPONSIBILITIES 1 & 2: GRAPH DATA STRUCTURE & ADJACENCY LIST REPRESENTATION
// ==============================================================================
/**
 * @brief Encapsulates a geographical location in Uttarakhand and its landslide risk state.
 */
class Vertex {
private:
    std::string id_;
    std::string name_;
    double lat_ = 0.0;
    double lon_ = 0.0;
    double elevationM_ = 0.0;
    double riskScore_ = 0.0;
    std::string riskLevel_ = "Low";
    double staticScore_ = 0.0;
    double dynamicScore_ = 0.0;

public:
    Vertex() = default;
    Vertex(std::string id, std::string name, double lat, double lon, double elev)
        : id_(id), name_(name), lat_(lat), lon_(lon), elevationM_(elev) {}

    // Getters (Encapsulation)
    const std::string& getId() const { return id_; }
    const std::string& getName() const { return name_; }
    double getLat() const { return lat_; }
    double getLon() const { return lon_; }
    double getElevation() const { return elevationM_; }
    double getRiskScore() const { return riskScore_; }
    const std::string& getRiskLevel() const { return riskLevel_; }
    double getStaticScore() const { return staticScore_; }
    double getDynamicScore() const { return dynamicScore_; }

    // Mutator
    void updateRisk(double totalScore, const std::string& level, double stat = 0.0, double dyn = 0.0) {
        riskScore_ = totalScore;
        riskLevel_ = level;
        staticScore_ = stat;
        dynamicScore_ = dyn;
    }
};

/**
 * @brief Encapsulates a road segment (edge) connecting two locations in the graph.
 */
class Edge {
private:
    std::string roadId_;
    std::string u_; // Source location ID
    std::string v_; // Target location ID
    double distanceKm_ = 0.0;
    std::string highway_;
    std::string roadType_;
    std::string description_;

    // Computed risk-weighted properties
    double edgeRiskScore_ = 0.0;
    std::string edgeRiskLevel_ = "Low";
    double riskMultiplier_ = 1.0;
    double riskCost_ = 0.0;
    bool criticalPenaltyApplied_ = false;

public:
    Edge() = default;
    Edge(std::string id, std::string u, std::string v, double dist,
         std::string highway = "", std::string rtype = "", std::string desc = "")
        : roadId_(id), u_(u), v_(v), distanceKm_(dist),
          highway_(highway), roadType_(rtype), description_(desc), riskCost_(dist) {}

    // Getters
    const std::string& getRoadId() const { return roadId_; }
    const std::string& getSource() const { return u_; }
    const std::string& getDestination() const { return v_; }
    double getDistanceKm() const { return distanceKm_; }
    const std::string& getHighway() const { return highway_; }
    const std::string& getRoadType() const { return roadType_; }
    const std::string& getDescription() const { return description_; }

    double getEdgeRiskScore() const { return edgeRiskScore_; }
    const std::string& getEdgeRiskLevel() const { return edgeRiskLevel_; }
    double getRiskMultiplier() const { return riskMultiplier_; }
    double getRiskCost() const { return riskCost_; }
    bool isCriticalPenaltyApplied() const { return criticalPenaltyApplied_; }

    // Setters for dynamic risk calculation
    void setRiskParameters(double score, const std::string& level, double mult, double cost, bool penalty) {
        edgeRiskScore_ = score;
        edgeRiskLevel_ = level;
        riskMultiplier_ = mult;
        riskCost_ = cost;
        criticalPenaltyApplied_ = penalty;
    }
};

/**
 * @brief Graph data structure representing Uttarakhand's road network.
 * Uses an Adjacency List: std::unordered_map<string, vector<Edge>>.
 * 
 * Space Complexity: O(V + E)
 * Neighborhood Lookup: O(degree(u))
 */
class Graph {
private:
    std::unordered_map<std::string, Vertex> vertices_;
    std::unordered_map<std::string, std::vector<Edge>> adj_;

public:
    Graph() = default;

    void addVertex(const Vertex& v) {
        vertices_[v.getId()] = v;
        if (adj_.find(v.getId()) == adj_.end()) {
            adj_[v.getId()] = {};
        }
    }

    void addEdge(const Edge& e, bool bidirectional = true) {
        adj_[e.getSource()].push_back(e);
        if (bidirectional) {
            Edge revEdge(e.getRoadId() + "_rev", e.getDestination(), e.getSource(),
                         e.getDistanceKm(), e.getHighway(), e.getRoadType(), e.getDescription());
            adj_[e.getDestination()].push_back(revEdge);
        }
    }

    const Vertex* getVertex(const std::string& id) const {
        auto it = vertices_.find(id);
        return (it != vertices_.end()) ? &(it->second) : nullptr;
    }

    Vertex* getVertexMutable(const std::string& id) {
        auto it = vertices_.find(id);
        return (it != vertices_.end()) ? &(it->second) : nullptr;
    }

    const std::vector<Edge>& getNeighbors(const std::string& id) const {
        static const std::vector<Edge> emptyList;
        auto it = adj_.find(id);
        return (it != adj_.end()) ? it->second : emptyList;
    }

    const std::unordered_map<std::string, Vertex>& getVertices() const {
        return vertices_;
    }

    size_t getVertexCount() const { return vertices_.size(); }
    size_t getEdgeCount() const {
        size_t total = 0;
        for (const auto& pair : adj_) total += pair.second.size();
        return total / 2; // Undirected count
    }

// ==============================================================================
// RESPONSIBILITY 3: RISK-BASED EDGE WEIGHT DESIGN
// ==============================================================================
    /**
     * @brief Assigns edge weights based on Member 1's landslide risk scores.
     * 
     * Formula:
     *   R_edge = (R_u + R_v) / 2
     *   risk_multiplier = 1.0 + alpha * (R_edge / 100.0)
     *   penalty = (u or v or edge is Critical) ? critical_penalty : 0.0
     *   risk_cost = distance_km * risk_multiplier + penalty
     */
    void updateEdgeWeights(double alpha = SlopeShieldConfig::DEFAULT_ALPHA,
                           double criticalPenalty = SlopeShieldConfig::CRITICAL_PENALTY,
                           const std::unordered_map<std::string, std::pair<double, std::string>>& nodeOverrides = {},
                           const std::unordered_map<std::string, std::pair<double, std::string>>& edgeOverrides = {}) {
        for (auto& pair : adj_) {
            const std::string& u = pair.first;
            const Vertex* uVert = getVertex(u);

            double uRisk = uVert ? uVert->getRiskScore() : 0.0;
            std::string uLevel = uVert ? uVert->getRiskLevel() : "Low";

            auto uOvIt = nodeOverrides.find(u);
            if (uOvIt != nodeOverrides.end()) {
                uRisk = uOvIt->second.first;
                uLevel = uOvIt->second.second;
            }

            for (Edge& edge : pair.second) {
                const std::string& v = edge.getDestination();
                const Vertex* vVert = getVertex(v);

                double vRisk = vVert ? vVert->getRiskScore() : 0.0;
                std::string vLevel = vVert ? vVert->getRiskLevel() : "Low";

                auto vOvIt = nodeOverrides.find(v);
                if (vOvIt != nodeOverrides.end()) {
                    vRisk = vOvIt->second.first;
                    vLevel = vOvIt->second.second;
                }

                double rEdge = 0.0;
                std::string level = "Low";

                std::string cleanRoadId = edge.getRoadId();
                size_t revPos = cleanRoadId.find("_rev");
                if (revPos != std::string::npos) cleanRoadId = cleanRoadId.substr(0, revPos);

                auto edgeOvIt = edgeOverrides.find(cleanRoadId);
                if (edgeOvIt != edgeOverrides.end()) {
                    rEdge = edgeOvIt->second.first;
                    level = edgeOvIt->second.second;
                } else {
                    rEdge = std::round(((uRisk + vRisk) / 2.0) * 100.0) / 100.0;

                    if (uLevel == "Critical" || vLevel == "Critical" || rEdge >= SlopeShieldConfig::CRITICAL_THRESHOLD) {
                        level = "Critical";
                    } else if (uLevel == "High" || vLevel == "High" || rEdge >= SlopeShieldConfig::HIGH_THRESHOLD) {
                        level = "High";
                    } else if (rEdge >= SlopeShieldConfig::MODERATE_THRESHOLD) {
                        level = "Moderate";
                    } else {
                        level = "Low";
                    }
                }

                double multiplier = 1.0 + alpha * (rEdge / 100.0);
                bool penaltyApplied = (level == "Critical");
                double cost = edge.getDistanceKm() * multiplier;
                if (penaltyApplied) cost += criticalPenalty;

                cost = std::round(cost * 100.0) / 100.0;
                edge.setRiskParameters(rEdge, level, multiplier, cost, penaltyApplied);
            }
        }
    }
};

// ==============================================================================
// RESPONSIBILITY 5: DIJKSTRA'S ALGORITHM IMPLEMENTATION
// ==============================================================================
enum class RoutingMode {
    SAFEST,   // Minimizes risk-weighted cost
    SHORTEST  // Minimizes physical distance in km
};

struct RouteSegmentResult {
    std::string roadId;
    std::string fromId;
    std::string fromName;
    std::string toId;
    std::string toName;
    std::string highway;
    std::string roadType;
    double distanceKm = 0.0;
    double edgeRiskScore = 0.0;
    std::string edgeRiskLevel;
    double riskMultiplier = 1.0;
    double riskCost = 0.0;
    double fromLat = 0.0;
    double fromLon = 0.0;
    double toLat = 0.0;
    double toLon = 0.0;
};

struct RouteResult {
    std::string sourceId;
    std::string destId;
    std::string modeString;
    bool found = false;
    std::vector<std::string> path;
    std::vector<std::string> pathNames;
    std::vector<std::pair<double, double>> coordinates;
    double totalDistanceKm = 0.0;
    double totalRiskCost = 0.0;
    double averageRiskScore = 0.0;
    std::string maxRiskLevel = "Low";
    std::vector<RouteSegmentResult> segments;
};

class DijkstraRouter {
public:
    static RouteResult findPath(const Graph& graph,
                                const std::string& source,
                                const std::string& destination,
                                RoutingMode mode = RoutingMode::SAFEST) {
        RouteResult result;
        result.sourceId = source;
        result.destId = destination;
        result.modeString = (mode == RoutingMode::SAFEST) ? "risk" : "distance";

        const Vertex* sVert = graph.getVertex(source);
        const Vertex* dVert = graph.getVertex(destination);
        if (!sVert || !dVert) return result;

        if (source == destination) {
            result.found = true;
            result.path = {source};
            result.pathNames = {sVert->getName()};
            result.coordinates = {{sVert->getLat(), sVert->getLon()}};
            result.averageRiskScore = sVert->getRiskScore();
            result.maxRiskLevel = sVert->getRiskLevel();
            return result;
        }

        std::unordered_map<std::string, double> dist;
        std::unordered_map<std::string, std::string> parent;
        std::unordered_map<std::string, Edge> edgeUsed;
        std::unordered_set<std::string> visited;

        for (const auto& pair : graph.getVertices()) {
            dist[pair.first] = std::numeric_limits<double>::infinity();
        }

        dist[source] = 0.0;
        MinPriorityQueue<std::string> pq;
        pq.push(0.0, source);

        while (!pq.isEmpty()) {
            auto [currDist, u] = pq.pop();

            if (visited.find(u) != visited.end()) continue;
            visited.insert(u);

            if (u == destination) break;
            if (currDist > dist[u]) continue;

            for (const Edge& edge : graph.getNeighbors(u)) {
                const std::string& v = edge.getDestination();
                if (visited.find(v) != visited.end()) continue;

                double weight = (mode == RoutingMode::SAFEST) ? edge.getRiskCost() : edge.getDistanceKm();
                double newDist = currDist + weight;

                // Edge Relaxation
                if (newDist < dist[v]) {
                    dist[v] = newDist;
                    parent[v] = u;
                    edgeUsed[v] = edge;
                    pq.push(newDist, v);
                }
            }
        }

        if (dist[destination] == std::numeric_limits<double>::infinity()) {
            result.found = false;
            return result;
        }

        // Backtrack path pointers
        std::vector<std::string> pathNodes;
        std::vector<Edge> pathEdges;
        std::string curr = destination;

        while (curr != source) {
            pathNodes.push_back(curr);
            auto eIt = edgeUsed.find(curr);
            if (eIt != edgeUsed.end()) {
                pathEdges.push_back(eIt->second);
            }
            auto pIt = parent.find(curr);
            if (pIt == parent.end()) break;
            curr = pIt->second;
        }
        pathNodes.push_back(source);

        std::reverse(pathNodes.begin(), pathNodes.end());
        std::reverse(pathEdges.begin(), pathEdges.end());

        result.found = true;
        result.path = pathNodes;
        for (const std::string& nid : pathNodes) {
            const Vertex* v = graph.getVertex(nid);
            result.pathNames.push_back(v->getName());
            result.coordinates.push_back({v->getLat(), v->getLon()});
        }

        double totalDist = 0.0;
        double totalCost = 0.0;
        double sumRisk = 0.0;

        std::map<std::string, int> rankMap = {{"Low", 0}, {"Moderate", 1}, {"High", 2}, {"Critical", 3}};
        int maxRank = 0;

        for (const Edge& e : pathEdges) {
            totalDist += e.getDistanceKm();
            totalCost += e.getRiskCost();
            sumRisk += e.getEdgeRiskScore();

            const Vertex* uV = graph.getVertex(e.getSource());
            const Vertex* vV = graph.getVertex(e.getDestination());

            maxRank = std::max({maxRank,
                                rankMap[uV->getRiskLevel()],
                                rankMap[vV->getRiskLevel()],
                                rankMap[e.getEdgeRiskLevel()]});

            RouteSegmentResult seg;
            seg.roadId = e.getRoadId();
            seg.fromId = e.getSource();
            seg.fromName = uV->getName();
            seg.toId = e.getDestination();
            seg.toName = vV->getName();
            seg.highway = e.getHighway();
            seg.roadType = e.getRoadType();
            seg.distanceKm = e.getDistanceKm();
            seg.edgeRiskScore = e.getEdgeRiskScore();
            seg.edgeRiskLevel = e.getEdgeRiskLevel();
            seg.riskMultiplier = e.getRiskMultiplier();
            seg.riskCost = e.getRiskCost();
            seg.fromLat = uV->getLat();
            seg.fromLon = uV->getLon();
            seg.toLat = vV->getLat();
            seg.toLon = vV->getLon();
            result.segments.push_back(seg);
        }

        std::map<int, std::string> invRankMap = {{0, "Low"}, {1, "Moderate"}, {2, "High"}, {3, "Critical"}};
        result.totalDistanceKm = std::round(totalDist * 100.0) / 100.0;
        result.totalRiskCost = std::round(totalCost * 100.0) / 100.0;
        result.averageRiskScore = pathEdges.empty() ? 0.0 : std::round((sumRisk / pathEdges.size()) * 100.0) / 100.0;
        result.maxRiskLevel = invRankMap[maxRank];

        return result;
    }
};

// ==============================================================================
// RESPONSIBILITY 6: ROUTE TESTING AND COMPARISON
// ==============================================================================
class RouteComparison {
private:
    RouteResult shortest_;
    RouteResult safest_;
    bool isIdentical_ = false;
    double distanceDiffKm_ = 0.0;
    double costDiff_ = 0.0;
    double riskReductionPct_ = 0.0;
    std::string recommendation_;

public:
    RouteComparison(const RouteResult& shortest, const RouteResult& safest)
        : shortest_(shortest), safest_(safest) {
        isIdentical_ = (shortest.path == safest.path);
        distanceDiffKm_ = std::round((safest.totalDistanceKm - shortest.totalDistanceKm) * 100.0) / 100.0;
        costDiff_ = std::round((safest.totalRiskCost - shortest.totalRiskCost) * 100.0) / 100.0;

        if (shortest.totalRiskCost > 0.0) {
            double reduction = (shortest.totalRiskCost - safest.totalRiskCost) / shortest.totalRiskCost * 100.0;
            riskReductionPct_ = std::round(std::max(reduction, 0.0) * 10.0) / 10.0;
        }

        if (isIdentical_) {
            std::ostringstream ss;
            ss << "The shortest path is already the safest path ("
               << std::fixed << std::setprecision(1) << safest.totalDistanceKm
               << " km, risk cost: " << safest.totalRiskCost << ").";
            recommendation_ = ss.str();
        } else {
            std::ostringstream ss;
            ss << "Safest route takes " << std::showpos << std::fixed << std::setprecision(1)
               << distanceDiffKm_ << " km detour to reduce risk cost by "
               << std::noshowpos << riskReductionPct_ << "% (avoids active landslide hazards).";
            recommendation_ = ss.str();
        }
    }

    const RouteResult& getShortest() const { return shortest_; }
    const RouteResult& getSafest() const { return safest_; }
    bool isIdentical() const { return isIdentical_; }
    double getDistanceDiffKm() const { return distanceDiffKm_; }
    double getCostDiff() const { return costDiff_; }
    double getRiskReductionPct() const { return riskReductionPct_; }
    const std::string& getRecommendation() const { return recommendation_; }
};

// ==============================================================================
// DATA INGESTION: CSV Loader
// ==============================================================================
class DataLoader {
public:
    static Graph loadGraph(const std::string& staticPath = "data/locations_static.csv",
                           const std::string& riskPath = "data/risk_scores.csv",
                           const std::string& roadsPath = "data/road_network.csv") {
        Graph graph;

        // 1. Ingest static location details
        std::ifstream fStatic(staticPath);
        if (!fStatic.is_open()) {
            throw std::runtime_error("Cannot open static locations file: " + staticPath);
        }
        std::string line;
        std::getline(fStatic, line); // header
        while (std::getline(fStatic, line)) {
            if (line.empty()) continue;
            auto cols = Utils::parseCsvLine(line);
            if (cols.size() < 6) continue;
            Vertex v(cols[0], cols[1], std::stod(cols[2]), std::stod(cols[3]), std::stod(cols[4]));
            graph.addVertex(v);
        }

        // 2. Ingest Member 1 risk scores
        std::ifstream fRisk(riskPath);
        if (fRisk.is_open()) {
            std::getline(fRisk, line); // header
            while (std::getline(fRisk, line)) {
                if (line.empty()) continue;
                auto cols = Utils::parseCsvLine(line);
                if (cols.size() < 8) continue;
                Vertex* v = graph.getVertexMutable(cols[0]);
                if (v) {
                    v->updateRisk(std::stod(cols[6]), cols[7], std::stod(cols[4]), std::stod(cols[5]));
                }
            }
        }

        // 3. Ingest road network connections
        std::ifstream fRoads(roadsPath);
        if (!fRoads.is_open()) {
            throw std::runtime_error("Cannot open road network file: " + roadsPath);
        }
        std::getline(fRoads, line); // header
        while (std::getline(fRoads, line)) {
            if (line.empty()) continue;
            auto cols = Utils::parseCsvLine(line);
            if (cols.size() < 4) continue;
            std::string roadId = cols[0];
            std::string u = cols[1];
            std::string v = cols[2];
            double dist = std::stod(cols[3]);
            std::string hw = (cols.size() > 4) ? cols[4] : "";
            std::string rtype = (cols.size() > 5) ? cols[5] : "";
            std::string desc = (cols.size() > 6) ? cols[6] : "";
            graph.addEdge(Edge(roadId, u, v, dist, hw, rtype, desc), true);
        }

        graph.updateEdgeWeights();
        return graph;
    }
};

// ==============================================================================
// RESPONSIBILITY 7: ROUTE OUTPUT GENERATION (Frontend JSON)
// ==============================================================================
class JsonExporter {
public:
    static void exportRoutes(const Graph& graph,
                             const std::vector<std::pair<std::string, std::string>>& corridors,
                             const std::string& outputPath = "data/route_output.json") {
        std::ofstream out(outputPath);
        if (!out.is_open()) {
            throw std::runtime_error("Cannot write to route output file: " + outputPath);
        }

        out << "{\n";
        out << "  \"metadata\": {\n";
        out << "    \"system\": \"SlopeShield Intelligent Safe Route Engine\",\n";
        out << "    \"author\": \"Jahnvi Verma (Member 2)\",\n";
        out << "    \"implementation\": \"C++ OOP & Data Structures (Adjacency List + Min-Heap CLRS + Dijkstra)\",\n";
        out << "    \"weight_formula\": \"distance * (1 + 1.5 * edge_risk/100) + critical_penalty\",\n";
        out << "    \"generated_at\": \"" << Utils::getIsoTimestamp() << "\"\n";
        out << "  },\n";

        // Locations dictionary
        out << "  \"all_locations\": {\n";
        const auto& verts = graph.getVertices();
        size_t vi = 0;
        for (const auto& [id, v] : verts) {
            out << "    \"" << id << "\": {\n";
            out << "      \"location_id\": \"" << v.getId() << "\",\n";
            out << "      \"name\": \"" << v.getName() << "\",\n";
            out << "      \"lat\": " << v.getLat() << ",\n";
            out << "      \"lon\": " << v.getLon() << ",\n";
            out << "      \"elevation_m\": " << v.getElevation() << ",\n";
            out << "      \"risk_score\": " << std::fixed << std::setprecision(2) << v.getRiskScore() << ",\n";
            out << "      \"risk_level\": \"" << v.getRiskLevel() << "\",\n";
            out << "      \"static_score\": " << v.getStaticScore() << ",\n";
            out << "      \"dynamic_score\": " << v.getDynamicScore() << "\n";
            out << "    }" << (vi + 1 < verts.size() ? ",\n" : "\n");
            vi++;
        }
        out << "  },\n";

        // Precomputed Corridors
        out << "  \"routes\": {\n";
        for (size_t i = 0; i < corridors.size(); ++i) {
            const auto& [src, dst] = corridors[i];
            RouteResult shortest = DijkstraRouter::findPath(graph, src, dst, RoutingMode::SHORTEST);
            RouteResult safest = DijkstraRouter::findPath(graph, src, dst, RoutingMode::SAFEST);
            RouteComparison comp(shortest, safest);

            std::string key = src + "_to_" + dst;
            out << "    \"" << key << "\": {\n";
            out << "      \"source_id\": \"" << src << "\",\n";
            out << "      \"dest_id\": \"" << dst << "\",\n";
            out << "      \"is_identical\": " << (comp.isIdentical() ? "true" : "false") << ",\n";
            out << "      \"distance_diff_km\": " << std::fixed << std::setprecision(2) << comp.getDistanceDiffKm() << ",\n";
            out << "      \"cost_diff\": " << comp.getCostDiff() << ",\n";
            out << "      \"risk_reduction_pct\": " << comp.getRiskReductionPct() << ",\n";
            out << "      \"recommendation\": \"" << comp.getRecommendation() << "\",\n";

            auto printRoute = [&](const RouteResult& r, const std::string& objName, bool trailingComma) {
                out << "      \"" << objName << "\": {\n";
                out << "        \"total_distance_km\": " << r.totalDistanceKm << ",\n";
                out << "        \"total_risk_cost\": " << r.totalRiskCost << ",\n";
                out << "        \"average_risk_score\": " << r.averageRiskScore << ",\n";
                out << "        \"max_risk_level\": \"" << r.maxRiskLevel << "\",\n";
                out << "        \"path\": [";
                for (size_t p = 0; p < r.path.size(); ++p) {
                    out << "\"" << r.path[p] << "\"" << (p + 1 < r.path.size() ? ", " : "");
                }
                out << "],\n";
                out << "        \"coordinates\": [";
                for (size_t c = 0; c < r.coordinates.size(); ++c) {
                    out << "[" << r.coordinates[c].first << ", " << r.coordinates[c].second << "]"
                        << (c + 1 < r.coordinates.size() ? ", " : "");
                }
                out << "]\n";
                out << "      }" << (trailingComma ? ",\n" : "\n");
            };

            printRoute(shortest, "shortest_route", true);
            printRoute(safest, "safest_route", false);
            out << "    }" << (i + 1 < corridors.size() ? ",\n" : "\n");
        }
        out << "  }\n";
        out << "}\n";
    }
};

// ==============================================================================
// TEST ENGINE: Scenario Execution (tests/route_cases.csv)
// ==============================================================================
class RouteTester {
public:
    static int runAllTests(Graph& graph, const std::string& casesPath = "tests/route_cases.csv") {
        std::cout << "\n=========================================================================================================\n";
        std::cout << " EXECUTING MEMBER 2 (C++) ROUTE TESTS ACROSS RISK CONDITIONS (tests/route_cases.csv)\n";
        std::cout << "=========================================================================================================\n";
        std::cout << std::left << std::setw(32) << "Case ID" << " | "
                  << std::setw(12) << "Route" << " | "
                  << std::setw(28) << "Safest Path Got" << " | "
                  << std::setw(28) << "Expected Path" << " | Verdict\n";
        std::cout << "---------------------------------------------------------------------------------------------------------\n";

        std::ifstream fCases(casesPath);
        if (!fCases.is_open()) {
            std::cerr << "[ERROR] Cannot open test cases file: " << casesPath << "\n";
            return 1;
        }

        std::string line;
        std::getline(fCases, line); // header
        int fails = 0;

        auto formatPath = [](const std::vector<std::string>& nodes) {
            std::string s;
            for (size_t i = 0; i < nodes.size(); ++i) {
                s += nodes[i] + (i + 1 < nodes.size() ? "->" : "");
            }
            return s;
        };

        while (std::getline(fCases, line)) {
            if (line.empty()) continue;
            auto cols = Utils::parseCsvLine(line);
            if (cols.size() < 10) continue;

            std::string caseId = cols[0];
            std::string src = cols[1];
            std::string dst = cols[2];
            std::string ovType = cols[4];
            std::string ovTarget = cols[5];
            double ovScore = std::stod(cols[6]);
            std::string ovLevel = cols[7];
            std::string expShort = cols[8];
            std::string expSafe = cols[9];

            std::unordered_map<std::string, std::pair<double, std::string>> nodeOv;
            std::unordered_map<std::string, std::pair<double, std::string>> edgeOv;

            if (ovType == "NODE") {
                nodeOv[ovTarget] = {ovScore, ovLevel};
            } else if (ovType == "EDGE") {
                edgeOv[ovTarget] = {ovScore, ovLevel};
            }

            graph.updateEdgeWeights(SlopeShieldConfig::DEFAULT_ALPHA,
                                    SlopeShieldConfig::CRITICAL_PENALTY,
                                    nodeOv, edgeOv);

            RouteResult shortest = DijkstraRouter::findPath(graph, src, dst, RoutingMode::SHORTEST);
            RouteResult safest = DijkstraRouter::findPath(graph, src, dst, RoutingMode::SAFEST);

            std::string gotShort = formatPath(shortest.path);
            std::string gotSafe = formatPath(safest.path);

            bool ok = (gotShort == expShort && gotSafe == expSafe);
            if (!ok) fails++;

            std::string routeTitle = src + "->" + dst;
            std::cout << std::left << std::setw(32) << caseId << " | "
                      << std::setw(12) << routeTitle << " | "
                      << std::setw(28) << gotSafe << " | "
                      << std::setw(28) << expSafe << " | "
                      << (ok ? "PASS" : "FAIL") << "\n";
        }

        // Reset to standard baseline
        graph.updateEdgeWeights();
        std::cout << "=========================================================================================================\n";
        if (fails == 0) {
            std::cout << ">> ALL ROUTE TESTS PASSED (8/8). Algorithm successfully diverts around hazards in C++!\n\n";
        } else {
            std::cout << ">> " << fails << " ROUTE TEST(S) FAILED!\n\n";
        }
        return fails;
    }
};

// ==============================================================================
// PRESENTATION: Formatted Comparison Table
// ==============================================================================
static void printRouteComparisonTable(const Graph& graph,
                                      const std::vector<std::pair<std::string, std::string>>& corridors) {
    std::cout << "\n============================================================================================\n";
    std::cout << " SlopeShield Safe Route Engine (C++17 OOP & DSA) - Member 2 (Jahnvi Verma)\n";
    std::cout << "============================================================================================\n";
    std::cout << std::left << std::setw(14) << "Corridor" << " | "
              << std::setw(8) << "Mode" << " | "
              << std::setw(9) << "Distance" << " | "
              << std::setw(10) << "Risk Cost" << " | "
              << std::setw(8) << "Max Risk" << " | Selected Path\n";
    std::cout << "--------------------------------------------------------------------------------------------\n";

    auto formatPath = [](const std::vector<std::string>& nodes) {
        std::string s;
        for (size_t i = 0; i < nodes.size(); ++i) {
            s += nodes[i] + (i + 1 < nodes.size() ? " -> " : "");
        }
        return s;
    };

    for (const auto& [src, dst] : corridors) {
        RouteResult shortest = DijkstraRouter::findPath(graph, src, dst, RoutingMode::SHORTEST);
        RouteResult safest = DijkstraRouter::findPath(graph, src, dst, RoutingMode::SAFEST);

        std::string title = src + " -> " + dst;
        std::cout << std::left << std::setw(14) << title << " | "
                  << std::setw(8) << "Shortest" << " | "
                  << std::fixed << std::setprecision(1) << std::setw(6) << shortest.totalDistanceKm << " km | "
                  << std::setw(10) << shortest.totalRiskCost << " | "
                  << std::setw(8) << shortest.maxRiskLevel << " | "
                  << formatPath(shortest.path) << "\n";

        std::cout << std::left << std::setw(14) << "" << " | "
                  << std::setw(8) << "Safest" << " | "
                  << std::fixed << std::setprecision(1) << std::setw(6) << safest.totalDistanceKm << " km | "
                  << std::setw(10) << safest.totalRiskCost << " | "
                  << std::setw(8) << safest.maxRiskLevel << " | "
                  << formatPath(safest.path) << "\n";
        std::cout << "--------------------------------------------------------------------------------------------\n";
    }
}

// ==============================================================================
// MAIN ENTRY POINT
// ==============================================================================
int main(int argc, char* argv[]) {
    try {
        Graph graph = DataLoader::loadGraph("data/locations_static.csv",
                                            "data/risk_scores.csv",
                                            "data/road_network.csv");

        std::vector<std::pair<std::string, std::string>> standardCorridors = {
            {"RISH", "BADR"}, {"RISH", "KEDN"}, {"RISH", "GANG"},
            {"KEDN", "BADR"}, {"RISH", "UTTK"}, {"DEHR", "MUSS"}, {"CHAM", "MALP"}
        };

        // CLI argument handling
        bool runTest = false;
        std::string srcQuery = "";
        std::string dstQuery = "";

        for (int i = 1; i < argc; ++i) {
            std::string arg = argv[i];
            if (arg == "--test") {
                runTest = true;
            } else if (arg == "--source" && i + 1 < argc) {
                srcQuery = argv[++i];
            } else if (arg == "--dest" && i + 1 < argc) {
                dstQuery = argv[++i];
            }
        }

        if (runTest) {
            return RouteTester::runAllTests(graph, "tests/route_cases.csv");
        }

        if (!srcQuery.empty() && !dstQuery.empty()) {
            std::transform(srcQuery.begin(), srcQuery.end(), srcQuery.begin(), ::toupper);
            std::transform(dstQuery.begin(), dstQuery.end(), dstQuery.begin(), ::toupper);

            const Vertex* sV = graph.getVertex(srcQuery);
            const Vertex* dV = graph.getVertex(dstQuery);
            if (!sV || !dV) {
                std::cerr << "Invalid source (" << srcQuery << ") or destination (" << dstQuery << ")\n";
                return 1;
            }

            RouteResult shortest = DijkstraRouter::findPath(graph, srcQuery, dstQuery, RoutingMode::SHORTEST);
            RouteResult safest = DijkstraRouter::findPath(graph, srcQuery, dstQuery, RoutingMode::SAFEST);
            RouteComparison comp(shortest, safest);

            auto formatPath = [](const std::vector<std::string>& nodes) {
                std::string s;
                for (size_t i = 0; i < nodes.size(); ++i) {
                    s += nodes[i] + (i + 1 < nodes.size() ? " -> " : "");
                }
                return s;
            };

            std::cout << "\n=================================================================\n";
            std::cout << " ROUTE QUERY (C++ OOP): " << srcQuery << " (" << sV->getName() << ") -> "
                      << dstQuery << " (" << dV->getName() << ")\n";
            std::cout << "=================================================================\n";
            std::cout << "Shortest Distance Path : " << formatPath(shortest.path) << "\n";
            std::cout << "  Distance : " << std::fixed << std::setprecision(1) << shortest.totalDistanceKm
                      << " km | Cost: " << shortest.totalRiskCost << " | Hazard: " << shortest.maxRiskLevel << "\n";
            std::cout << "Safest Risk Path       : " << formatPath(safest.path) << "\n";
            std::cout << "  Distance : " << std::fixed << std::setprecision(1) << safest.totalDistanceKm
                      << " km | Cost: " << safest.totalRiskCost << " | Hazard: " << safest.maxRiskLevel << "\n";
            std::cout << "Recommendation         : " << comp.getRecommendation() << "\n";
            std::cout << "=================================================================\n\n";
            return 0;
        }

        // Default: Export frontend JSON and display comparison table
        JsonExporter::exportRoutes(graph, standardCorridors, "data/route_output.json");
        std::cout << "Generated frontend route output successfully: data/route_output.json\n";

        printRouteComparisonTable(graph, standardCorridors);
        std::cout << "\nTip: Run with '--test' to execute all 8 risk scenario tests.\n";
        return 0;

    } catch (const std::exception& ex) {
        std::cerr << "[CRITICAL ERROR] " << ex.what() << "\n";
        return 1;
    }
}
