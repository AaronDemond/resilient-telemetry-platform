"""Verify deterministic telemetry generation for equal simulation seeds."""

from __future__ import annotations

import unittest

from initialize import Simulation, initialize_simulation


def _run_simulation_iterations(
    simulation: Simulation,
    iterations: int,
) -> list[list[tuple[str, bytes]]]:
    """Advance a simulation and collect each iteration's serialized telemetry."""
    telemetry_snapshots: list[list[tuple[str, bytes]]] = []

    for _ in range(iterations):
        simulation.run_iteration()
        telemetry_snapshots.append(
            [
                (unit.unit_id, unit.get_telemetry_message().SerializeToString())
                for unit in simulation.get_units()
            ]
        )

    return telemetry_snapshots


class SimulationSeedTest(unittest.TestCase):
    """Check deterministic output from independently created simulations."""

    def test_same_seed_produces_identical_telemetry(self) -> None:
        """Equal seeds and unit counts must produce identical telemetry."""
        num_units = 10
        seed = 42
        iterations = 5
        simulation_a = initialize_simulation(num_units=num_units, seed=seed)
        simulation_b = initialize_simulation(num_units=num_units, seed=seed)

        self.assertIsNot(simulation_a, simulation_b)
        self.assertEqual(len(simulation_a.get_units()), num_units)
        self.assertEqual(len(simulation_b.get_units()), num_units)

        telemetry_a = _run_simulation_iterations(simulation_a, iterations)
        telemetry_b = _run_simulation_iterations(simulation_b, iterations)

        self.assertEqual(
            telemetry_a,
            telemetry_b,
            "simulations with equal seeds produced different telemetry",
        )


if __name__ == "__main__":
    unittest.main()
