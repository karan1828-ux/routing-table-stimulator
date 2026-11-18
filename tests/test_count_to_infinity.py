"""
Unit tests for Count-to-Infinity simulation and prevention mechanisms.
"""
import unittest
from simulation.count_to_infinity import simulate_count_to_infinity
from network.topology import NetworkTopology


class TestCountToInfinity(unittest.TestCase):
    def test_standard_count_to_infinity_loop(self):
        # Run standard simulation with threshold 8 for fast unit test
        result = simulate_count_to_infinity(mode="standard", infinity_threshold=8)
        self.assertTrue(result["converged"])
        # Should take multiple iterations to count up to 8
        self.assertGreaterEqual(result["total_iterations"], 6)
        # Should reach metric close to or at threshold
        self.assertGreaterEqual(result["max_cost_observed"], 7)
        # Check that loop was detected in at least one step
        loops = [s["routing_loop"] for s in result["steps"] if s["routing_loop"]]
        self.assertTrue(len(loops) > 0)

    def test_split_horizon_prevents_loop(self):
        # Split horizon should converge in fewer iterations than standard mode
        result = simulate_count_to_infinity(mode="split_horizon", infinity_threshold=16)
        self.assertTrue(result["converged"])
        # Converges almost immediately after failure
        self.assertLessEqual(result["total_iterations"], 4)
        # Cost should not inflate to 15 or 16
        self.assertLess(result["max_cost_observed"], 6)

    def test_poison_reverse_prevents_loop(self):
        result = simulate_count_to_infinity(mode="poison_reverse", infinity_threshold=16)
        self.assertTrue(result["converged"])
        self.assertLessEqual(result["total_iterations"], 4)
        self.assertLess(result["max_cost_observed"], 6)


if __name__ == "__main__":
    unittest.main()
