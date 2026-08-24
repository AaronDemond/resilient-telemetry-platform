"""Helpers for constructing protobuf telemetry messages for simulator testing.

This module intentionally uses the generated Python protobuf classes as the
canonical contract for telemetry payloads.
"""

from __future__ import annotations

import random
from typing import Optional

from telemetry.v1 import telemetry_event_pb2, telemetry_message_pb2

from simulator import Unit


def create_telemetry_message(
    unit: Unit,
    *,
    message_id: Optional[str] = None,
    run_id: str = "run-001",
    boot_id: str = "boot-001",
    sequence_number: int = 1,
    software_version: str = "1.0.0",
) -> telemetry_message_pb2.TelemetryMessage:
    """Build a valid TelemetryMessage for a given unit.

    The simulator is intentionally generating simple but realistic data using the
    generated protobuf message definitions instead of hand-rolled dictionaries.
    """
    message = telemetry_message_pb2.TelemetryMessage()

    message.envelope.message_id = message_id or f"msg-{sequence_number:06d}"
    message.envelope.run_id = run_id
    message.envelope.unit_id = unit.unit_id
    message.envelope.boot_id = boot_id
    message.envelope.session_id = f"session-{unit.unit_id}"
    message.envelope.sequence_number = sequence_number
    message.envelope.source_timestamp_ms = 1700000000000 + sequence_number * 1000
    message.envelope.schema_version = 1
    message.envelope.correlation_id = f"corr-{unit.unit_id}-{sequence_number:06d}"

    message.event.unit_id = unit.unit_id
    message.event.boot_id = boot_id
    message.event.schema_version = 1
    message.event.software_version = software_version
    message.event.sequence_number = sequence_number
    message.event.source_timestamp_ms = message.envelope.source_timestamp_ms
    message.event.latitude = 40.7128 + random.uniform(-0.1, 0.1)
    message.event.longitude = -74.0060 + random.uniform(-0.1, 0.1)
    message.event.fuel_remaining = 100.0 - (sequence_number % 50) * 1.5
    message.event.equipment_temperature_c = 65.0 + random.uniform(-10.0, 15.0)
    message.event.connectivity_quality = 0.75 + random.uniform(0.0, 0.2)
    message.event.health_flags.temperature_warning = sequence_number % 7 == 0
    message.event.health_flags.connectivity_degraded = sequence_number % 5 == 0
    message.event.health_flags.maintenance_required = sequence_number % 11 == 0
    message.event.status = telemetry_event_pb2.UNIT_STATUS_AVAILABLE
    message.event.correlation_id = message.envelope.correlation_id

    return message
