"""
Comprehensive End-to-End Integration Tests for Routing Algorithm Simulator.
"""

import unittest
from app import app, current_topology


class TestEndToEndIntegration(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True
        current_topology.load_sample_network()

    def test_frontend_page_render(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.data.decode("utf-8")
        self.assertIn("Routing Algorithm Simulator", html)
        self.assertIn("Count-to-Infinity Problem Lab", html)
        self.assertIn("Educational Guide", html)
        self.assertIn("cytoscape.min.js", html)

    def test_sample_network_topology(self):
        res = self.client.get("/api/network")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()["topology"]
        nodes = [n["id"] for n in data["nodes"]]
        self.assertEqual(sorted(nodes), ["A", "B", "C", "D", "E"])
        self.assertEqual(len(data["edges"]), 7)

    def test_dijkstra_full_flow(self):
        res = self.client.post("/api/simulation/dijkstra", json={"source": "A"})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()["data"]

        self.assertEqual(data["source"], "A")
        self.assertEqual(data["algorithm"], "Dijkstra (Link State)")
        
        table = {row["destination"]: row for row in data["routing_table"]}
        self.assertEqual(table["A"]["cost"], 0)
        self.assertEqual(table["B"]["cost"], 3)
        self.assertEqual(table["C"]["cost"], 2)
        self.assertEqual(table["D"]["cost"], 8)
        self.assertEqual(table["E"]["cost"], 10)

        # Predecessor / path check
        self.assertEqual(table["E"]["path"], "A -> C -> B -> D -> E")
        self.assertEqual(table["E"]["next_hop"], "C")

    def test_distance_vector_full_flow(self):
        res = self.client.post("/api/simulation/distance-vector", json={"source": "A"})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()["data"]

        self.assertTrue(data["converged"])
        self.assertGreater(data["iterations_count"], 0)
        
        table = {row["destination"]: row for row in data["routing_table"]}
        self.assertEqual(table["A"]["cost"], 0)
        self.assertEqual(table["B"]["cost"], 3)
        self.assertEqual(table["C"]["cost"], 2)
        self.assertEqual(table["D"]["cost"], 8)
        self.assertEqual(table["E"]["cost"], 10)

    def test_count_to_infinity_scenarios(self):
        # 1. Standard mode: counts to 16, creates loop
        res_std = self.client.post("/api/simulation/count-to-infinity", json={
            "mode": "standard",
            "infinity_threshold": 16
        })
        self.assertEqual(res_std.status_code, 200)
        d_std = res_std.get_json()["data"]
        self.assertTrue(d_std["converged"])
        self.assertGreaterEqual(d_std["total_iterations"], 12)
        self.assertEqual(d_std["max_cost_observed"], 15)

        # 2. Split Horizon: avoids counting to 16
        res_sh = self.client.post("/api/simulation/count-to-infinity", json={
            "mode": "split_horizon",
            "infinity_threshold": 16
        })
        self.assertEqual(res_sh.status_code, 200)
        d_sh = res_sh.get_json()["data"]
        self.assertTrue(d_sh["converged"])
        self.assertLessEqual(d_sh["total_iterations"], 4)
        self.assertLess(d_sh["max_cost_observed"], 5)

        # 3. Poison Reverse: avoids counting to 16
        res_pr = self.client.post("/api/simulation/count-to-infinity", json={
            "mode": "poison_reverse",
            "infinity_threshold": 16
        })
        self.assertEqual(res_pr.status_code, 200)
        d_pr = res_pr.get_json()["data"]
        self.assertTrue(d_pr["converged"])
        self.assertLessEqual(d_pr["total_iterations"], 4)
        self.assertLess(d_pr["max_cost_observed"], 5)

    def test_random_network_generator(self):
        res = self.client.post("/api/network/random", json={"num_nodes": 7, "density": 0.5})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()["topology"]
        self.assertEqual(len(data["nodes"]), 7)
        self.assertGreaterEqual(len(data["edges"]), 6)


if __name__ == "__main__":
    unittest.main()
