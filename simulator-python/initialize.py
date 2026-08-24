"""Initialize the simulator with a reproducible random state."""

from __future__ import annotations

import math
import random
import time
from typing import Callable, List

from simulator import MovementState, Position, Unit
from telemetry_data import TelemetryGenerator


class Simulation:
    """Own an independent, deterministic simulation run."""

    DEFAULT_UPDATE_INTERVAL_SECONDS = 1.0
    MIN_SPEED = 0.01
    MAX_SPEED = 0.05
    MIN_DIRECTION_DURATION_SECONDS = 20.0
    MAX_DIRECTION_DURATION_SECONDS = 60.0
    MIN_SPEED_DURATION_SECONDS = 15.0
    MAX_SPEED_DURATION_SECONDS = 45.0

    def __init__(
        self,
        num_units: int = 0,
        seed: int = 0,
        *,
        area_width: float = 100.0,
        area_height: float = 100.0,
    ) -> None:
        if num_units < 0:
            raise ValueError("num_units must be non-negative")
        if area_width <= 0.0 or area_height <= 0.0:
            raise ValueError("simulation area dimensions must be positive")

        self.num_units = num_units
        self.seed = seed
        self.area_width = area_width
        self.area_height = area_height
        self.rng = random.Random(seed)
        self.telemetry_generator = TelemetryGenerator(rng=self.rng)
        self.units: List[Unit] = []
        self.initialize_units()

    def _new_direction_duration(self) -> float:
        """Choose how long a unit keeps its current direction."""
        return self.rng.uniform(
            self.MIN_DIRECTION_DURATION_SECONDS,
            self.MAX_DIRECTION_DURATION_SECONDS,
        )

    def _new_speed_duration(self) -> float:
        """Choose how long a unit keeps its current speed."""
        return self.rng.uniform(
            self.MIN_SPEED_DURATION_SECONDS,
            self.MAX_SPEED_DURATION_SECONDS,
        )

    def _change_direction(self, movement: MovementState) -> None:
        """Turn a unit by a meaningful amount and reset its direction timer."""
        turn = self.rng.uniform(math.pi / 6.0, (2.0 * math.pi) / 3.0)
        turn_sign = self.rng.choice((-1.0, 1.0))
        movement.direction_radians = (
            movement.direction_radians + turn_sign * turn
        ) % math.tau
        movement.direction_seconds_remaining = self._new_direction_duration()

    def _change_speed(self, movement: MovementState) -> None:
        """Assign a noticeably different speed and reset its speed timer."""
        new_speed = self.rng.uniform(self.MIN_SPEED, self.MAX_SPEED)
        while math.isclose(new_speed, movement.speed, abs_tol=0.001):
            new_speed = self.rng.uniform(self.MIN_SPEED, self.MAX_SPEED)
        movement.speed = new_speed
        movement.speed_seconds_remaining = self._new_speed_duration()

    def generate_telemetry(self, unit: Unit) -> Unit:
        """Generate and attach a telemetry message for a single unit.

        The telemetry generator owns the protobuf creation logic; this method
        delegates to it, stores the generated message on the unit, and returns the
        unit so callers can inspect the generated data.
        """
        if not isinstance(unit, Unit):
            raise TypeError("unit must be a Unit instance")

        unit.attach_telemetry_message(
            self.telemetry_generator.generate_random_data(unit)
        )
        return unit

    def get_units(self) -> List[Unit]:
        """Return the simulation units."""
        return list(self.units)

    def initialize_units(self) -> None:
        """Reset and populate units from the simulation seed."""
        self.rng = random.Random(self.seed)
        self.telemetry_generator = TelemetryGenerator(rng=self.rng)
        self.units = []

        for index in range(self.num_units):
            position = Position(
                x=self.rng.uniform(0.0, self.area_width),
                y=self.rng.uniform(0.0, self.area_height),
                area_width=self.area_width,
                area_height=self.area_height,
            )
            # Evenly spaced headings and speeds guarantee distinct initial motion.
            direction = (
                math.tau * index / max(1, self.num_units)
                + self.rng.uniform(-0.1, 0.1)
            ) % math.tau
            speed_fraction = (index + 1) / (self.num_units + 1)
            speed = self.MIN_SPEED + speed_fraction * (self.MAX_SPEED - self.MIN_SPEED)
            movement = MovementState(
                direction_radians=direction,
                speed=speed,
                direction_seconds_remaining=self._new_direction_duration(),
                speed_seconds_remaining=self._new_speed_duration(),
            )
            self.units.append(
                Unit(
                    unit_id=f"unit-{index:03d}",
                    position=position,
                    movement=movement,
                )
            )

    def run_iteration(
        self,
        elapsed_seconds: float = DEFAULT_UPDATE_INTERVAL_SECONDS,
    ) -> List[Unit]:
        """Move every unit for one time step without generating telemetry."""
        if elapsed_seconds <= 0.0:
            raise ValueError("elapsed_seconds must be positive")

        for unit in self.units:
            position = unit.position
            movement = unit.movement

            if movement.direction_seconds_remaining <= 0.0:
                self._change_direction(movement)
            if movement.speed_seconds_remaining <= 0.0:
                self._change_speed(movement)

            distance = movement.speed * elapsed_seconds
            # Modulo wraps units crossing any map edge to the opposite side.
            position.x = (
                position.x + math.cos(movement.direction_radians) * distance
            ) % self.area_width
            position.y = (
                position.y + math.sin(movement.direction_radians) * distance
            ) % self.area_height
            movement.direction_seconds_remaining -= elapsed_seconds
            movement.speed_seconds_remaining -= elapsed_seconds

        return self.get_units()

    def run_movement_loop(
        self,
        *,
        iterations: int | None = None,
        interval_seconds: float = DEFAULT_UPDATE_INTERVAL_SECONDS,
        sleep_fn: Callable[[float], None] = time.sleep,
    ) -> List[Unit]:
        """Move units on a timed loop, or continuously when iterations is None."""
        if iterations is not None and iterations < 0:
            raise ValueError("iterations must be non-negative or None")
        if interval_seconds <= 0.0:
            raise ValueError("interval_seconds must be positive")

        completed_iterations = 0
        while iterations is None or completed_iterations < iterations:
            sleep_fn(interval_seconds)
            self.run_iteration(elapsed_seconds=interval_seconds)
            completed_iterations += 1

        return self.get_units()

    def print_state(self) -> None:
        """Print only the current simulation state without generating telemetry."""
        print("Current simulation state:")
        for unit in self.units:
            position = unit.position
            print(f"  {unit.unit_id}: position=({position.x:.2f}, {position.y:.2f})")


def initialize_simulation(
    num_units: int,
    seed: int,
    *,
    area_width: float = 100.0,
    area_height: float = 100.0,
) -> Simulation:
    """Create and return an independent initialized simulation run."""
    return Simulation(
        num_units=num_units,
        seed=seed,
        area_width=area_width,
        area_height=area_height,
    )


if __name__ == "__main__":
    initialize_simulation(num_units=3, seed=42).print_state()
