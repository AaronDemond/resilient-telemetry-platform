"""Utilities for generating random telemetry data for simulator testing.

This module intentionally uses the generated protobuf classes as the canonical
contract representation for telemetry messages. The in-memory Unit object below
is a lightweight simulator model that keeps the unit_id alongside any future
fields we add for testing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Protocol, cast

from google.protobuf.message import Message


class TelemetryEnvelope(Protocol):
    """Typed envelope fields used by the simulator."""

    message_id: str
    run_id: str
    unit_id: str
    boot_id: str
    sequence_number: int


class TelemetryEvent(Protocol):
    """Typed event fields used by the simulator."""

    unit_id: str
    boot_id: str
    sequence_number: int
    latitude: float
    longitude: float
    status: int


class TelemetryMessageView(Protocol):
    """Structural view of the generated TelemetryMessage API."""

    envelope: TelemetryEnvelope
    event: TelemetryEvent

    def SerializeToString(self) -> bytes:
        """Serialize the generated protobuf message."""


@dataclass
class Position:
    """A unit position within a bounded simulation area."""

    x: float = 0.0
    y: float = 0.0
    area_width: float = 100.0
    area_height: float = 100.0

    def __post_init__(self) -> None:
        """Validate the position and its coordinate bounds."""
        if self.area_width <= 0.0 or self.area_height <= 0.0:
            raise ValueError("position area dimensions must be positive")
        if not 0.0 <= self.x <= self.area_width:
            raise ValueError("position x must be within the simulation area")
        if not 0.0 <= self.y <= self.area_height:
            raise ValueError("position y must be within the simulation area")

    @property
    def latitude(self) -> float:
        """Map the simulation y coordinate to a valid latitude."""
        return (self.y / self.area_height) * 180.0 - 90.0

    @property
    def longitude(self) -> float:
        """Map the simulation x coordinate to a valid longitude."""
        return (self.x / self.area_width) * 360.0 - 180.0


@dataclass
class Unit:
    """Simple simulator model for an operational unit.

    The unit keeps its identity and can store the most recently generated
    telemetry message for that unit.
    """

    unit_id: str
    position: Position = field(default_factory=Position)
    telemetry_message: TelemetryMessageView | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        """Validate the model before it is used by simulator code."""
        if not self.unit_id:
            raise ValueError("unit_id must not be empty")

    def attach_telemetry_message(self, message: Message) -> None:
        """Attach a generated protobuf telemetry message to this unit."""
        if not isinstance(message, Message):
            raise TypeError("telemetry message must be a generated protobuf Message")
        self.telemetry_message = cast(TelemetryMessageView, message)

    def get_telemetry_message(self) -> TelemetryMessageView:
        """Return the attached telemetry message or fail if none was generated."""
        if self.telemetry_message is None:
            raise RuntimeError(f"no telemetry message has been generated for {self.unit_id}")
        return self.telemetry_message


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
