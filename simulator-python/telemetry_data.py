"""Validation and deterministic generation for telemetry protobuf messages."""

from __future__ import annotations

import os
import random
from importlib import import_module
from pathlib import Path
import sys
from typing import Any

from google.protobuf.message import Message

from simulator import Unit


def _load_generated_module(module_name: str) -> Any:
    """Load a CMake-generated protobuf module or report the required setup."""
    try:
        return import_module(module_name)
    except ModuleNotFoundError as error:
        raise ModuleNotFoundError(
            "Generated telemetry protobuf modules are unavailable. Build the "
            "telemetry_proto_python CMake target and add the active build's "
            "generated/python directory to PYTHONPATH."
        ) from error


def _generated_python_directory_has_telemetry_modules(candidate: Path) -> bool:
    """Return True when a build tree contains the generated telemetry stubs."""
    telemetry_event_module = candidate / "telemetry" / "v1" / "telemetry_event_pb2.py"
    telemetry_message_module = candidate / "telemetry" / "v1" / "telemetry_message_pb2.py"
    return telemetry_event_module.is_file() and telemetry_message_module.is_file()


def _bootstrap_generated_python_path() -> None:
    """Add a generated protobuf directory if the workspace has already built one."""
    override = os.environ.get("TELEMETRY_PROTO_PYTHON_DIR")
    if override:
        candidate = Path(override)
        if candidate.is_dir() and _generated_python_directory_has_telemetry_modules(candidate):
            sys.path.insert(0, str(candidate))
            return

    project_root = Path(__file__).resolve().parent.parent
    for build_root in (project_root / "build", project_root / "cpp" / "build"):
        for candidate in sorted(build_root.glob("*/generated/python")):
            if candidate.is_dir() and _generated_python_directory_has_telemetry_modules(candidate):
                sys.path.insert(0, str(candidate))
                return


_bootstrap_generated_python_path()


telemetry_event_pb2 = _load_generated_module("telemetry.v1.telemetry_event_pb2")
telemetry_message_pb2 = _load_generated_module("telemetry.v1.telemetry_message_pb2")
TelemetryMessage = telemetry_message_pb2.TelemetryMessage


class TelemetryData:
    """Wrap and validate a generated telemetry.v1.TelemetryMessage."""

    def __init__(self, message: Message | None = None) -> None:
        self._message = TelemetryMessage()
        if message is not None:
            self.set_message(message)

    def get_message(self) -> Message:
        """Return the current generated protobuf message after validation."""
        self._ensure_valid()
        return self._message

    def set_message(self, message: Message) -> Message:
        """Clone and validate a generated TelemetryMessage."""
        if not isinstance(message, Message):
            raise TypeError("message must be a generated protobuf Message")
        if message.DESCRIPTOR.full_name != "telemetry.v1.TelemetryMessage":
            raise TypeError("message must be a telemetry.v1.TelemetryMessage")

        cloned = TelemetryMessage()
        cloned.CopyFrom(message)
        self._message = cloned
        self._ensure_valid()
        return self._message

    def _ensure_valid(self) -> None:
        """Validate the wrapped message against the v1 telemetry contract."""
        if not self._message.HasField("envelope"):
            raise ValueError("TelemetryMessage.envelope is required")
        if not self._message.HasField("event"):
            raise ValueError("TelemetryMessage.event is required")

        envelope = self._message.envelope
        event = self._message.event

        if not envelope.message_id.strip():
            raise ValueError("envelope.message_id must be non-empty")
        if not envelope.run_id.strip():
            raise ValueError("envelope.run_id must be non-empty")
        if not envelope.unit_id.strip():
            raise ValueError("envelope.unit_id must be non-empty")
        if not envelope.boot_id.strip():
            raise ValueError("envelope.boot_id must be non-empty")
        if envelope.sequence_number < 1:
            raise ValueError("envelope.sequence_number must be >= 1")
        if envelope.source_timestamp_ms < 0:
            raise ValueError("envelope.source_timestamp_ms must be >= 0")
        if envelope.schema_version < 1:
            raise ValueError("envelope.schema_version must be >= 1")

        if not event.unit_id.strip():
            raise ValueError("event.unit_id must be non-empty")
        if not event.boot_id.strip():
            raise ValueError("event.boot_id must be non-empty")
        if event.schema_version < 1:
            raise ValueError("event.schema_version must be >= 1")
        if not event.software_version.strip():
            raise ValueError("event.software_version must be non-empty")
        if event.sequence_number < 1:
            raise ValueError("event.sequence_number must be >= 1")
        if event.source_timestamp_ms < 0:
            raise ValueError("event.source_timestamp_ms must be >= 0")
        if not -90.0 <= event.latitude <= 90.0:
            raise ValueError("event.latitude must be in the range [-90.0, 90.0]")
        if not -180.0 <= event.longitude <= 180.0:
            raise ValueError("event.longitude must be in the range [-180.0, 180.0]")
        if not 0.0 <= event.fuel_remaining <= 100.0:
            raise ValueError("event.fuel_remaining must be in the range [0.0, 100.0]")
        if not -50.0 <= event.equipment_temperature_c <= 120.0:
            raise ValueError(
                "event.equipment_temperature_c must be in the range [-50.0, 120.0]"
            )
        if not 0.0 <= event.connectivity_quality <= 1.0:
            raise ValueError("event.connectivity_quality must be in the range [0.0, 1.0]")
        if event.status == telemetry_event_pb2.UNIT_STATUS_UNSPECIFIED:
            raise ValueError("event.status must be explicitly set")

        if envelope.unit_id != event.unit_id:
            raise ValueError("envelope and event unit IDs must match")
        if envelope.boot_id != event.boot_id:
            raise ValueError("envelope and event boot IDs must match")
        if envelope.sequence_number != event.sequence_number:
            raise ValueError("envelope and event sequence numbers must match")
        if envelope.source_timestamp_ms != event.source_timestamp_ms:
            raise ValueError("envelope and event source timestamps must match")

    def serialize(self) -> bytes:
        """Serialize the validated generated protobuf message."""
        self._ensure_valid()
        return self._message.SerializeToString()


class TelemetryGenerator:
    """Generate deterministic, valid telemetry messages for simulation units."""

    def __init__(self, seed: int = 0, *, rng: random.Random | None = None) -> None:
        self._rng = rng if rng is not None else random.Random(seed)
        self._run_id = f"run-{self._rng.randint(1, 9999):04d}"
        self._boot_ids: dict[str, str] = {}
        self._sequence_numbers: dict[str, int] = {}
        self._status_by_unit: dict[str, int] = {}
        self._status_hold_remaining: dict[str, int] = {}
        self._health_flags_by_unit: dict[str, dict[str, bool]] = {}
        self._health_hold_remaining: dict[str, int] = {}

    def _status_for_unit(self, unit_id: str) -> int:
        """Keep available/returning units stable for a minimum of five iterations."""
        remaining = self._status_hold_remaining.get(unit_id, 0)
        current_status = self._status_by_unit.get(unit_id)
        if remaining > 0 and current_status is not None:
            self._status_hold_remaining[unit_id] = remaining - 1
            return current_status

        statuses = [
            telemetry_event_pb2.UNIT_STATUS_AVAILABLE,
            telemetry_event_pb2.UNIT_STATUS_EN_ROUTE,
            telemetry_event_pb2.UNIT_STATUS_RETURNING,
        ]
        status_probabilities = [
            0.01,
            0.98,
            0.01,
        ]
        selected_status = self._rng.choices(statuses, weights=status_probabilities, k=1)[0]
        self._status_by_unit[unit_id] = selected_status
        self._status_hold_remaining[unit_id] = (
            5 if selected_status in (
                telemetry_event_pb2.UNIT_STATUS_AVAILABLE,
                telemetry_event_pb2.UNIT_STATUS_RETURNING,
            ) else 0
        )
        return selected_status

    def _health_flags_for_unit(self, unit_id: str) -> dict[str, bool]:
        """Keep non-healthy states active for at least five iterations."""
        remaining = self._health_hold_remaining.get(unit_id, 0)
        current_flags = self._health_flags_by_unit.get(unit_id)
        if remaining > 0 and current_flags is not None:
            self._health_hold_remaining[unit_id] = remaining - 1
            return current_flags

        selected_flags = {
            "temperature_warning": self._rng.random() < 0.05,
            "connectivity_degraded": self._rng.random() < 0.05,
            "maintenance_required": self._rng.random() < 0.05,
        }
        self._health_flags_by_unit[unit_id] = selected_flags
        self._health_hold_remaining[unit_id] = 5 if any(selected_flags.values()) else 0
        return selected_flags

    def generate_random_data(self, unit: Unit) -> Message:
        """Generate a validated protobuf message describing one unit."""
        if not isinstance(unit, Unit):
            raise TypeError("unit must be a Unit instance")

        unit_id = unit.unit_id
        if unit_id not in self._boot_ids:
            self._boot_ids[unit_id] = f"boot-{self._rng.randint(1, 999):03d}"

        boot_id = self._boot_ids[unit_id]
        sequence_number = self._sequence_numbers.get(unit_id, 0) + 1
        self._sequence_numbers[unit_id] = sequence_number
        timestamp_ms = 1_700_000_000_000 + sequence_number * 1_000
        message = TelemetryMessage()

        message.envelope.message_id = f"msg-{unit_id}-{sequence_number:06d}"
        message.envelope.run_id = self._run_id
        message.envelope.unit_id = unit_id
        message.envelope.boot_id = boot_id
        message.envelope.session_id = f"session-{boot_id}"
        message.envelope.sequence_number = sequence_number
        message.envelope.source_timestamp_ms = timestamp_ms
        message.envelope.schema_version = 1
        message.envelope.correlation_id = f"corr-{unit_id}-{sequence_number:06d}"

        message.event.unit_id = unit_id
        message.event.boot_id = boot_id
        message.event.schema_version = 1
        message.event.software_version = "1.0.0"
        message.event.sequence_number = sequence_number
        message.event.source_timestamp_ms = timestamp_ms
        message.event.latitude = unit.position.latitude
        message.event.longitude = unit.position.longitude
        message.event.fuel_remaining = self._rng.uniform(0.0, 100.0)
        message.event.equipment_temperature_c = self._rng.uniform(-20.0, 120.0)
        message.event.connectivity_quality = self._rng.uniform(0.0, 1.0)

        health_flags = self._health_flags_for_unit(unit_id)
        message.event.health_flags.temperature_warning = health_flags["temperature_warning"]
        message.event.health_flags.connectivity_degraded = health_flags["connectivity_degraded"]
        message.event.health_flags.maintenance_required = health_flags["maintenance_required"]
        message.event.status = self._status_for_unit(unit_id)
        message.event.correlation_id = message.envelope.correlation_id

        return TelemetryData(message).get_message()


__all__ = ["TelemetryData", "TelemetryGenerator"]
