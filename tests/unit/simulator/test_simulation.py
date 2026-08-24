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
                simulation.generate_telemetry(unit)
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

    def test_units_keep_distinct_movement_between_direction_changes(self) -> None:
        """Units must have distinct motion that persists across short updates."""
        simulation = initialize_simulation(num_units=10, seed=42)
        initial_movement = [
            (unit.movement.direction_radians, unit.movement.speed)
            for unit in simulation.get_units()
        ]

        self.assertEqual(len(set(initial_movement)), 10)
        simulation.run_iteration(elapsed_seconds=5.0)

        for unit, expected_movement in zip(
            simulation.get_units(),
            initial_movement,
            strict=True,
        ):
            with self.subTest(unit_id=unit.unit_id):
                self.assertEqual(
                    unit.movement.direction_radians,
                    expected_movement[0],
                )
                self.assertEqual(unit.movement.speed, expected_movement[1])

    def test_position_wraps_across_map_boundary(self) -> None:
        """A unit crossing an edge must re-enter from the opposite edge."""
        simulation = initialize_simulation(num_units=1, seed=42)
        unit = simulation.get_units()[0]
        unit.position.x = 99.0
        unit.position.y = 50.0
        unit.movement.direction_radians = 0.0
        unit.movement.speed = 1.0
        unit.movement.direction_seconds_remaining = 30.0
        unit.movement.speed_seconds_remaining = 30.0

        simulation.run_iteration(elapsed_seconds=5.0)

        self.assertAlmostEqual(unit.position.x, 4.0)
        self.assertAlmostEqual(unit.position.y, 50.0)
        simulation.generate_telemetry(unit)
        self.assertAlmostEqual(unit.get_telemetry_message().event.longitude, -165.6)

    def test_direction_and_speed_change_only_after_duration_expires(self) -> None:
        """Movement values must persist until their individual timers expire."""
        simulation = initialize_simulation(num_units=1, seed=42)
        unit = simulation.get_units()[0]
        original_direction = unit.movement.direction_radians
        original_speed = unit.movement.speed
        unit.movement.direction_seconds_remaining = 5.0
        unit.movement.speed_seconds_remaining = 5.0

        simulation.run_iteration(elapsed_seconds=5.0)

        self.assertEqual(unit.movement.direction_radians, original_direction)
        self.assertEqual(unit.movement.speed, original_speed)

        simulation.run_iteration(elapsed_seconds=5.0)

        self.assertNotEqual(unit.movement.direction_radians, original_direction)
        self.assertNotEqual(unit.movement.speed, original_speed)

    def test_movement_loop_only_moves_units_every_second(self) -> None:
        """The loop must move every second without generating telemetry."""
        simulation = initialize_simulation(num_units=2, seed=42)
        sleep_intervals: list[float] = []
        starting_positions = [
            (unit.position.x, unit.position.y)
            for unit in simulation.get_units()
        ]

        simulation.run_movement_loop(
            iterations=2,
            sleep_fn=sleep_intervals.append,
        )

        self.assertEqual(sleep_intervals, [1.0, 1.0])
        for unit, starting_position in zip(
            simulation.get_units(),
            starting_positions,
            strict=True,
        ):
            with self.subTest(unit_id=unit.unit_id):
                self.assertNotEqual(
                    (unit.position.x, unit.position.y),
                    starting_position,
                )
                with self.assertRaises(RuntimeError):
                    unit.get_telemetry_message()

    def test_movement_does_not_mutate_existing_telemetry(self) -> None:
        """Moving a unit must not change its last attached telemetry message."""
        simulation = initialize_simulation(num_units=1, seed=42)
        unit = simulation.get_units()[0]
        simulation.generate_telemetry(unit)
        message_before_movement = unit.get_telemetry_message()
        latitude_before_movement = message_before_movement.event.latitude
        longitude_before_movement = message_before_movement.event.longitude

        simulation.run_iteration()

        self.assertIs(unit.get_telemetry_message(), message_before_movement)
        self.assertEqual(
            unit.get_telemetry_message().event.latitude,
            latitude_before_movement,
        )
        self.assertEqual(
            unit.get_telemetry_message().event.longitude,
            longitude_before_movement,
        )


if __name__ == "__main__":
    unittest.main()
