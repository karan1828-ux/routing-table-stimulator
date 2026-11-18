"""
Network Topology Data Structure.
Uses an adjacency list representation with pure Python dictionaries and sets.
Provides graph validation, mutation, and sample/random topology generation.
"""

import random
from typing import Dict, List, Set, Tuple, Any, Optional


class NetworkTopology:
    def __init__(self):
        # Adjacency list: node -> {neighbor: weight}
        self.adj: Dict[str, Dict[str, float]] = {}

    def add_node(self, node_id: str) -> None:
        """Add a router node to the network."""
        node_id = str(node_id).strip().upper()
        if not node_id:
            raise ValueError("Router identifier cannot be empty.")
        if node_id in self.adj:
            raise ValueError(f"Router '{node_id}' already exists in topology.")
        self.adj[node_id] = {}

    def remove_node(self, node_id: str) -> None:
        """Remove a router node and all incident connections."""
        node_id = str(node_id).strip().upper()
        if node_id not in self.adj:
            raise ValueError(f"Router '{node_id}' does not exist.")
        
        # Remove incident edges from neighbors
        for neighbor in list(self.adj[node_id].keys()):
            del self.adj[neighbor][node_id]
        
        # Remove the node itself
        del self.adj[node_id]

    def add_edge(self, u: str, v: str, weight: float) -> None:
        """Add an undirected connection between router u and router v with a cost weight."""
        u = str(u).strip().upper()
        v = str(v).strip().upper()
        
        if u not in self.adj:
            raise ValueError(f"Router '{u}' does not exist.")
        if v not in self.adj:
            raise ValueError(f"Router '{v}' does not exist.")
        if u == v:
            raise ValueError("Self-loop connections are not permitted.")
        
        try:
            w = float(weight)
        except (ValueError, TypeError):
            raise ValueError("Connection weight must be a valid number.")

        if w <= 0:
            raise ValueError("Routing metric (cost) must be strictly positive (> 0).")

        self.adj[u][v] = w
        self.adj[v][u] = w

    def remove_edge(self, u: str, v: str) -> None:
        """Remove the undirected connection between router u and router v."""
        u = str(u).strip().upper()
        v = str(v).strip().upper()
        
        if u not in self.adj or v not in self.adj:
            raise ValueError("One or both routers do not exist.")
        if v not in self.adj[u]:
            raise ValueError(f"Connection between '{u}' and '{v}' does not exist.")
        
        del self.adj[u][v]
        del self.adj[v][u]

    def update_edge(self, u: str, v: str, weight: float) -> None:
        """Update the connection weight between router u and router v."""
        self.add_edge(u, v, weight)

    def get_nodes(self) -> List[str]:
        """Return a sorted list of all router identifiers."""
        return sorted(list(self.adj.keys()))

    def get_neighbors(self, node_id: str) -> Dict[str, float]:
        """Return dict of {neighbor: weight} for a given router."""
        node_id = str(node_id).strip().upper()
        if node_id not in self.adj:
            raise ValueError(f"Router '{node_id}' does not exist.")
        return dict(self.adj[node_id])

    def get_edges(self) -> List[Dict[str, Any]]:
        """Return a list of all undirected edges with weights."""
        edges = []
        seen = set()
        for u in sorted(self.adj.keys()):
            for v, w in sorted(self.adj[u].items()):
                edge_pair = tuple(sorted([u, v]))
                if edge_pair not in seen:
                    seen.add(edge_pair)
                    edges.append({
                        "source": edge_pair[0],
                        "target": edge_pair[1],
                        "weight": w
                    })
        return edges

    def clear(self) -> None:
        """Clear all routers and connections."""
        self.adj.clear()

    def load_sample_network(self) -> None:
        """
        Load the canonical 5-router sample network:
        Routers: A, B, C, D, E
        Edges:
        A-B = 4
        A-C = 2
        B-C = 1
        B-D = 5
        C-D = 8
        C-E = 10
        D-E = 2
        """
        self.clear()
        for node in ["A", "B", "C", "D", "E"]:
            self.add_node(node)
        
        edges = [
            ("A", "B", 4),
            ("A", "C", 2),
            ("B", "C", 1),
            ("B", "D", 5),
            ("C", "D", 8),
            ("C", "E", 10),
            ("D", "E", 2)
        ]
        for u, v, w in edges:
            self.add_edge(u, v, w)

    def load_predefined(self, preset_name: str) -> None:
        """Load predefined standard educational network topologies."""
        preset = preset_name.lower().strip()
        if preset in ("sample", "default"):
            self.load_sample_network()
        elif preset in ("mesh", "ring_mesh"):
            self.clear()
            nodes = ["R1", "R2", "R3", "R4", "R5", "R6"]
            for n in nodes:
                self.add_node(n)
            edges = [
                ("R1", "R2", 3),
                ("R2", "R3", 4),
                ("R3", "R4", 2),
                ("R4", "R5", 6),
                ("R5", "R6", 1),
                ("R6", "R1", 5),
                ("R2", "R5", 7),
                ("R1", "R4", 8),
            ]
            for u, v, w in edges:
                self.add_edge(u, v, w)
        elif preset in ("count_to_infinity", "c2i"):
            self.clear()
            for n in ["A", "B", "C", "DEST"]:
                self.add_node(n)
            edges = [
                ("A", "B", 1),
                ("B", "C", 1),
                ("C", "DEST", 1)
            ]
            for u, v, w in edges:
                self.add_edge(u, v, w)
        elif preset in ("disconnected", "partitioned"):
            self.clear()
            # Two separate components
            for n in ["A", "B", "C", "X", "Y", "Z"]:
                self.add_node(n)
            self.add_edge("A", "B", 3)
            self.add_edge("B", "C", 2)
            self.add_edge("A", "C", 4)
            self.add_edge("X", "Y", 5)
            self.add_edge("Y", "Z", 1)
        else:
            raise ValueError(f"Unknown preset topology '{preset_name}'.")

    def generate_random_network(self, num_nodes: int = 6, density: float = 0.45, min_weight: int = 1, max_weight: int = 12) -> None:
        """
        Generate a connected random graph with alphabetical router labels.
        Guarantees connectivity by first building a random spanning tree, then adding edges based on density.
        """
        if num_nodes < 2 or num_nodes > 15:
            raise ValueError("Number of routers must be between 2 and 15.")
        
        self.clear()
        labels = [chr(ord('A') + i) for i in range(num_nodes)]
        for label in labels:
            self.add_node(label)
        
        # Step 1: Spanning tree to ensure network is fully connected
        connected = [labels[0]]
        unconnected = labels[1:]
        random.shuffle(unconnected)

        while unconnected:
            u = random.choice(connected)
            v = unconnected.pop()
            weight = random.randint(min_weight, max_weight)
            self.add_edge(u, v, weight)
            connected.append(v)
        
        # Step 2: Add extra random edges according to density
        all_possible = []
        for i in range(num_nodes):
            for j in range(i + 1, num_nodes):
                u = labels[i]
                v = labels[j]
                if v not in self.adj[u]:
                    all_possible.append((u, v))
        
        random.shuffle(all_possible)
        extra_count = int(len(all_possible) * max(0.0, min(1.0, density)))
        for k in range(extra_count):
            u, v = all_possible[k]
            weight = random.randint(min_weight, max_weight)
            self.add_edge(u, v, weight)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize topology for JSON transmission."""
        return {
            "nodes": [{"id": n, "label": n} for n in self.get_nodes()],
            "edges": self.get_edges(),
            "adjacency": {k: dict(v) for k, v in self.adj.items()}
        }

    def from_dict(self, data: Dict[str, Any]) -> None:
        """Load topology from JSON format."""
        self.clear()
        nodes = data.get("nodes", [])
        for node in nodes:
            nid = node["id"] if isinstance(node, dict) else str(node)
            self.add_node(nid)
        
        edges = data.get("edges", [])
        for edge in edges:
            u = edge.get("source")
            v = edge.get("target")
            w = edge.get("weight", 1)
            self.add_edge(u, v, w)
