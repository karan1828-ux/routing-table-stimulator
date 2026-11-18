"""
Flask Application and REST API Routes for Routing Algorithm Simulator.
"""

import csv
import io
from flask import Flask, render_template, request, jsonify, Response
from flask_cors import CORS

from network.topology import NetworkTopology
from algorithms.dijkstra import run_dijkstra
from algorithms.bellman_ford import run_distance_vector
from simulation.count_to_infinity import simulate_count_to_infinity
from simulation.link_failure import LinkFailureManager

app = Flask(__name__)
CORS(app)

# Global in-memory network topology state
current_topology = NetworkTopology()
current_topology.load_sample_network()

# Link failure manager
failure_manager = LinkFailureManager(current_topology)


@app.route("/")
def index():
    """Render the main interactive dashboard."""
    return render_template("index.html")


# ============================================================================
# Topology Management API Endpoints
# ============================================================================

@app.route("/api/network", methods=["GET"])
def get_network():
    """Get the current network topology (nodes, edges, adjacency)."""
    return jsonify({
        "success": True,
        "topology": current_topology.to_dict()
    })


@app.route("/api/network/reset", methods=["POST"])
def reset_network():
    """Reset network to the canonical 5-router sample network or clear completely."""
    data = request.get_json(silent=True) or {}
    mode = data.get("mode", "sample")

    try:
        if mode == "clear":
            current_topology.clear()
        else:
            current_topology.load_sample_network()
        
        return jsonify({
            "success": True,
            "message": "Network reset successfully.",
            "topology": current_topology.to_dict()
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/api/network/load-preset", methods=["POST"])
def load_preset():
    """Load a predefined network topology."""
    data = request.get_json(silent=True) or {}
    preset_name = data.get("preset", "sample")

    try:
        current_topology.load_predefined(preset_name)
        return jsonify({
            "success": True,
            "message": f"Loaded preset '{preset_name}' successfully.",
            "topology": current_topology.to_dict()
        })
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": f"Failed to load preset: {str(e)}"}), 500


@app.route("/api/network/random", methods=["POST"])
def generate_random():
    """Generate a random connected network topology."""
    data = request.get_json(silent=True) or {}
    num_nodes = int(data.get("num_nodes", 6))
    density = float(data.get("density", 0.45))
    min_weight = int(data.get("min_weight", 1))
    max_weight = int(data.get("max_weight", 12))

    try:
        current_topology.generate_random_network(num_nodes, density, min_weight, max_weight)
        return jsonify({
            "success": True,
            "message": f"Generated random network with {num_nodes} routers.",
            "topology": current_topology.to_dict()
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/api/network/nodes", methods=["POST"])
def add_node():
    """Add a new router node to the topology."""
    data = request.get_json(silent=True) or {}
    node_id = data.get("id")

    if not node_id:
        return jsonify({"success": False, "error": "Router identifier 'id' is required."}), 400

    try:
        current_topology.add_node(node_id)
        return jsonify({
            "success": True,
            "message": f"Router '{node_id.strip().upper()}' added successfully.",
            "topology": current_topology.to_dict()
        })
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/api/network/nodes/<node_id>", methods=["DELETE"])
def remove_node(node_id):
    """Remove a router node from the topology."""
    try:
        current_topology.remove_node(node_id)
        return jsonify({
            "success": True,
            "message": f"Router '{node_id.strip().upper()}' removed successfully.",
            "topology": current_topology.to_dict()
        })
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/api/network/edges", methods=["POST"])
def add_edge():
    """Add or update an undirected connection between two routers."""
    data = request.get_json(silent=True) or {}
    u = data.get("source")
    v = data.get("target")
    weight = data.get("weight")

    if not u or not v or weight is None:
        return jsonify({"success": False, "error": "Source, target, and weight are required."}), 400

    try:
        current_topology.add_edge(u, v, weight)
        return jsonify({
            "success": True,
            "message": f"Connection {u.strip().upper()} <---> {v.strip().upper()} (cost: {weight}) added.",
            "topology": current_topology.to_dict()
        })
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/api/network/edges", methods=["DELETE"])
def remove_edge():
    """Remove an undirected connection between two routers."""
    data = request.get_json(silent=True) or {}
    u = data.get("source")
    v = data.get("target")

    if not u or not v:
        return jsonify({"success": False, "error": "Source and target are required."}), 400

    try:
        current_topology.remove_edge(u, v)
        return jsonify({
            "success": True,
            "message": f"Connection {u.strip().upper()} <---> {v.strip().upper()} removed.",
            "topology": current_topology.to_dict()
        })
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/api/network/edges/update", methods=["POST"])
def update_edge_weight():
    """Update connection weight."""
    data = request.get_json(silent=True) or {}
    u = data.get("source")
    v = data.get("target")
    weight = data.get("weight")

    if not u or not v or weight is None:
        return jsonify({"success": False, "error": "Source, target, and weight are required."}), 400

    try:
        current_topology.update_edge(u, v, weight)
        return jsonify({
            "success": True,
            "message": f"Connection {u.strip().upper()} <---> {v.strip().upper()} cost updated to {weight}.",
            "topology": current_topology.to_dict()
        })
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400


# ============================================================================
# Simulation API Endpoints
# ============================================================================

@app.route("/api/simulation/dijkstra", methods=["POST"])
def simulate_dijkstra():
    """Execute Dijkstra's Algorithm from a selected source router."""
    data = request.get_json(silent=True) or {}
    source = data.get("source")

    nodes = current_topology.get_nodes()
    if not nodes:
        return jsonify({"success": False, "error": "Network has no routers. Add routers first."}), 400

    if not source:
        source = nodes[0]

    try:
        result = run_dijkstra(current_topology, source)
        return jsonify({
            "success": True,
            "data": result
        })
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": f"Execution error: {str(e)}"}), 500


@app.route("/api/simulation/distance-vector", methods=["POST"])
def simulate_distance_vector():
    """Execute Distributed Distance Vector Routing on the topology."""
    data = request.get_json(silent=True) or {}
    source = data.get("source")
    max_iters = int(data.get("max_iterations", 50))

    nodes = current_topology.get_nodes()
    if not nodes:
        return jsonify({"success": False, "error": "Network has no routers. Add routers first."}), 400

    if not source:
        source = nodes[0]

    try:
        result = run_distance_vector(current_topology, source_node=source, max_iterations=max_iters)
        return jsonify({
            "success": True,
            "data": result
        })
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": f"Execution error: {str(e)}"}), 500


@app.route("/api/simulation/routing-tables", methods=["GET"])
def get_routing_tables():
    """Get dynamically calculated routing tables for all routers using Distance Vector convergence."""
    nodes = current_topology.get_nodes()
    if not nodes:
        return jsonify({"success": True, "tables": {}})

    try:
        result = run_distance_vector(current_topology)
        return jsonify({
            "success": True,
            "tables": result["all_routing_tables"],
            "converged": result["converged"],
            "iterations": result["iterations_count"]
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/simulation/count-to-infinity", methods=["POST"])
def run_count_to_infinity():
    """Execute Count-to-Infinity simulation scenario with loop prevention variants."""
    data = request.get_json(silent=True) or {}
    mode = data.get("mode", "standard")
    infinity_threshold = int(data.get("infinity_threshold", 16))
    destination = data.get("destination", "DEST")
    failed_link = data.get("failed_link", ["C", "DEST"])

    # Build Count-to-Infinity topology or use current if requested
    use_custom_topo = data.get("use_current_topology", False)
    topo = current_topology if use_custom_topo else None

    try:
        result = simulate_count_to_infinity(
            topology=topo,
            failed_link=tuple(failed_link) if failed_link else None,
            destination=destination,
            mode=mode,
            infinity_threshold=infinity_threshold
        )
        return jsonify({
            "success": True,
            "data": result
        })
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": f"Count-to-Infinity simulation error: {str(e)}"}), 500


@app.route("/api/simulation/link-failure", methods=["POST"])
def toggle_link_failure():
    """Sever or restore a specific connection in the active network."""
    data = request.get_json(silent=True) or {}
    action = data.get("action", "fail")
    u = data.get("source")
    v = data.get("target")

    if not u or not v:
        return jsonify({"success": False, "error": "Source and target are required."}), 400

    try:
        if action == "fail":
            res = failure_manager.fail_link(u, v)
        elif action == "restore":
            res = failure_manager.restore_link(u, v)
        else:
            return jsonify({"success": False, "error": "Invalid action. Use 'fail' or 'restore'."}), 400
        
        return jsonify({
            "success": True,
            "result": res,
            "topology": current_topology.to_dict(),
            "failed_links": failure_manager.get_failed_links()
        })
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/api/export/csv", methods=["POST"])
def export_csv():
    """Export routing table data as a downloadable CSV file."""
    data = request.get_json(silent=True) or {}
    table_rows = data.get("table", [])
    router_id = data.get("router", "All")

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Router", "Destination", "Next Hop", "Cost", "Path"])

    for row in table_rows:
        writer.writerow([
            row.get("router", ""),
            row.get("destination", ""),
            row.get("next_hop", "-"),
            row.get("cost_display", row.get("cost", "")),
            row.get("path", "")
        ])

    csv_data = output.getvalue()
    filename = f"routing_table_{router_id}.csv"

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
