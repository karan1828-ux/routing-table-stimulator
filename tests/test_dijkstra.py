"""
Unit tests for Dijkstra's Algorithm implementation.
"""
import unittest
from network.topology import NetworkTopology
from algorithms.dijkstra import run_dijkstra


class TestDijkstra(unittest.TestCase):
    def setUp(self):
        self.topology = NetworkTopology()
        self.topology.load_sample_network()

    def test_sample_network_from_a(self):
        result = run_dijkstra(self.topology, "A")
        table = {row["destination"]: row for row in result["routing_table"]}

        # Check costs
        self.assertEqual(table["A"]["cost"], 0)
        self.assertEqual(table["B"]["cost"], 3)  # A -> C -> B (2 + 1 = 3)
        self.assertEqual(table["C"]["cost"], 2)  # A -> C (2)
        self.assertEqual(table["D"]["cost"], 8)  # A -> C -> B -> D (2 + 1 + 5 = 8)
        self.assertEqual(table["E"]["cost"], 10) # A -> C -> B -> D -> E (2 + 1 + 5 + 2 = 10)

        # Check next hops
        self.assertEqual(table["A"]["next_hop"], "-")
        self.assertEqual(table["B"]["next_hop"], "C")
        self.assertEqual(table["C"]["next_hop"], "C")
        self.assertEqual(table["D"]["next_hop"], "C")
        self.assertEqual(table["E"]["next_hop"], "C")

        # Check paths
        self.assertEqual(table["B"]["path_nodes"], ["A", "C", "B"])
        self.assertEqual(table["D"]["path_nodes"], ["A", "C", "B", "D"])
        self.assertEqual(table["E"]["path_nodes"], ["A", "C", "B", "D", "E"])

    def test_sample_network_from_d(self):
        result = run_dijkstra(self.topology, "D")
        table = {row["destination"]: row for row in result["routing_table"]}

        self.assertEqual(table["D"]["cost"], 0)
        self.assertEqual(table["E"]["cost"], 2)  # D -> E (2)
        self.assertEqual(table["B"]["cost"], 5)  # D -> B (5)
        self.assertEqual(table["C"]["cost"], 6)  # D -> B -> C (5 + 1 = 6 < 8)
        self.assertEqual(table["A"]["cost"], 8)  # D -> B -> C -> A (5 + 1 + 2 = 8)

        self.assertEqual(table["E"]["next_hop"], "E")
        self.assertEqual(table["B"]["next_hop"], "B")
        self.assertEqual(table["C"]["next_hop"], "B")
        self.assertEqual(table["A"]["next_hop"], "B")

    def test_negative_weight_rejection(self):
        topo = NetworkTopology()
        topo.add_node("X")
        topo.add_node("Y")
        # Direct dictionary insertion or edge test
        topo.adj["X"]["Y"] = -3
        topo.adj["Y"]["X"] = -3
        with self.assertRaises(ValueError):
            run_dijkstra(topo, "X")

    def test_disconnected_router(self):
        topo = NetworkTopology()
        topo.add_node("A")
        topo.add_node("B")
        topo.add_node("ISOLATED")
        topo.add_edge("A", "B", 5)

        res = run_dijkstra(topo, "A")
        table = {row["destination"]: row for row in res["routing_table"]}
        self.assertEqual(table["B"]["cost"], 5)
        self.assertIsNone(table["ISOLATED"]["cost"])
        self.assertEqual(table["ISOLATED"]["cost_display"], "∞")
        self.assertEqual(table["ISOLATED"]["next_hop"], "-")
        self.assertEqual(table["ISOLATED"]["path"], "Unreachable")


if __name__ == "__main__":
    unittest.main()
