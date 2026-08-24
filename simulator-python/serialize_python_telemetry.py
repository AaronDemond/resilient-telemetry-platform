"""Serialize a Python-generated TelemetryMessage to bytes for C++ round-trip tests.

This script intentionally uses the generated protobuf Python classes from the
project build output so the C++ and Python sides share the same wire contract.
"""

from __future__ import annotations

import sys
from pathlib import Path

from simulator import Unit
from telemetry_message_builder import create_telemetry_message


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: serialize_python_telemetry.py <output_path>")

    output_path = Path(sys.argv[1])
    output_path.parent.mkdir(parents=True, exist_ok=True)

    unit = Unit(unit_id="unit-python-roundtrip")
    message = create_telemetry_message(
        unit,
        message_id="msg-python-roundtrip",
        run_id="run-python-roundtrip",
        boot_id="boot-python-roundtrip",
        sequence_number=42,
        software_version="1.2.3",
    )

    output_path.write_bytes(message.SerializeToString())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
