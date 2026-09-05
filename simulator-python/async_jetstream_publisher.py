"""Asynchronous JetStream publisher used by the simulator.

The simulator publishes generated protobuf bytes without blocking its own unit
movement loop. Messages are queued in a background thread and sent to NATS
JetStream on a dedicated connection. This keeps the simulation responsive while
still making delivery reliable enough for local ingestion tests.
"""

from __future__ import annotations

import asyncio
import os
import queue
import threading
import time
from pathlib import Path
from typing import Any


def _load_dotenv_values() -> dict[str, str]:
    """Read repo-local settings so local dev stays portable across hosts."""
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
    """Prefer process-environment values before repo-local .env settings."""
    value = os.environ.get(name)
    if value:
        return value
    value = _load_dotenv_values().get(name)
    if value:
        return value
    return default


class AsyncJetStreamPublisher:
    """Background publisher that drains a bounded queue into NATS JetStream."""

    def __init__(
        self,
        *,
        nats_url: str | None = None,
        stream_name: str | None = None,
        subject: str | None = None,
        queue_size: int = 256,
        retry_delay: float = 1.0,
        nats_factory: Any | None = None,
    ) -> None:
        self.nats_url = nats_url or _resolve_environment_value("TELEMETRY_NATS_URL", "nats://127.0.0.1:14222")
        self.stream_name = stream_name or _resolve_environment_value("TELEMETRY_TEST_STREAM", "TELEMETRY_TEST_STREAM")
        self.subject = subject or _resolve_environment_value("TELEMETRY_TEST_SUBJECT", "telemetry.test.ingestor")
        self.queue_size = max(1, int(queue_size))
        self.retry_delay = max(0.1, float(retry_delay))
        self._queue: "queue.Queue[bytes]" = queue.Queue(maxsize=self.queue_size)
        self._stop_event = threading.Event()
        self._nats_factory = nats_factory
        self._thread: threading.Thread | None = None
        if nats_factory is not None:
            self._thread = threading.Thread(target=self._background_loop, daemon=True)
            self._thread.start()
            return
        try:
            from nats.aio.client import Client as NATS  # noqa: F401
        except ModuleNotFoundError:
            self._thread = None
            return
        self._thread = threading.Thread(target=self._background_loop, daemon=True)
        self._thread.start()

    @property
    def is_stopped(self) -> bool:
        return self._stop_event.is_set()

    def publish(self, payload: bytes | bytearray) -> None:
        """Queue a serialized telemetry payload for background delivery."""
        if self._thread is None:
            raise RuntimeError("nats-py is not installed; telemetry publisher is disabled")
        if self._stop_event.is_set():
            raise RuntimeError("jetstream publisher is closed")
        if not isinstance(payload, (bytes, bytearray)):
            raise TypeError("payload must be bytes-like")
        message = bytes(payload)
        try:
            self._queue.put_nowait(message)
        except queue.Full as exc:
            raise RuntimeError("telemetry publish queue is full") from exc

    def close(self, *, drain_timeout: float = 10.0) -> None:
        """Stop accepting new work and drain accepted payloads before exit."""
        if self._thread is None:
            return
        self._stop_event.set()
        deadline = time.monotonic() + max(0.0, float(drain_timeout))
        while not self._queue.empty() and time.monotonic() < deadline:
            time.sleep(0.05)
        self._thread.join(timeout=max(0.5, float(drain_timeout)))

    def _background_loop(self) -> None:
        """Keep a single async queue consumer alive on its own thread."""
        try:
            asyncio.run(self._async_main())
        except RuntimeError:
            loop = asyncio.new_event_loop()
            try:
                loop.run_until_complete(self._async_main())
            finally:
                loop.close()
        except Exception:
            return

    async def _async_main(self) -> None:
        """Publish queued messages until the queue is drained and the publisher is stopped."""
        connection_factory = self._nats_factory or self._default_nats_factory
        nc = connection_factory()
        try:
            await nc.connect(servers=[self.nats_url], name="telemetry-simulator")
            js = nc.jetstream()
            await self._ensure_stream(js)
            while not self._stop_event.is_set() or not self._queue.empty():
                try:
                    payload = self._queue.get(timeout=0.25)
                except queue.Empty:
                    continue

                while True:
                    try:
                        await js.publish(self.subject, payload)
                        break
                    except Exception:
                        if self._stop_event.is_set():
                            raise
                        await asyncio.sleep(self.retry_delay)

                self._queue.task_done()
        finally:
            try:
                await nc.close()
            except Exception:
                pass

    @staticmethod
    def _default_nats_factory() -> Any:
        from nats.aio.client import Client as NATS

        return NATS()

    async def _ensure_stream(self, js: Any) -> None:
        """Create the JetStream stream once so local publishes do not fail on startup."""
        try:
            from nats.js.errors import NotFoundError
            from nats.js.api import RetentionPolicy, StorageType, StreamConfig

            try:
                await js.stream_info(self.stream_name)
                return
            except NotFoundError:
                config = StreamConfig(
                    name=self.stream_name,
                    subjects=[self.subject],
                    retention=RetentionPolicy.LIMITS,
                    storage=StorageType.FILE,
                    max_msgs=-1,
                    max_bytes=-1,
                )
                await js.add_stream(config)
        except Exception:
            return
