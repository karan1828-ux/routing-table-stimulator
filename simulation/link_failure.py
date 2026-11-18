"""
Link Failure Module.
Handles simulating failure and recovery of physical connections in the network.
"""
from typing import Dict, Any, Optional
from network.topology import NetworkTopology


class LinkFailureManager:
    def __init__(self, topology: NetworkTopology):
        self.topology = topology
        # Store failed links: tuple(sorted([u, v])) -> weight
        self.failed_links: Dict[tuple, float] = {}

    def fail_link(self, u: str, v: str) -> Dict[str, Any]:
        """Simulate a physical link cut between u and v."""
        u = str(u).strip().upper()
        v = str(v).strip().upper()
        edge_key = tuple(sorted([u, v]))

        neighbors = self.topology.get_neighbors(u)
        if v not in neighbors:
            raise ValueError(f"Link between {u} and {v} does not exist in the active network.")
        
        weight = neighbors[v]
        self.failed_links[edge_key] = weight
        self.topology.remove_edge(u, v)

        return {
            "status": "failed",
            "link": {"source": u, "target": v, "original_weight": weight},
            "message": f"Link ({u} <---> {v}) severed. Link cost set to ∞."
        }

    def restore_link(self, u: str, v: str) -> Dict[str, Any]:
        """Restore a previously failed link."""
        u = str(u).strip().upper()
        v = str(v).strip().upper()
        edge_key = tuple(sorted([u, v]))

        if edge_key not in self.failed_links:
            raise ValueError(f"Link between {u} and {v} is not currently marked as failed.")
        
        weight = self.failed_links.pop(edge_key)
        self.topology.add_edge(u, v, weight)

        return {
            "status": "restored",
            "link": {"source": u, "target": v, "weight": weight},
            "message": f"Link ({u} <---> {v}) restored with cost {weight}."
        }

    def get_failed_links(self) -> Dict[str, Any]:
        """List all currently severed links."""
        return [
            {"source": k[0], "target": k[1], "weight": w}
            for k, w in self.failed_links.items()
        ]
