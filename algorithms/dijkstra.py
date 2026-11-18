"""
Dijkstra's Shortest Path Algorithm (Link State Routing).
Pure Python implementation with step-by-step execution traces and routing table generation.
Assumes a complete view of network topology (Link State Database / LSDB).
"""

import math
from typing import Dict, List, Any, Optional
from network.topology import NetworkTopology


def reconstruct_path(predecessors: Dict[str, Optional[str]], source: str, target: str) -> List[str]:
    """Reconstruct complete node path from source to target using predecessor map."""
    if source == target:
        return [source]
    if predecessors.get(target) is None:
        return []
    
    path = []
    curr = target
    visited = set()
    while curr is not None:
        if curr in visited:
            # Prevent infinite loop if predecessor has cycles
            break
        visited.add(curr)
        path.append(curr)
        if curr == source:
            break
        curr = predecessors.get(curr)
    
    if not path or path[-1] != source:
        return []
    path.reverse()
    return path


def determine_next_hop(path: List[str]) -> str:
    """
    Determine the next hop router from the source along the shortest path.
    - If path has only source: '-' (Local)
    - If path has length >= 2: the second router in the path
    - If empty: '-' (Unreachable)
    """
    if not path or len(path) == 0:
        return "-"
    if len(path) == 1:
        return "-"
    return path[1]


def run_dijkstra(topology: NetworkTopology, source_node: str) -> Dict[str, Any]:
    """
    Execute Dijkstra's Shortest Path Algorithm on the topology.
    Returns:
    - routing_table: list of destination records with cost, next_hop, full path
    - steps: detailed trace of each step for step-by-step animation and educational UI
    - shortest_paths: dict of target -> list of nodes in path
    - statistics: nodes count, edge count, visited count, updates count
    """
    nodes = topology.get_nodes()
    source = str(source_node).strip().upper()
    
    if not nodes:
        raise ValueError("Network topology is empty. Please add routers first.")
    if source not in nodes:
        raise ValueError(f"Source router '{source}' does not exist in network topology.")
    
    # Check for negative edge weights (Dijkstra requires non-negative edge weights)
    for edge in topology.get_edges():
        if edge["weight"] < 0:
            raise ValueError(f"Negative edge weight detected on connection ({edge['source']}-{edge['target']}: {edge['weight']}). "
                             "Dijkstra's Algorithm requires non-negative edge weights.")
    
    # Initial state
    distances: Dict[str, float] = {node: float("inf") for node in nodes}
    distances[source] = 0.0
    predecessors: Dict[str, Optional[str]] = {node: None for node in nodes}
    unvisited: set = set(nodes)
    visited: List[str] = []
    
    steps: List[Dict[str, Any]] = []
    update_count = 0

    def serialize_distances(dist_map: Dict[str, float]) -> Dict[str, Any]:
        return {k: ("inf" if math.isinf(v) else (int(v) if v.is_integer() else round(v, 2))) 
                for k, v in dist_map.items()}

    # Step 0: Initialization
    steps.append({
        "step": 0,
        "type": "init",
        "description": f"Initialized Link State Database. Set tentative cost to source router {source} to 0, all other routers to ∞.",
        "current_node": source,
        "visited": list(visited),
        "unvisited": sorted(list(unvisited)),
        "distances": serialize_distances(distances),
        "predecessors": dict(predecessors),
        "highlight_nodes": [source],
        "highlight_edges": [],
        "tree_edges": []
    })

    while unvisited:
        # Select unvisited node with smallest distance
        current_node = min(unvisited, key=lambda node: distances[node])
        current_dist = distances[current_node]

        # If min distance is infinity, remaining unvisited nodes are disconnected
        if math.isinf(current_dist):
            steps.append({
                "step": len(steps),
                "type": "unreachable_partition",
                "description": f"Remaining unvisited routers {sorted(list(unvisited))} are disconnected from source {source}.",
                "current_node": None,
                "visited": list(visited),
                "unvisited": sorted(list(unvisited)),
                "distances": serialize_distances(distances),
                "predecessors": dict(predecessors),
                "highlight_nodes": [],
                "highlight_edges": [],
                "tree_edges": _get_current_tree_edges(predecessors, source)
            })
            break

        # Mark current node as visited
        unvisited.remove(current_node)
        visited.append(current_node)

        steps.append({
            "step": len(steps),
            "type": "select_min",
            "description": f"Extracted router {current_node} with minimum tentative distance ({int(current_dist) if current_dist.is_integer() else current_dist}). Marked as permanently settled/visited.",
            "current_node": current_node,
            "visited": list(visited),
            "unvisited": sorted(list(unvisited)),
            "distances": serialize_distances(distances),
            "predecessors": dict(predecessors),
            "highlight_nodes": [current_node],
            "highlight_edges": [],
            "tree_edges": _get_current_tree_edges(predecessors, source)
        })

        # Relax incident edges to unvisited neighbors
        neighbors = topology.get_neighbors(current_node)
        for neighbor, weight in sorted(neighbors.items()):
            if neighbor in unvisited:
                tentative_dist = current_dist + weight
                prev_dist = distances[neighbor]
                
                if tentative_dist < prev_dist:
                    distances[neighbor] = tentative_dist
                    predecessors[neighbor] = current_node
                    update_count += 1
                    
                    prev_str = "∞" if math.isinf(prev_dist) else str(int(prev_dist) if prev_dist.is_integer() else prev_dist)
                    new_str = str(int(tentative_dist) if tentative_dist.is_integer() else tentative_dist)
                    
                    steps.append({
                        "step": len(steps),
                        "type": "relax_edge",
                        "description": f"Relaxed edge ({current_node} -> {neighbor}): New path cost ({int(current_dist) if current_dist.is_integer() else current_dist} + {int(weight) if float(weight).is_integer() else weight} = {new_str}) is lower than previous cost ({prev_str}). Updated predecessor of {neighbor} to {current_node}.",
                        "current_node": current_node,
                        "neighbor": neighbor,
                        "edge_weight": weight,
                        "visited": list(visited),
                        "unvisited": sorted(list(unvisited)),
                        "distances": serialize_distances(distances),
                        "predecessors": dict(predecessors),
                        "highlight_nodes": [current_node, neighbor],
                        "highlight_edges": [{"source": current_node, "target": neighbor, "status": "relaxed"}],
                        "tree_edges": _get_current_tree_edges(predecessors, source)
                    })
                else:
                    prev_str = str(int(prev_dist) if prev_dist.is_integer() else prev_dist)
                    tent_str = str(int(tentative_dist) if tentative_dist.is_integer() else tentative_dist)
                    steps.append({
                        "step": len(steps),
                        "type": "examine_neighbor",
                        "description": f"Checked edge ({current_node} -> {neighbor}): Tentative cost ({tent_str}) is not strictly better than existing known cost ({prev_str}). No update performed.",
                        "current_node": current_node,
                        "neighbor": neighbor,
                        "edge_weight": weight,
                        "visited": list(visited),
                        "unvisited": sorted(list(unvisited)),
                        "distances": serialize_distances(distances),
                        "predecessors": dict(predecessors),
                        "highlight_nodes": [current_node, neighbor],
                        "highlight_edges": [{"source": current_node, "target": neighbor, "status": "examined"}],
                        "tree_edges": _get_current_tree_edges(predecessors, source)
                    })

    # Construct final routing table and shortest paths
    routing_table = []
    shortest_paths = {}

    for dest in sorted(nodes):
        cost = distances[dest]
        cost_val = None if math.isinf(cost) else (int(cost) if cost.is_integer() else round(cost, 2))
        cost_display = "∞" if math.isinf(cost) else str(cost_val)
        
        path = reconstruct_path(predecessors, source, dest)
        shortest_paths[dest] = path
        next_hop = determine_next_hop(path)

        path_display = " -> ".join(path) if path else "Unreachable"

        routing_table.append({
            "router": source,
            "destination": dest,
            "next_hop": next_hop,
            "cost": cost_val,
            "cost_display": cost_display,
            "path": path_display,
            "path_nodes": path
        })

    # Final summary step
    steps.append({
        "step": len(steps),
        "type": "completed",
        "description": f"Dijkstra's Algorithm completed for source router {source}. Shortest Path Tree (SPT) built. Routing table generated.",
        "current_node": source,
        "visited": list(visited),
        "unvisited": sorted(list(unvisited)),
        "distances": serialize_distances(distances),
        "predecessors": dict(predecessors),
        "highlight_nodes": [source],
        "highlight_edges": [],
        "tree_edges": _get_current_tree_edges(predecessors, source)
    })

    return {
        "source": source,
        "algorithm": "Dijkstra (Link State)",
        "routing_table": routing_table,
        "shortest_paths": shortest_paths,
        "steps": steps,
        "statistics": {
            "num_routers": len(nodes),
            "num_connections": len(topology.get_edges()),
            "total_steps": len(steps),
            "total_updates": update_count,
            "visited_count": len(visited),
            "convergence_status": "Converged (Optimal shortest paths found)"
        }
    }


def _get_current_tree_edges(predecessors: Dict[str, Optional[str]], source: str) -> List[Dict[str, str]]:
    """Return all edges currently belonging to the shortest path tree."""
    edges = []
    for node, pred in predecessors.items():
        if pred is not None:
            edges.append({"source": pred, "target": node})
    return edges
