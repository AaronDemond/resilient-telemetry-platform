"""Utilities for generating random telemetry data for simulator testing.

This module intentionally uses the generated protobuf classes as the canonical
contract representation for telemetry messages. The in-memory Unit object below
is a lightweight simulator model that keeps the unit_id alongside any future
fields we add for testing.
"""

from __future__ import annotations

import asyncio
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Protocol, cast

from google.protobuf.message import Message


def _load_dotenv_values() -> dict[str, str]:
    """Load repo-local .env values for local simulator/ingestor wiring."""
    values: dict[str, str] = {}
    project_root = Path(__file__).resolve().parent.parent
    for candidate in (project_root / ".env", Path.cwd() / ".env"):
        if not candidate.is_file():
            continue

        for raw_line in candidate.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"')
            if key:
                values[key] = value

    return values


def _resolve_environment_value(name: str, default: str) -> str:
    """Prefer the process environment, then the repo-local .env values."""
    value = os.environ.get(name)
    if value:
        return value

    value = _load_dotenv_values().get(name)
    if value:
        return value

    return default


def _publish_telemetry_to_ingestor(message: Message) -> None:
    """Best-effort publish of a generated message to the JetStream ingestor."""
    try:
        from nats.aio.client import Client as NATS
        from nats.js.api import RetentionPolicy, StorageType, StreamConfig
        from nats.js.errors import NotFoundError
    except ModuleNotFoundError:
        return

    nats_url = _resolve_environment_value("TELEMETRY_NATS_URL", "nats://127.0.0.1:14222")
    stream_name = _resolve_environment_value("TELEMETRY_TEST_STREAM", "TELEMETRY_TEST_STREAM")
    subject = _resolve_environment_value("TELEMETRY_TEST_SUBJECT", "telemetry.test.ingestor")

    async def _publish() -> None:
        nc = NATS()
        try:
            await nc.connect(servers=[nats_url], name="telemetry-simulator")
            js = nc.jetstream()
            config = StreamConfig(
                name=stream_name,
                subjects=[subject],
                retention=RetentionPolicy.LIMITS,
                storage=StorageType.FILE,
                max_msgs=-1,
                max_bytes=-1,
            )

            try:
                info = await js.stream_info(stream_name)
                current_config = info.config
                if (
                    current_config.subjects != [subject]
                    or current_config.max_msgs != -1
                    or current_config.max_bytes != -1
                ):
                    await js.update_stream(stream_name, config)
            except NotFoundError:
                await js.add_stream(config)

            await js.publish(subject, message.SerializeToString())
        finally:
            await nc.close()

    try:
        asyncio.run(_publish())
    except RuntimeError:
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(_publish())
        finally:
            loop.close()
    except Exception as exc:  # pragma: no cover - best effort for local dev
        print(
            f"Telemetry publish skipped: {exc}",
            file=sys.stderr,
        )


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
class MovementState:
    """Persistent direction and speed state for one moving unit."""

    direction_radians: float = 0.0
    speed: float = 0.0
    direction_seconds_remaining: float = 0.0
    speed_seconds_remaining: float = 0.0

    def __post_init__(self) -> None:
        """Validate movement values before the simulation uses them."""
        if self.speed < 0.0:
            raise ValueError("movement speed must be non-negative")
        if self.direction_seconds_remaining < 0.0:
            raise ValueError("direction duration must be non-negative")
        if self.speed_seconds_remaining < 0.0:
            raise ValueError("speed duration must be non-negative")


@dataclass
class Unit:
    """Simple simulator model for an operational unit.

    The unit keeps its identity and can store the most recently generated
    telemetry message for that unit.
    """

    unit_id: str
    position: Position = field(default_factory=Position)
    movement: MovementState = field(default_factory=MovementState)
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
