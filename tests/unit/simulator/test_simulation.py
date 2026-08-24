"""Verify simulation iteration and unit telemetry behavior."""

from __future__ import annotations

import unittest

from initialize import initialize_simulation


class SimulationBehaviorTest(unittest.TestCase):
    """Check unit state and telemetry across repeated simulation iterations."""

    def test_five_iterations_generate_valid_unit_telemetry(self) -> None:
        """Each iteration must update all units and attach consistent telemetry."""
        num_units = 10
        simulation = initialize_simulation(num_units=num_units, seed=42)

        self.assertEqual(len(simulation.get_units()), num_units)
        for unit in simulation.get_units():
            with self.subTest(unit_id=unit.unit_id, state="before telemetry"):
                with self.assertRaises(RuntimeError):
                    unit.get_telemetry_message()

        for expected_sequence in range(1, 6):
            units = simulation.run_iteration()
            self.assertEqual(len(units), num_units)

            for unit in units:
                with self.subTest(
                    unit_id=unit.unit_id,
                    iteration=expected_sequence,
                ):
                    position = unit.position
                    message = unit.get_telemetry_message()

                    self.assertGreaterEqual(position.x, 0.0)
                    self.assertLessEqual(position.x, position.area_width)
                    self.assertGreaterEqual(position.y, 0.0)
                    self.assertLessEqual(position.y, position.area_height)
                    self.assertEqual(message.envelope.unit_id, unit.unit_id)
                    self.assertEqual(message.event.unit_id, unit.unit_id)
                    self.assertEqual(message.envelope.boot_id, message.event.boot_id)
                    self.assertEqual(
                        message.envelope.sequence_number,
                        expected_sequence,
                    )
                    self.assertEqual(
                        message.event.sequence_number,
                        expected_sequence,
                    )
                    self.assertAlmostEqual(
                        message.event.latitude,
                        position.latitude,
                    )
                    self.assertAlmostEqual(
                        message.event.longitude,
                        position.longitude,
                    )


if __name__ == "__main__":
    unittest.main()
