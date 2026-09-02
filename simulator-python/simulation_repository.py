"""Persist simulation metadata and checkpoints in a portable SQLite store."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


class SimulationRepository:
    """Small repository boundary that keeps run state recoverable and testable."""

    DEFAULT_DB_PATH = Path(__file__).resolve().parent / "simulation_runs.sqlite3"

    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = Path(db_path) if db_path is not None else self.DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection: sqlite3.Connection | None = sqlite3.connect(
            str(self.db_path),
            timeout=30,
            check_same_thread=False,
        )
        self._connection.row_factory = sqlite3.Row
        self.ensure_schema()

    def close(self) -> None:
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    def __enter__(self) -> "SimulationRepository":
        return self

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        self.close()

    def _connect(self) -> sqlite3.Connection:
        if self._connection is None:
            raise RuntimeError("simulation repository connection is closed")
        return self._connection

    def ensure_schema(self) -> None:
        """Create durable tables for run metadata and generated message state."""
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS simulation_runs (
                    run_id TEXT PRIMARY KEY,
                    seed INTEGER NOT NULL,
                    unit_count INTEGER NOT NULL,
                    interval_ms INTEGER NOT NULL,
                    iteration_count INTEGER NOT NULL,
                    state TEXT NOT NULL,
                    completed_iterations INTEGER NOT NULL DEFAULT 0,
                    rng_seed INTEGER NOT NULL,
                    rng_state TEXT NOT NULL,
                    rng_draw_count INTEGER NOT NULL DEFAULT 0,
                    checkpoint_json TEXT,
                    last_error TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS simulation_run_messages (
                    run_id TEXT NOT NULL,
                    iteration_number INTEGER NOT NULL,
                    unit_id TEXT NOT NULL,
                    payload BLOB NOT NULL,
                    fingerprint TEXT NOT NULL,
                    published INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (run_id, iteration_number, unit_id),
                    FOREIGN KEY (run_id) REFERENCES simulation_runs(run_id)
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_simulation_runs_state ON simulation_runs(state)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_simulation_run_messages_run_id ON simulation_run_messages(run_id, iteration_number)"
            )

    @staticmethod
    def _normalize_integer(value: Any, *, field_name: str) -> int:
        """Accept Python ints, scientific-notation strings, and legacy float values."""
        if value is None:
            raise ValueError(f"{field_name} cannot be null")
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, int):
            return int(value)
        if isinstance(value, float):
            if value.is_integer():
                return int(value)
            return int(Decimal(str(value)).to_integral_value())

        text = str(value).strip()
        if not text:
            raise ValueError(f"{field_name} cannot be empty")
        try:
            return int(text)
        except ValueError:
            try:
                return int(Decimal(text).to_integral_value())
            except InvalidOperation as exc:
                raise ValueError(f"{field_name} is not a valid integer: {value!r}") from exc

    def _timestamp(self) -> str:
        return datetime.now(timezone.utc).isoformat(timespec="seconds")

    def create_run(
        self,
        *,
        run_id: str,
        seed: int,
        unit_count: int,
        interval_ms: int,
        iteration_count: int,
        state: str = "running",
        rng_seed: int,
        rng_state: int,
        rng_draw_count: int = 0,
        checkpoint_json: str | None = None,
        last_error: str | None = None,
    ) -> dict[str, Any]:
        """Insert a new run and return the canonical database row."""
        now = self._timestamp()
        normalized_rng_seed = self._normalize_integer(rng_seed, field_name="rng_seed")
        normalized_rng_state = self._normalize_integer(rng_state, field_name="rng_state")
        normalized_rng_draw_count = self._normalize_integer(rng_draw_count, field_name="rng_draw_count")
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO simulation_runs (
                    run_id, seed, unit_count, interval_ms, iteration_count, state,
                    completed_iterations, rng_seed, rng_state, rng_draw_count,
                    checkpoint_json, last_error, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    int(seed),
                    int(unit_count),
                    int(interval_ms),
                    int(iteration_count),
                    state,
                    normalized_rng_seed,
                    str(normalized_rng_state),
                    normalized_rng_draw_count,
                    checkpoint_json,
                    last_error,
                    now,
                    now,
                ),
            )
        return self.get_run(run_id)

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        """Load a run row by ID."""
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM simulation_runs WHERE run_id = ?",
                (run_id,),
            ).fetchone()
        if row is None:
            return None
        payload = dict(row)
        if "rng_state" in payload:
            payload["rng_state"] = self._normalize_integer(payload["rng_state"], field_name="rng_state")
        if "rng_seed" in payload:
            payload["rng_seed"] = self._normalize_integer(payload["rng_seed"], field_name="rng_seed")
        if "rng_draw_count" in payload:
            payload["rng_draw_count"] = self._normalize_integer(payload["rng_draw_count"], field_name="rng_draw_count")
        return payload

    def update_run(
        self,
        run_id: str,
        *,
        state: str | None = None,
        completed_iterations: int | None = None,
        rng_seed: int | None = None,
        rng_state: int | None = None,
        rng_draw_count: int | None = None,
        checkpoint_json: str | None = None,
        last_error: str | None = None,
    ) -> dict[str, Any]:
        """Apply a partial update to a run row."""
        existing = self.get_run(run_id)
        if existing is None:
            raise KeyError(f"unknown simulation run: {run_id}")

        next_state = state if state is not None else existing["state"]
        next_completed = completed_iterations if completed_iterations is not None else existing["completed_iterations"]
        next_rng_seed = rng_seed if rng_seed is not None else existing["rng_seed"]
        next_rng_state = rng_state if rng_state is not None else existing["rng_state"]
        next_rng_draw_count = rng_draw_count if rng_draw_count is not None else existing["rng_draw_count"]
        next_checkpoint = checkpoint_json if checkpoint_json is not None else existing["checkpoint_json"]
        next_last_error = last_error if last_error is not None else existing["last_error"]

        normalized_rng_seed = self._normalize_integer(next_rng_seed, field_name="rng_seed")
        normalized_rng_state = self._normalize_integer(next_rng_state, field_name="rng_state")
        normalized_rng_draw_count = self._normalize_integer(next_rng_draw_count, field_name="rng_draw_count")

        with self._connect() as connection:
            connection.execute(
                """
                UPDATE simulation_runs
                SET state = ?,
                    completed_iterations = ?,
                    rng_seed = ?,
                    rng_state = ?,
                    rng_draw_count = ?,
                    checkpoint_json = ?,
                    last_error = ?,
                    updated_at = ?
                WHERE run_id = ?
                """,
                (
                    next_state,
                    int(next_completed),
                    normalized_rng_seed,
                    str(normalized_rng_state),
                    normalized_rng_draw_count,
                    next_checkpoint,
                    next_last_error,
                    self._timestamp(),
                    run_id,
                ),
            )
        return self.get_run(run_id)

    def active_run_exists(self) -> bool:
        """Return True when another run is occupying the active slot."""
        with self._connect() as connection:
            row = connection.execute(
                "SELECT 1 FROM simulation_runs WHERE state IN ('running', 'paused', 'error') LIMIT 1"
            ).fetchone()
        return row is not None

    def store_message(self, *, run_id: str, iteration_number: int, unit_id: str, payload: bytes, fingerprint: str, published: int = 0) -> None:
        """Persist generated message bytes for exact comparison and replay."""
        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO simulation_run_messages (
                    run_id, iteration_number, unit_id, payload, fingerprint, published
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (run_id, int(iteration_number), unit_id, payload, fingerprint, int(published)),
            )

    def get_messages_for_run(self, run_id: str) -> list[dict[str, Any]]:
        """Return all messages for a run, sorted by iteration and unit."""
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM simulation_run_messages WHERE run_id = ? ORDER BY iteration_number, unit_id",
                (run_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def compare_runs(self, left_run_id: str, right_run_id: str) -> dict[str, Any]:
        """Compare two completed runs by their deterministic fingerprints."""
        left = self.get_run(left_run_id)
        right = self.get_run(right_run_id)
        if left is None or right is None:
            raise KeyError("both run IDs must exist")
        if left["state"] != "completed" or right["state"] != "completed":
            return {"match": False, "reason": "both runs must be completed"}

        left_messages = self.get_messages_for_run(left_run_id)
        right_messages = self.get_messages_for_run(right_run_id)
        if len(left_messages) != len(right_messages):
            return {"match": False, "reason": "message count mismatch"}

        left_by_key = {(row["iteration_number"], row["unit_id"]): row for row in left_messages}
        right_by_key = {(row["iteration_number"], row["unit_id"]): row for row in right_messages}
        if left_by_key.keys() != right_by_key.keys():
            return {"match": False, "reason": "message coverage mismatch"}

        for key in left_by_key:
            left_row = left_by_key[key]
            right_row = right_by_key[key]
            if left_row["fingerprint"] != right_row["fingerprint"]:
                return {"match": False, "reason": f"mismatch at {key[0]}/{key[1]}"}
        return {"match": True, "reason": "all messages match"}

    def list_runs(self) -> list[dict[str, Any]]:
        """Return the runs sorted by creation time."""
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM simulation_runs ORDER BY created_at DESC"
            ).fetchall()
        return [dict(row) for row in rows]

    def serialize_checkpoint(self, state: Any) -> str:
        """Serialize any checkpoint payload to JSON for database storage."""
        return json.dumps(state, sort_keys=True)

    def deserialize_checkpoint(self, payload: str | None) -> Any:
        """Deserialize a database checkpoint payload back to Python data."""
        if payload is None:
            return None
        return json.loads(payload)
