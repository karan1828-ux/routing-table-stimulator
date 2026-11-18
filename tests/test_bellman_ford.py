"""
Unit tests for Distributed Distance-Vector / Bellman-Ford implementation.
"""
import unittest
from network.topology import NetworkTopology
from algorithms.bellman_ford import run_distance_vector
from algorithms.dijkstra import run_dijkstra


class TestDistanceVector(unittest.TestCase):
    def setUp(self):
        self.topology = NetworkTopology()
        self.topology.load_sample_network()

    def test_sample_network_convergence(self):
        result = run_distance_vector(self.topology, source_node="A")
        self.assertTrue(result["converged"])
        self.assertGreaterEqual(result["iterations_count"], 1)

        # Get final routing table for A
        table = {row["destination"]: row for row in result["routing_table"]}

        # Costs must match Dijkstra exactly
        self.assertEqual(table["A"]["cost"], 0)
        self.assertEqual(table["B"]["cost"], 3)
        self.assertEqual(table["C"]["cost"], 2)
        self.assertEqual(table["D"]["cost"], 8)
        self.assertEqual(table["E"]["cost"], 10)

        # Next hops from A must be C
        self.assertEqual(table["B"]["next_hop"], "C")
        self.assertEqual(table["C"]["next_hop"], "C")
        self.assertEqual(table["D"]["next_hop"], "C")
        self.assertEqual(table["E"]["next_hop"], "C")

    def test_compare_all_routers_with_dijkstra(self):
        """Verify that Distance Vector converges to the same shortest paths as Dijkstra for all routers."""
        dv_result = run_distance_vector(self.topology)
        all_tables = dv_result["all_routing_tables"]

        for router in self.topology.get_nodes():
            dijkstra_result = run_dijkstra(self.topology, router)
            dijkstra_map = {r["destination"]: r["cost"] for r in dijkstra_result["routing_table"]}
            dv_map = {r["destination"]: r["cost"] for r in all_tables[router]}

            for dest in self.topology.get_nodes():
                self.assertEqual(
                    dv_map[dest],
                    dijkstra_map[dest],
                    f"Cost mismatch from router {router} to {dest}: DV={dv_map[dest]} vs Dijkstra={dijkstra_map[dest]}"
                )

    def test_iterations_trace(self):
        result = run_distance_vector(self.topology)
        iterations = result["iterations"]
        self.assertGreater(len(iterations), 1)
        # Iteration 0 has 0 exchanges
        self.assertEqual(iterations[0]["iteration"], 0)
        # Subsequent iterations have exchanges
        self.assertGreater(len(iterations[1]["exchanges"]), 0)


if __name__ == "__main__":
    unittest.main()
