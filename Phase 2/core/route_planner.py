"""
================================================================================
SlopeShield: Intelligent Landslide Risk & Safe Route System
OOP Route Planner & DSA Graph Hierarchy (Member 3 Architecture integrating Member 2 DSA)
Authors: Jahnvi Verma (Member 2: Graph & Dijkstra) & Anshika Gaur (Member 3: Integration)
================================================================================

This module encapsulates Member 2's DSA routing architecture in an OOP hierarchy:
1. BaseRoutePlanner: Abstract Base Class defining pathfinding algorithms.
2. MinPriorityQueue: Custom Min-Heap Priority Queue from scratch (CLRS design).
3. RoadGraph: Graph representation using an Adjacency List with road geometry preservation.
4. DijkstraRoutePlanner: Concrete implementation of Dijkstra's algorithm for
   Shortest Distance and Safest Risk-Weighted paths, concatenating detailed road geometry.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Any
from core.models import Location, RoadSegment, RouteResult, RouteComparison


class MinPriorityQueue:
    """
    Min-Heap Priority Queue implemented from scratch based on CLRS design.
    Maintains min-heap invariant: parent(i) <= children(2i+1, 2i+2).
    Guarantees O(log N) push and O(log N) extract-min (pop).
    """
    def __init__(self):
        self._heap: List[Tuple[float, int, Any]] = []
        self._counter: int = 0

    def push(self, priority: float, item: Any) -> None:
        """Insert an item with an associated numeric priority into the min-heap."""
        entry = (float(priority), self._counter, item)
        self._counter += 1
        self._heap.append(entry)
        self._sift_up(len(self._heap) - 1)

    def pop(self) -> Tuple[float, Any]:
        """Extract and return the element with the minimum priority: (priority, item)."""
        if not self._heap:
            raise IndexError("pop from empty MinPriorityQueue")
        min_entry = self._heap[0]
        last_entry = self._heap.pop()
        if self._heap:
            self._heap[0] = last_entry
            self._sift_down(0)
        return (min_entry[0], min_entry[2])

    def peek(self) -> Tuple[float, Any]:
        if not self._heap:
            raise IndexError("peek from empty MinPriorityQueue")
        return (self._heap[0][0], self._heap[0][2])

    def is_empty(self) -> bool:
        return len(self._heap) == 0

    def __len__(self) -> int:
        return len(self._heap)

    def _sift_up(self, index: int) -> None:
        while index > 0:
            parent = (index - 1) // 2
            if self._heap[index][0] < self._heap[parent][0]:
                self._heap[index], self._heap[parent] = self._heap[parent], self._heap[index]
                index = parent
            else:
                break

    def _sift_down(self, index: int) -> None:
        n = len(self._heap)
        while True:
            smallest = index
            left = 2 * index + 1
            right = 2 * index + 2

            if left < n and self._heap[left][0] < self._heap[smallest][0]:
                smallest = left
            if right < n and self._heap[right][0] < self._heap[smallest][0]:
                smallest = right

            if smallest != index:
                self._heap[index], self._heap[smallest] = self._heap[smallest], self._heap[index]
                index = smallest
            else:
                break


class RoadGraph:
    """
    Graph data structure representing the Uttarakhand road network.
    Uses an Adjacency List for space efficiency and fast neighbor traversal.
    Maintains intermediate polyline coordinates for all road corridors.
    """
    def __init__(self):
        self._vertices: Dict[str, Location] = {}
        self._adj: Dict[str, List[RoadSegment]] = {}

    @property
    def vertices(self) -> Dict[str, Location]:
        return self._vertices

    @property
    def adj(self) -> Dict[str, List[RoadSegment]]:
        return self._adj

    def add_location(self, location: Location) -> None:
        """Add a location vertex to the graph."""
        self._vertices[location.id] = location
        if location.id not in self._adj:
            self._adj[location.id] = []

    def add_road(self, road: RoadSegment, bidirectional: bool = True) -> None:
        """Add a road corridor edge to the graph, preserving reverse geometry."""
        if road.u not in self._vertices or road.v not in self._vertices:
            raise KeyError(f"Vertices {road.u} or {road.v} must be added to graph before adding road.")

        self._adj[road.u].append(road)

        if bidirectional:
            rev_geom = [list(pt) for pt in reversed(road.geometry)] if road.geometry else []
            rev_road = RoadSegment(
                road_id=f"{road.road_id}_rev",
                u=road.v,
                v=road.u,
                distance_km=road.distance_km,
                highway=road.highway,
                road_type=road.road_type,
                description=road.description,
                geometry=rev_geom,
                has_verified_geometry=road.has_verified_geometry
            )
            self._adj[road.v].append(rev_road)

    def get_location(self, location_id: str) -> Optional[Location]:
        return self._vertices.get(location_id)

    def get_neighbors(self, location_id: str) -> List[RoadSegment]:
        return self._adj.get(location_id, [])

    def get_edge(self, u: str, v: str) -> Optional[RoadSegment]:
        for edge in self.get_neighbors(u):
            if edge.v == v:
                return edge
        return None

    def update_edge_weights(self, alpha: float = 1.5, critical_penalty: float = 1000.0,
                            node_overrides: Optional[Dict[str, Tuple[float, str]]] = None,
                            edge_overrides: Optional[Dict[str, Tuple[float, str]]] = None) -> None:
        """
        Calculates risk-based weights on all edges.
        Incorporates custom node or edge overrides for hazard simulations.
        """
        node_overrides = node_overrides or {}
        edge_overrides = edge_overrides or {}

        for u, edges in self._adj.items():
            u_loc = self._vertices.get(u)
            for edge in edges:
                v_loc = self._vertices.get(edge.v)
                if not u_loc or not v_loc:
                    continue

                clean_id = edge.road_id.replace("_rev", "")
                custom_override = edge_overrides.get(clean_id)

                temp_u = u_loc
                temp_v = v_loc
                if u in node_overrides or edge.v in node_overrides:
                    temp_u = Location(u_loc.id, u_loc.name, u_loc.lat, u_loc.lon)
                    temp_v = Location(v_loc.id, v_loc.name, v_loc.lat, v_loc.lon)

                    u_score = node_overrides[u][0] if u in node_overrides else u_loc.risk.total_score
                    u_lvl = node_overrides[u][1] if u in node_overrides else u_loc.risk.risk_level
                    temp_u.set_risk(u_loc.risk.static_score, u_loc.risk.dynamic_score, u_score, u_lvl)

                    v_score = node_overrides[edge.v][0] if edge.v in node_overrides else v_loc.risk.total_score
                    v_lvl = node_overrides[edge.v][1] if edge.v in node_overrides else v_loc.risk.risk_level
                    temp_v.set_risk(v_loc.risk.static_score, v_loc.risk.dynamic_score, v_score, v_lvl)

                edge.calculate_weight(temp_u, temp_v, alpha, critical_penalty, custom_override)


class BaseRoutePlanner(ABC):
    """Abstract Base Class for routing algorithms."""

    @abstractmethod
    def find_path(self, graph: RoadGraph, source: str, destination: str, mode: str = "safest") -> RouteResult:
        """Find the optimal route between source and destination in the graph."""
        pass


class DijkstraRoutePlanner(BaseRoutePlanner):
    """
    Dijkstra's Algorithm Route Planner utilizing the custom MinPriorityQueue.
    Supports 'safest' (risk-weighted) and 'shortest' (distance) modes.
    Concatenates complete, verified road geometry in strict traversal order.
    """

    def find_path(self, graph: RoadGraph, source: str, destination: str, mode: str = "safest") -> RouteResult:
        result = RouteResult(source, destination, mode)

        if not graph.vertices:
            result.error_message = "Graph is empty."
            return result

        if source not in graph.vertices or destination not in graph.vertices:
            result.error_message = f"Invalid location: source '{source}' or destination '{destination}' does not exist in network."
            return result

        if source == destination:
            v = graph.vertices[source]
            result.found = True
            result.path = [source]
            result.path_names = [v.name]
            result.coordinates = [[v.lat, v.lon]]
            result.has_verified_geometry = True
            result.is_schematic = False
            result.total_distance_km = 0.0
            result.total_risk_cost = 0.0
            result.average_risk_score = v.risk.total_score
            result.max_risk_level = v.risk.risk_level
            return result

        dist: Dict[str, float] = {nid: float('inf') for nid in graph.vertices}
        parent: Dict[str, Optional[str]] = {nid: None for nid in graph.vertices}
        edge_used: Dict[str, Optional[RoadSegment]] = {nid: None for nid in graph.vertices}
        visited = set()

        dist[source] = 0.0
        pq = MinPriorityQueue()
        pq.push(0.0, source)

        while not pq.is_empty():
            curr_dist, u = pq.pop()

            if u in visited:
                continue
            visited.add(u)

            if u == destination:
                break

            if curr_dist > dist[u]:
                continue

            for edge in graph.get_neighbors(u):
                v = edge.v
                if v in visited:
                    continue

                weight = edge.risk_cost if mode == "safest" else edge.distance_km
                if weight < 0.0:
                    weight = 0.0  # Dijkstra invariant: non-negative weights
                new_dist = curr_dist + weight

                if new_dist < dist[v]:
                    dist[v] = new_dist
                    parent[v] = u
                    edge_used[v] = edge
                    pq.push(new_dist, v)

        if dist[destination] == float('inf'):
            result.found = False
            result.error_message = f"Destination '{destination}' is unreachable from source '{source}'."
            return result

        # Backtrack path
        curr: Optional[str] = destination
        path_nodes: List[str] = []
        path_edges: List[RoadSegment] = []
        while curr is not None:
            path_nodes.append(curr)
            e = edge_used.get(curr)
            if e is not None:
                path_edges.append(e)
            curr = parent.get(curr)

        path_nodes.reverse()
        path_edges.reverse()

        result.found = True
        result.path = path_nodes
        result.path_names = [graph.vertices[nid].name for nid in path_nodes]

        # Concatenate complete road geometry in exact traversal order
        concatenated_coords: List[List[float]] = []
        all_verified = len(path_edges) > 0

        tot_dist = 0.0
        tot_cost = 0.0
        risk_scores = []
        levels_order = {"Low": 0, "Moderate": 1, "High": 2, "Critical": 3}
        max_level_val = 0
        segments = []

        for e in path_edges:
            tot_dist += e.distance_km
            tot_cost += e.risk_cost
            u_loc = graph.vertices[e.u]
            v_loc = graph.vertices[e.v]
            risk_scores.append(e.edge_risk_score)

            for lvl in [u_loc.risk.risk_level, v_loc.risk.risk_level, e.edge_risk_level]:
                max_level_val = max(max_level_val, levels_order.get(lvl, 0))

            # Segment geometry traversal
            if e.geometry and len(e.geometry) > 1:
                e_coords = [list(pt) for pt in e.geometry]
            else:
                e_coords = [[u_loc.lat, u_loc.lon], [v_loc.lat, v_loc.lon]]
                all_verified = False

            if not e.has_verified_geometry:
                all_verified = False

            # Concatenate coordinates avoiding duplicate junction point
            if not concatenated_coords:
                concatenated_coords.extend(e_coords)
            else:
                if e_coords and concatenated_coords[-1] == e_coords[0]:
                    concatenated_coords.extend(e_coords[1:])
                else:
                    concatenated_coords.extend(e_coords)

            segments.append({
                "road_id": e.road_id,
                "from_id": e.u,
                "from_name": u_loc.name,
                "to_id": e.v,
                "to_name": v_loc.name,
                "highway": e.highway,
                "road_type": e.road_type,
                "distance_km": e.distance_km,
                "edge_risk_score": e.edge_risk_score,
                "edge_risk_level": e.edge_risk_level,
                "risk_multiplier": e.risk_multiplier,
                "risk_cost": e.risk_cost,
                "from_coords": [u_loc.lat, u_loc.lon],
                "to_coords": [v_loc.lat, v_loc.lon],
                "has_verified_geometry": e.has_verified_geometry,
                "geometry": e_coords
            })

        if not concatenated_coords:
            concatenated_coords = [[graph.vertices[nid].lat, graph.vertices[nid].lon] for nid in path_nodes]

        inv_levels = {0: "Low", 1: "Moderate", 2: "High", 3: "Critical"}
        result.coordinates = concatenated_coords
        result.has_verified_geometry = all_verified
        result.is_schematic = not all_verified
        result.total_distance_km = round(tot_dist, 2)
        result.total_risk_cost = round(tot_cost, 2)
        result.average_risk_score = round(sum(risk_scores) / len(risk_scores), 2) if risk_scores else 0.0
        result.max_risk_level = inv_levels.get(max_level_val, "Low")
        result.segments = segments

        return result

    def compare_routes(self, graph: RoadGraph, source: str, destination: str) -> RouteComparison:
        """Compute both Shortest Distance and Safest Risk paths and return their comparison."""
        shortest = self.find_path(graph, source, destination, mode="shortest")
        safest = self.find_path(graph, source, destination, mode="safest")
        return RouteComparison(shortest, safest)
