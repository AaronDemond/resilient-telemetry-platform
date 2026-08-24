"""Initialize the simulator with a reproducible random state."""

from __future__ import annotations

import random
from typing import List

from simulator import Position, Unit
from telemetry_data import TelemetryGenerator


class Simulation:
    """Own an independent, deterministic simulation run."""

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
            self.units.append(Unit(unit_id=f"unit-{index:03d}", position=position))

    def run_iteration(self, max_position_delta: float = 5.0) -> List[Unit]:
        """Advance every unit once and attach its newly generated telemetry."""
        if max_position_delta < 0.0:
            raise ValueError("max_position_delta must be non-negative")

        for unit in self.units:
            position = unit.position
            position.x = min(
                self.area_width,
                max(0.0, position.x + self.rng.uniform(-max_position_delta, max_position_delta)),
            )
            position.y = min(
                self.area_height,
                max(0.0, position.y + self.rng.uniform(-max_position_delta, max_position_delta)),
            )
            self.generate_telemetry(unit)

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
