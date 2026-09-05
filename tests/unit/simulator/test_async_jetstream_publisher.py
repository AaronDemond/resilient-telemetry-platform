"""Verify the simulator's async JetStream publisher stays out of the hot path."""

from __future__ import annotations

import time
import unittest
from types import SimpleNamespace

from async_jetstream_publisher import AsyncJetStreamPublisher


class FakeJetStream:
    def __init__(self, owner):
        self.owner = owner

    async def stream_info(self, _stream_name):
        raise RuntimeError("stream not created yet")

    async def add_stream(self, config):
        self.owner.stream_config = config

    async def publish(self, subject, payload):
        self.owner.messages.append((subject, payload))
        return SimpleNamespace(stream="test", seq=len(self.owner.messages))


class FakeNATS:
    def __init__(self):
        self.messages = []
        self.stream_config = None

    async def connect(self, servers, name):
        self.servers = servers
        self.name = name

    def jetstream(self):
        return FakeJetStream(self)

    async def close(self):
        return None


class AsyncJetStreamPublisherTest(unittest.TestCase):
    def test_publish_queues_messages_for_background_delivery(self) -> None:
        fake_nats = FakeNATS()
        publisher = AsyncJetStreamPublisher(
            nats_url="nats://example:4222",
            stream_name="TELEMETRY_TEST_STREAM",
            subject="telemetry.test.ingestor",
            queue_size=8,
            retry_delay=0.01,
            nats_factory=lambda: fake_nats,
        )

        publisher.publish(b"alpha-message")
        deadline = time.time() + 1.0
        while not fake_nats.messages and time.time() < deadline:
            time.sleep(0.02)

        self.assertTrue(fake_nats.messages)
        self.assertEqual(fake_nats.messages[0][0], "telemetry.test.ingestor")
        self.assertEqual(fake_nats.messages[0][1], b"alpha-message")

        publisher.close(drain_timeout=1.0)


if __name__ == "__main__":
    unittest.main()
