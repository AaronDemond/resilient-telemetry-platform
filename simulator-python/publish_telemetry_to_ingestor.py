"""Publish one test telemetry message to the JetStream ingestor.

Run the ingestor first, then start this script. It uses the existing simulator
message builder to create a valid TelemetryMessage, clears any stale test
messages from the stream, and publishes a fresh payload for the C++ ingestor
to print.
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path


def _bootstrap_generated_python_path() -> None:
    """Add a generated protobuf directory if the workspace has already built one."""
    override = os.environ.get("TELEMETRY_PROTO_PYTHON_DIR")
    if override:
        candidate = Path(override)
        if candidate.is_dir() and (candidate / "telemetry" / "v1" / "telemetry_message_pb2.py").is_file():
            sys.path.insert(0, str(candidate))
            return

    project_root = Path(__file__).resolve().parent.parent
    for build_root in (project_root / "build", project_root / "cpp" / "build"):
        for candidate in sorted(build_root.glob("*/generated/python")):
            if candidate.is_dir() and (candidate / "telemetry" / "v1" / "telemetry_message_pb2.py").is_file():
                sys.path.insert(0, str(candidate))
                return


_bootstrap_generated_python_path()

from nats.aio.client import Client as NATS
from nats.js.api import RetentionPolicy, StorageType, StreamConfig
from nats.js.errors import NotFoundError

from simulator import Unit
from telemetry_message_builder import create_telemetry_message


NATS_URL = os.environ.get("TELEMETRY_NATS_URL", "nats://127.0.0.1:14222")
STREAM_NAME = os.environ.get("TELEMETRY_TEST_STREAM", "TELEMETRY_TEST_STREAM")
SUBJECT = os.environ.get("TELEMETRY_TEST_SUBJECT", "telemetry.test.ingestor")


async def ensure_stream(js) -> None:
    """Create the test stream once so the sender can publish through JetStream."""
    try:
        await js.stream_info(STREAM_NAME)
    except NotFoundError:
        config = StreamConfig(
            name=STREAM_NAME,
            subjects=[SUBJECT],
            retention=RetentionPolicy.LIMITS,
            storage=StorageType.FILE,
            max_msgs=1,
        )
        await js.add_stream(config)


async def main() -> int:
    nc = NATS()
    await nc.connect(servers=[NATS_URL], name="telemetry-jetstream-sender")

    try:
        js = nc.jetstream()
        await ensure_stream(js)

        # Remove any message left over from a previous run so the ingestor prints
        # the payload produced by this invocation.
        await js.purge_stream(STREAM_NAME)

        unit = Unit(unit_id="unit-jetstream-test")
        message = create_telemetry_message(
            unit,
            message_id="msg-jetstream-test",
            run_id="run-jetstream-test",
            boot_id="boot-jetstream-test",
            sequence_number=1,
            software_version="1.0.0",
        )

        ack = await js.publish(SUBJECT, message.SerializeToString())
        print(
            f"Published {message.envelope.message_id} to {SUBJECT} "
            f"(stream={ack.stream}, seq={ack.seq})"
        )
        return 0
    finally:
        await nc.close()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))