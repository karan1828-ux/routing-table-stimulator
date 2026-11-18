"""
Unit tests for Flask API endpoints.
"""
import unittest
import json
from app import app, current_topology


class TestAppAPI(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True
        # Reset to sample network
        current_topology.load_sample_network()

    def test_get_network(self):
        res = self.client.get("/api/network")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(len(data["topology"]["nodes"]), 5)

    def test_add_and_remove_node(self):
        # Add node Z
        res = self.client.post("/api/network/nodes", json={"id": "Z"})
        self.assertEqual(res.status_code, 200)
        self.assertIn("Z", current_topology.get_nodes())

        # Duplicate node error
        res = self.client.post("/api/network/nodes", json={"id": "Z"})
        self.assertEqual(res.status_code, 400)

        # Remove node Z
        res = self.client.delete("/api/network/nodes/Z")
        self.assertEqual(res.status_code, 200)
        self.assertNotIn("Z", current_topology.get_nodes())

    def test_add_and_update_edge(self):
        res = self.client.post("/api/network/edges", json={"source": "A", "target": "D", "weight": 7})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(current_topology.adj["A"]["D"], 7)

        # Negative weight should fail
        res = self.client.post("/api/network/edges", json={"source": "A", "target": "D", "weight": -2})
        self.assertEqual(res.status_code, 400)

    def test_dijkstra_api(self):
        res = self.client.post("/api/simulation/dijkstra", json={"source": "A"})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["source"], "A")
        self.assertGreater(len(data["data"]["steps"]), 0)

    def test_distance_vector_api(self):
        res = self.client.post("/api/simulation/distance-vector", json={"source": "A"})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertTrue(data["data"]["converged"])
        self.assertIn("iterations", data["data"])

    def test_count_to_infinity_api(self):
        res = self.client.post("/api/simulation/count-to-infinity", json={
            "mode": "split_horizon",
            "infinity_threshold": 16
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["mode"], "split_horizon")

    def test_csv_export(self):
        table = [
            {"router": "A", "destination": "B", "next_hop": "C", "cost_display": "3", "path": "A -> C -> B"}
        ]
        res = self.client.post("/api/export/csv", json={"table": table, "router": "A"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.mimetype, "text/csv")
        self.assertIn(b"Router,Destination,Next Hop,Cost,Path", res.data)


if __name__ == "__main__":
    unittest.main()
