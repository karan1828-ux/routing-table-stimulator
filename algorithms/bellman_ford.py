"""
Distributed Distance-Vector Routing Algorithm (Iterative Bellman-Ford).
Simulates genuine asynchronous/synchronous router-to-router distance-vector exchanges.
Each router maintains its own routing table and distance vector:
D_x(y) = min_v [ c(x, v) + D_v(y) ]
"""

import math
from typing import Dict, List, Any, Optional, Tuple
from network.topology import NetworkTopology


def run_distance_vector(topology: NetworkTopology, source_node: Optional[str] = None, max_iterations: int = 50) -> Dict[str, Any]:
    """
    Execute distributed iterative Distance-Vector Routing on the topology.
    - Each router maintains local routing table: {dest: (cost, next_hop)}
    - In each iteration, routers send their distance vectors to direct neighbors.
    - Neighbors recompute optimal paths using Bellman-Ford update equation.
    - Records detailed exchanges, table updates, and iteration snapshots.
    """
    nodes = topology.get_nodes()
    if not nodes:
        raise ValueError("Network topology is empty. Please add routers first.")
    
    if source_node is not None:
        source_node = str(source_node).strip().upper()
        if source_node not in nodes:
            raise ValueError(f"Source router '{source_node}' does not exist.")

    # Validate non-negative weights for basic routing
    for edge in topology.get_edges():
        if edge["weight"] < 0:
            raise ValueError(f"Negative edge weight detected on connection ({edge['source']}-{edge['target']}: {edge['weight']}). "
                             "Standard Distance Vector assumes positive costs.")

    # Initialize router states
    # router_tables[r][dest] = {"cost": float, "next_hop": str or None}
    router_tables: Dict[str, Dict[str, Dict[str, Any]]] = {}
    # neighbor_vectors[r][neighbor][dest] = cost
    neighbor_vectors: Dict[str, Dict[str, Dict[str, float]]] = {}

    for r in nodes:
        router_tables[r] = {}
        neighbor_vectors[r] = {}
        neighbors = topology.get_neighbors(r)
        
        for dest in nodes:
            if dest == r:
                router_tables[r][dest] = {"cost": 0.0, "next_hop": "-"}
            elif dest in neighbors:
                router_tables[r][dest] = {"cost": float(neighbors[dest]), "next_hop": dest}
            else:
                router_tables[r][dest] = {"cost": float("inf"), "next_hop": "-"}

    def format_cost(c: float) -> Any:
        if math.isinf(c):
            return "∞"
        return int(c) if c.is_integer() else round(c, 2)

    def extract_dv(r: str) -> Dict[str, Any]:
        """Extract distance vector D_r(*) for router r."""
        return {dest: format_cost(router_tables[r][dest]["cost"]) for dest in nodes}

    def take_global_snapshot(iteration_num: int, description: str, exchanges: List[Dict[str, Any]], updates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Capture global network state at current iteration."""
        tables_snapshot = {}
        for r in nodes:
            tables_snapshot[r] = []
            for dest in sorted(nodes):
                entry = router_tables[r][dest]
                cost = entry["cost"]
                cost_val = None if math.isinf(cost) else (int(cost) if cost.is_integer() else round(cost, 2))
                
                # Trace forwarding path across routers
                fwd_path = _trace_forwarding_path(router_tables, r, dest, nodes)
                path_str = " -> ".join(fwd_path) if fwd_path else ("Local" if r == dest else "Unreachable")

                tables_snapshot[r].append({
                    "router": r,
                    "destination": dest,
                    "next_hop": entry["next_hop"],
                    "cost": cost_val,
                    "cost_display": format_cost(cost),
                    "path": path_str,
                    "path_nodes": fwd_path
                })
        
        return {
            "iteration": iteration_num,
            "description": description,
            "tables": tables_snapshot,
            "distance_vectors": {r: extract_dv(r) for r in nodes},
            "exchanges": exchanges,
            "updates": updates
        }

    iterations_trace: List[Dict[str, Any]] = []
    total_updates = 0

    # Iteration 0: Initial state before any neighbor exchanges
    init_desc = "Initialization (Iteration 0): Each router initializes routing table with direct link costs and sets non-neighbors to ∞."
    iterations_trace.append(take_global_snapshot(0, init_desc, [], []))

    iteration = 0
    converged = False

    while iteration < max_iterations:
        iteration += 1
        round_exchanges: List[Dict[str, Any]] = []
        round_updates: List[Dict[str, Any]] = []
        has_changes = False

        # Phase 1: Exchange - Each router sends its DV to directly connected neighbors
        for sender in nodes:
            sender_dv = {dest: router_tables[sender][dest]["cost"] for dest in nodes}
            neighbors = topology.get_neighbors(sender)
            for recipient in sorted(neighbors.keys()):
                # Recipient receives DV from sender
                if recipient not in neighbor_vectors:
                    neighbor_vectors[recipient] = {}
                neighbor_vectors[recipient][sender] = dict(sender_dv)
                
                round_exchanges.append({
                    "from": sender,
                    "to": recipient,
                    "vector": {d: format_cost(c) for d, c in sender_dv.items()},
                    "summary": f"Router {sender} sent its Distance Vector to neighbor {recipient}"
                })

        # Phase 2: Compute - Each router evaluates Bellman-Ford update equation
        # D_x(y) = min_v [ c(x, v) + D_v(y) ]
        for r in nodes:
            neighbors = topology.get_neighbors(r)
            if not neighbors:
                continue

            for dest in nodes:
                if dest == r:
                    continue
                
                old_cost = router_tables[r][dest]["cost"]
                old_next_hop = router_tables[r][dest]["next_hop"]

                best_cost = float("inf")
                best_next_hop = "-"

                for neighbor, link_cost in sorted(neighbors.items()):
                    # Cost via neighbor = link_cost + neighbor's distance to dest
                    neighbor_dist_to_dest = neighbor_vectors.get(r, {}).get(neighbor, {}).get(dest, float("inf"))
                    total_via_neighbor = link_cost + neighbor_dist_to_dest

                    if total_via_neighbor < best_cost:
                        best_cost = total_via_neighbor
                        best_next_hop = neighbor

                # Check if this is an improvement or an update through the same next hop
                if not math.isclose(best_cost, old_cost, abs_tol=1e-5) or (best_next_hop != old_next_hop and not math.isinf(best_cost)):
                    router_tables[r][dest]["cost"] = best_cost
                    router_tables[r][dest]["next_hop"] = best_next_hop
                    has_changes = True
                    total_updates += 1

                    round_updates.append({
                        "router": r,
                        "destination": dest,
                        "old_cost": format_cost(old_cost),
                        "new_cost": format_cost(best_cost),
                        "old_next_hop": old_next_hop,
                        "new_next_hop": best_next_hop,
                        "reason": f"Router {r} updated route to {dest} via {best_next_hop}: cost changed from {format_cost(old_cost)} to {format_cost(best_cost)}."
                    })

        desc = (f"Iteration {iteration}: Routers exchanged distance vectors and updated routing tables. "
                f"({len(round_updates)} route updates detected)." if has_changes else 
                f"Iteration {iteration}: Routing tables stabilized. No distance updates occurred. Converged!")

        iterations_trace.append(take_global_snapshot(iteration, desc, round_exchanges, round_updates))

        if not has_changes:
            converged = True
            break

    # Build primary result
    final_snapshot = iterations_trace[-1]
    
    # If a specific source router was requested, return its final routing table as primary
    primary_source = source_node if source_node else nodes[0]
    primary_table = final_snapshot["tables"].get(primary_source, [])

    return {
        "source": primary_source,
        "algorithm": "Bellman-Ford (Distance Vector)",
        "converged": converged,
        "iterations_count": len(iterations_trace) - 1,
        "total_updates": total_updates,
        "iterations": iterations_trace,
        "routing_table": primary_table,
        "all_routing_tables": final_snapshot["tables"],
        "statistics": {
            "num_routers": len(nodes),
            "num_connections": len(topology.get_edges()),
            "iterations_to_converge": len(iterations_trace) - 1,
            "total_route_updates": total_updates,
            "convergence_status": "Converged" if converged else "Max iterations reached (Non-converged)"
        }
    }


def _trace_forwarding_path(tables: Dict[str, Dict[str, Dict[str, Any]]], source: str, dest: str, all_nodes: List[str]) -> List[str]:
    """Reconstruct packet forwarding path by following next-hop pointers across routers."""
    if source == dest:
        return [source]
    
    path = [source]
    curr = source
    visited = set([source])

    while curr != dest:
        entry = tables.get(curr, {}).get(dest)
        if not entry:
            return []
        
        next_hop = entry.get("next_hop")
        if not next_hop or next_hop == "-" or next_hop not in all_nodes:
            return []
        
        if next_hop in visited:
            # Routing loop detected!
            path.append(f"{next_hop} (Loop)")
            return path
        
        visited.add(next_hop)
        path.append(next_hop)
        curr = next_hop

    return path
