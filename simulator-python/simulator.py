"""Utilities for generating random telemetry data for simulator testing.

This module intentionally uses the generated protobuf classes as the canonical
contract representation for telemetry messages. The in-memory Unit object below
is a lightweight simulator model that keeps the unit_id alongside any future
fields we add for testing.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class Unit:
    """Simple simulator model for an operational unit.

    For now, the unit only needs a unit_id string, but this object provides a
    real domain object instead of a bare string so later simulator logic can add
    richer telemetry metadata without changing call sites.
    """

    unit_id: str

    def __post_init__(self) -> None:
        """Validate the model before it is used by simulator code."""
        if not self.unit_id:
            raise ValueError("unit_id must not be empty")


def generate_units(unit_count: int) -> List[Unit]:
    """Generate a list of Unit objects.

    Args:
        unit_count: Number of units to create.

    Returns:
        A list of Unit objects with unique unit_id values.
    """
    if unit_count < 0:
        raise ValueError("unit_count must be non-negative")

    return [Unit(unit_id=f"unit-{index:03d}") for index in range(unit_count)]
