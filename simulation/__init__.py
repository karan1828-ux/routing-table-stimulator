"""
Simulation package for routing events and Count-to-Infinity analysis.
"""
from .count_to_infinity import simulate_count_to_infinity
from .link_failure import LinkFailureManager

__all__ = ["simulate_count_to_infinity", "LinkFailureManager"]
