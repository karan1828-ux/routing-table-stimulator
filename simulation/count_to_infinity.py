"""
Count-to-Infinity Problem Simulation Module.
Demonstrates the classical routing loop phenomenon in Distance Vector protocols
and illustrates prevention mechanisms: Split Horizon, Poison Reverse, and Route Poisoning.
"""

import math
from typing import Dict, List, Any, Optional
from network.topology import NetworkTopology


def simulate_count_to_infinity(
    topology: Optional[NetworkTopology] = None,
    failed_link: Optional[tuple] = None,
    destination: Optional[str] = None,
    mode: str = "standard",
    infinity_threshold: int = 16,
    max_iterations: int = 30
) -> Dict[str, Any]:
    """
    Simulate Count-to-Infinity and compare with Split Horizon / Poison Reverse.
    
    Parameters:
    - topology: NetworkTopology instance (defaults to classic A - B - C - DEST line)
    - failed_link: (u, v) edge that gets severed (defaults to C - DEST)
    - destination: destination router that becomes disconnected (defaults to DEST)
    - mode: 'standard' | 'split_horizon' | 'poison_reverse'
    - infinity_threshold: metric threshold treated as infinity (default 16, RIP standard)
    - max_iterations: safeguard against endless execution
    """
    mode = mode.lower().strip()
    if mode not in ("standard", "split_horizon", "poison_reverse"):
        raise ValueError(f"Invalid mode '{mode}'. Expected 'standard', 'split_horizon', or 'poison_reverse'.")

    # If no custom topology provided, construct the standard 4-node topology:
    # A <--(1)--> B <--(1)--> C <--(1)--> DEST
    if topology is None:
        topology = NetworkTopology()
        for n in ["A", "B", "C", "DEST"]:
            topology.add_node(n)
        topology.add_edge("A", "B", 1)
        topology.add_edge("B", "C", 1)
        topology.add_edge("C", "DEST", 1)
        failed_link = ("C", "DEST")
        destination = "DEST"
    else:
        # Use provided or default
        if failed_link is None:
            failed_link = ("C", "DEST")
        if destination is None:
            destination = "DEST"

    u_fail, v_fail = failed_link
    u_fail = str(u_fail).strip().upper()
    v_fail = str(v_fail).strip().upper()
    destination = str(destination).strip().upper()

    nodes = topology.get_nodes()
    if destination not in nodes:
        raise ValueError(f"Target destination '{destination}' does not exist in topology.")

    # 1. Compute initial steady-state / converged tables before the failure
    # We do a standard distance vector convergence on the intact network
    intact_adj = {n: dict(topology.get_neighbors(n)) for n in nodes}
    
    # router_tables[r][dest] = {"cost": float, "next_hop": str}
    tables: Dict[str, Dict[str, Dict[str, Any]]] = {}
    for r in nodes:
        tables[r] = {}
        for d in nodes:
            if r == d:
                tables[r][d] = {"cost": 0.0, "next_hop": "-"}
            elif d in intact_adj[r]:
                tables[r][d] = {"cost": float(intact_adj[r][d]), "next_hop": d}
            else:
                tables[r][d] = {"cost": float("inf"), "next_hop": "-"}

    # Converge intact tables
    for _ in range(len(nodes) + 2):
        for r in nodes:
            for d in nodes:
                if r == d:
                    continue
                for nbr, w in intact_adj[r].items():
                    cost_via = w + tables[nbr][d]["cost"]
                    if cost_via < tables[r][d]["cost"]:
                        tables[r][d]["cost"] = cost_via
                        tables[r][d]["next_hop"] = nbr

    def format_metric(val: float) -> Any:
        if math.isinf(val) or val >= infinity_threshold:
            return f"∞ ({infinity_threshold})"
        return int(val) if val.is_integer() else round(val, 2)

    def is_unreachable(val: float) -> bool:
        return math.isinf(val) or val >= infinity_threshold

    def detect_loop(dest: str) -> Optional[List[str]]:
        """Detect if there is currently a cycle in next hops toward destination."""
        for start in nodes:
            if start == dest or is_unreachable(tables[start][dest]["cost"]):
                continue
            visited = []
            curr = start
            while curr != dest and not is_unreachable(tables[curr][dest]["cost"]):
                if curr in visited:
                    cycle_start = visited.index(curr)
                    return visited[cycle_start:] + [curr]
                visited.append(curr)
                nxt = tables[curr][dest]["next_hop"]
                if not nxt or nxt == "-" or nxt not in nodes:
                    break
                curr = nxt
        return None

    def capture_step(iteration: int, title: str, description: str, advertisements: List[Dict[str, Any]], updates: List[Dict[str, Any]], link_state: str = "active") -> Dict[str, Any]:
        snapshot_tables = {}
        for r in nodes:
            snapshot_tables[r] = []
            for d in sorted(nodes):
                entry = tables[r][d]
                c = entry["cost"]
                snapshot_tables[r].append({
                    "router": r,
                    "destination": d,
                    "next_hop": entry["next_hop"],
                    "cost": None if is_unreachable(c) else (int(c) if c.is_integer() else round(c, 2)),
                    "cost_display": format_metric(c)
                })

        loop = detect_loop(destination)

        # Dest cost map specifically for the target destination
        dest_costs = {r: format_metric(tables[r][destination]["cost"]) for r in nodes}
        dest_next_hops = {r: tables[r][destination]["next_hop"] for r in nodes}

        return {
            "iteration": iteration,
            "title": title,
            "description": description,
            "link_status": link_state,
            "destination": destination,
            "failed_link": {"source": u_fail, "target": v_fail},
            "tables": snapshot_tables,
            "dest_costs": dest_costs,
            "dest_next_hops": dest_next_hops,
            "advertisements": advertisements,
            "updates": updates,
            "routing_loop": loop,
            "loop_detected": loop is not None,
            "mode": mode
        }

    steps = []

    # Step 0: Initial Converged State
    step0_desc = (
        f"Initial steady state before link failure. All routers have converged. "
        f"Path to destination '{destination}' is stable across all routers."
    )
    steps.append(capture_step(0, "Initial Stable State", step0_desc, [], [], link_state="UP"))

    # Step 1: The Link Failure Event occurs!
    # Sever the link in our working topology
    active_adj = {n: dict(intact_adj[n]) for n in nodes}
    if v_fail in active_adj.get(u_fail, {}):
        del active_adj[u_fail][v_fail]
    if u_fail in active_adj.get(v_fail, {}):
        del active_adj[v_fail][u_fail]

    # The router adjacent to the failed link detects the physical link drop
    # For example, if link C - DEST fails, C detects it directly.
    # If link B - C fails, both B and C detect it.
    adjacent_detectors = []
    if u_fail == destination:
        adjacent_detectors.append(v_fail)
    elif v_fail == destination:
        adjacent_detectors.append(u_fail)
    else:
        adjacent_detectors.extend([u_fail, v_fail])

    step1_updates = []
    for detector in adjacent_detectors:
        if tables[detector][destination]["next_hop"] in (u_fail, v_fail):
            old_c = tables[detector][destination]["cost"]
            tables[detector][destination]["cost"] = float("inf")
            tables[detector][destination]["next_hop"] = "-"
            step1_updates.append({
                "router": detector,
                "destination": destination,
                "old_cost": format_metric(old_c),
                "new_cost": format_metric(float("inf")),
                "reason": f"Direct physical link severed! Router {detector} immediately marks destination {destination} as unreachable."
            })

    fail_desc = (
        f"CRITICAL EVENT: Link ({u_fail} <---> {v_fail}) has FAILED! "
        f"Router(s) {', '.join(adjacent_detectors)} detect link loss and set direct cost to {destination} as ∞."
    )
    steps.append(capture_step(1, "Link Failure Detected", fail_desc, [], step1_updates, link_state="DOWN"))

    # Now simulate the subsequent routing update iterations after the link failure
    iteration = 1
    converged = False

    while iteration < max_iterations:
        iteration += 1
        round_advs = []
        round_updates = []
        has_change = False

        # Phase 1: Prepare advertisements based on selected mode
        # advs_received[receiver][sender][dest] = advertised_cost
        advs_received: Dict[str, Dict[str, Dict[str, float]]] = {n: {} for n in nodes}

        for sender in nodes:
            neighbors = sorted(list(active_adj[sender].keys()))
            for recipient in neighbors:
                advs_received[recipient][sender] = {}
                
                for d in nodes:
                    actual_cost = tables[sender][d]["cost"]
                    next_hop_for_d = tables[sender][d]["next_hop"]

                    advertised_cost = actual_cost

                    if mode == "split_horizon":
                        # Rule: Do not advertise route back to the next-hop router
                        if next_hop_for_d == recipient and d != sender:
                            advertised_cost = float("inf")
                    elif mode == "poison_reverse":
                        # Rule: Advertise route back to next-hop with metric set to infinity
                        if next_hop_for_d == recipient and d != sender:
                            advertised_cost = float("inf")

                    advs_received[recipient][sender][d] = advertised_cost

                    # Log advertisements specifically affecting the target destination
                    if d == destination:
                        rule_note = ""
                        if mode == "split_horizon" and next_hop_for_d == recipient:
                            rule_note = " [Split Horizon: Suppressed route advertisement]"
                        elif mode == "poison_reverse" and next_hop_for_d == recipient:
                            rule_note = f" [Poison Reverse: Advertised as ∞ ({infinity_threshold})]"

                        round_advs.append({
                            "sender": sender,
                            "recipient": recipient,
                            "destination": d,
                            "advertised_cost": format_metric(advertised_cost),
                            "note": rule_note
                        })

        # Phase 2: Each router computes Bellman-Ford update for destination
        for r in nodes:
            if r == destination:
                continue

            old_cost = tables[r][destination]["cost"]
            old_next_hop = tables[r][destination]["next_hop"]

            best_cost = float("inf")
            best_next_hop = "-"

            neighbors = active_adj[r]
            for nbr, link_w in sorted(neighbors.items()):
                nbr_advertised = advs_received.get(r, {}).get(nbr, {}).get(destination, float("inf"))
                total_cost = link_w + nbr_advertised
                if total_cost < best_cost:
                    best_cost = total_cost
                    best_next_hop = nbr

            # Apply infinity cap
            if best_cost >= infinity_threshold or math.isinf(best_cost):
                best_cost = float("inf")
                best_next_hop = "-"

            cost_changed = not (math.isinf(old_cost) and math.isinf(best_cost)) and not math.isclose(old_cost, best_cost, abs_tol=1e-5)
            next_hop_changed = (old_next_hop != best_next_hop)

            if cost_changed or (next_hop_changed and not math.isinf(best_cost)):
                tables[r][destination]["cost"] = best_cost
                tables[r][destination]["next_hop"] = best_next_hop
                has_change = True

                explanation = ""
                if mode == "standard" and not math.isinf(best_cost):
                    explanation = (
                        f"ROUTING LOOP UPDATE: Router {r} updated its route to {destination} via {best_next_hop} "
                        f"with cost {format_metric(best_cost)}. Router {r} does not realize {best_next_hop}'s route "
                        f"was originally learned through {r} itself!"
                    )
                elif is_unreachable(best_cost):
                    explanation = f"Router {r} confirmed destination {destination} is completely unreachable (metric >= {infinity_threshold})."
                else:
                    explanation = f"Router {r} updated route to {destination} via {best_next_hop} (cost: {format_metric(best_cost)})."

                round_updates.append({
                    "router": r,
                    "destination": destination,
                    "old_cost": format_metric(old_cost),
                    "new_cost": format_metric(best_cost),
                    "old_next_hop": old_next_hop,
                    "new_next_hop": best_next_hop,
                    "reason": explanation
                })

        # Generate step narrative
        if not has_change:
            converged = True
            step_title = f"Iteration {iteration}: Converged"
            step_desc = (
                f"Convergence reached at iteration {iteration}. "
                f"All reachable routes are stable; unreachable destination '{destination}' is recognized as ∞."
            )
        else:
            step_title = f"Iteration {iteration}: Routing Update Exchange"
            if mode == "standard":
                step_desc = (
                    f"Iteration {iteration}: Routing costs continue to climb due to mutual reliance (Count-to-Infinity). "
                    f"Threshold: {infinity_threshold}."
                )
            elif mode == "split_horizon":
                step_desc = f"Iteration {iteration}: Split Horizon prevented loops by suppressing advertisements to next-hops."
            else:
                step_desc = f"Iteration {iteration}: Poison Reverse advertises metric ∞ back to predecessor, swiftly extinguishing loops."

        steps.append(capture_step(iteration, step_title, step_desc, round_advs, round_updates, link_state="DOWN"))

        if not has_change:
            break

    # Summary analysis
    max_cost_observed = 0.0
    for s in steps:
        for r, c_disp in s["dest_costs"].items():
            if "∞" not in str(c_disp):
                try:
                    c_num = float(c_disp)
                    if c_num > max_cost_observed:
                        max_cost_observed = c_num
                except ValueError:
                    pass

    return {
        "mode": mode,
        "destination": destination,
        "failed_link": [u_fail, v_fail],
        "infinity_threshold": infinity_threshold,
        "converged": converged,
        "total_iterations": len(steps) - 1,
        "steps": steps,
        "max_cost_observed": max_cost_observed,
        "summary": {
            "mode_name": {
                "standard": "Standard Distance Vector (Count-to-Infinity Vulnerable)",
                "split_horizon": "Distance Vector with Split Horizon",
                "poison_reverse": "Distance Vector with Poison Reverse"
            }.get(mode, mode),
            "iterations_to_resolve": len(steps) - 1,
            "max_metric_reached": max_cost_observed,
            "explanation": _get_mode_explanation(mode, infinity_threshold)
        }
    }


def _get_mode_explanation(mode: str, threshold: int) -> str:
    if mode == "standard":
        return (
            f"Under standard Distance Vector without loop prevention, routers bounce stale advertisements back and forth. "
            f"Because neither router has complete path information, each router believes the other possesses an alternate "
            f"path to the destination. The metric increments on each exchange until it hits the configured infinity threshold ({threshold}), "
            f"at which point the protocol finally considers the network unreachable."
        )
    elif mode == "split_horizon":
        return (
            "Split Horizon enforces a strict rule: 'Never advertise a route back out the same interface/to the router from "
            "which it was learned'. Because router A never advertises the destination back to router B, router B immediately "
            "recognizes there are no alternate paths when the direct link fails, averting the 2-node count-to-infinity loop."
        )
    else:
        return (
            f"Poison Reverse (Split Horizon with Poisoned Reverse) actively advertises routes back to the learning neighbor "
            f"with metric set explicitly to ∞ ({threshold}). This explicitly informs the predecessor that routing through "
            f"this router is invalid, immediately breaking 2-node loops and accelerating convergence across the network."
        )
