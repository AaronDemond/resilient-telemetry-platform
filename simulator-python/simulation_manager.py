"""Manage run lifecycle, state transitions, and deterministic comparison."""

from __future__ import annotations

import hashlib
import threading
import time
from uuid import uuid4

from initialize import initialize_simulation
from simulation_repository import SimulationRepository


class SimulationManager:
    """Own the single-active-run lifecycle used by the browser control API."""

    def __init__(self, repository: SimulationRepository | None = None) -> None:
        self.repository = repository or SimulationRepository()
        self._lock = threading.RLock()
        self._active_simulations: dict[str, object] = {}
        self._run_flags: dict[str, dict[str, bool]] = {}

    def _state_for_run(self, run_id: str) -> dict[str, bool]:
        flags = self._run_flags.setdefault(run_id, {"pause_requested": False, "stop_requested": False})
        return flags

    def _run_loop(self, run_id: str) -> None:
        run = self.repository.get_run(run_id)
        if run is None:
            return

        simulation = initialize_simulation(
            num_units=int(run["unit_count"]),
            seed=int(run["seed"]),
            run_id=run_id,
        )
        self._active_simulations[run_id] = simulation
        completed_iterations = int(run["completed_iterations"])
        interval_seconds = max(0.25, float(run["interval_ms"]) / 1000.0)

        try:
            while True:
                flags = self._state_for_run(run_id)
                if flags["pause_requested"]:
                    flags["pause_requested"] = False
                    self.repository.update_run(run_id, state="paused")
                    return
                if flags["stop_requested"]:
                    flags["stop_requested"] = False
                    self.repository.update_run(run_id, state="stopped")
                    return

                simulation.run_iteration(elapsed_seconds=interval_seconds)
                for unit in simulation.get_units():
                    simulation.generate_telemetry(unit)
                    message = unit.get_telemetry_message()
                    payload = message.SerializeToString()
                    self.repository.store_message(
                        run_id=run_id,
                        iteration_number=completed_iterations + 1,
                        unit_id=unit.unit_id,
                        payload=payload,
                        fingerprint=hashlib.sha256(payload).hexdigest(),
                        published=1,
                    )

                completed_iterations += 1
                self.repository.update_run(
                    run_id,
                    state="running",
                    completed_iterations=completed_iterations,
                    rng_seed=int(run["seed"]),
                    rng_state=int(simulation.rng.state),
                    rng_draw_count=int(simulation.rng.draw_count),
                )

                if completed_iterations >= int(run["iteration_count"]):
                    self.repository.update_run(
                        run_id,
                        state="completed",
                        completed_iterations=completed_iterations,
                        rng_seed=int(run["seed"]),
                        rng_state=int(simulation.rng.state),
                        rng_draw_count=int(simulation.rng.draw_count),
                    )
                    self._active_simulations.pop(run_id, None)
                    self._run_flags.pop(run_id, None)
                    return

                time.sleep(interval_seconds)
        except Exception as exc:
            self.repository.update_run(run_id, state="error", last_error=str(exc))
            self._active_simulations.pop(run_id, None)
            self._run_flags.pop(run_id, None)

    def start_run(
        self,
        *,
        seed: int,
        unit_count: int,
        interval_ms: int,
        iteration_count: int,
    ) -> dict[str, object]:
        """Create a fresh run, persist the active state, and kick off the background loop."""
        with self._lock:
            if self.repository.active_run_exists():
                raise RuntimeError("another simulation is already active")

            run_id = str(uuid4())
            simulation = initialize_simulation(
                num_units=int(unit_count),
                seed=int(seed),
                run_id=run_id,
            )
            prng_state = simulation.rng.state_dict()
            checkpoint_payload = self.repository.serialize_checkpoint(
                {
                    "seed": int(seed),
                    "state": prng_state,
                    "unit_count": int(unit_count),
                    "run_id": run_id,
                    "completed_iterations": 0,
                }
            )
            run = self.repository.create_run(
                run_id=run_id,
                seed=int(seed),
                unit_count=int(unit_count),
                interval_ms=int(interval_ms),
                iteration_count=int(iteration_count),
                state="running",
                rng_seed=int(seed),
                rng_state=int(prng_state["state"]),
                rng_draw_count=int(prng_state["draw_count"]),
                checkpoint_json=checkpoint_payload,
                last_error=None,
            )
            self._active_simulations[run_id] = simulation
            self._run_flags.setdefault(run_id, {"pause_requested": False, "stop_requested": False})

            print(f"Started simulation run_id={run_id}")
            thread = threading.Thread(target=self._run_loop, args=(run_id,), daemon=True)
            thread.start()
            return run

    def get_run(self, run_id: str) -> dict[str, object] | None:
        """Return the persisted row for a run by ID."""
        return self.repository.get_run(run_id)

    def get_current_run(self) -> dict[str, object] | None:
        """Return the most recently created non-completed run for the browser's current session."""
        runs = self.repository.list_runs()
        for run in runs:
            if run["state"] in {"running", "paused", "stopped", "error"}:
                return run
        return None

    def pause_current_run(self) -> dict[str, object]:
        """Pause whichever run is currently active for the browser session."""
        current = self.get_current_run()
        if current is None:
            raise KeyError("no active run")
        return self.pause_run(current["run_id"])

    def stop_current_run(self) -> dict[str, object]:
        """Stop whichever run is currently active for the browser session."""
        current = self.get_current_run()
        if current is None:
            raise KeyError("no active run")
        return self.stop_run(current["run_id"])

    def pause_run(self, run_id: str) -> dict[str, object]:
        """Pause a running simulation without losing the current deterministic state."""
        with self._lock:
            run = self.repository.get_run(run_id)
            if run is None:
                raise KeyError(f"unknown run_id: {run_id}")
            if run["state"] not in {"running", "paused", "error"}:
                raise RuntimeError("run cannot be paused in its current state")
            self._state_for_run(run_id)["pause_requested"] = True
            return self.repository.update_run(run_id, state="paused")

    def stop_run(self, run_id: str) -> dict[str, object]:
        """Stop a run while preserving its state for a future continue."""
        with self._lock:
            run = self.repository.get_run(run_id)
            if run is None:
                raise KeyError(f"unknown run_id: {run_id}")
            if run["state"] == "completed":
                raise RuntimeError("completed runs cannot be stopped")
            self._state_for_run(run_id)["stop_requested"] = True
            return self.repository.update_run(run_id, state="stopped")

    def continue_run(self, run_id: str) -> dict[str, object]:
        """Continue a stopped or paused run using its saved checkpoint."""
        with self._lock:
            run = self.repository.get_run(run_id)
            if run is None:
                raise KeyError(f"unknown run_id: {run_id}")
            if run["state"] == "completed":
                raise RuntimeError("completed runs cannot be continued")
            if self.repository.active_run_exists():
                raise RuntimeError("another run is active")
            self._state_for_run(run_id)["pause_requested"] = False
            self._state_for_run(run_id)["stop_requested"] = False
            run = self.repository.update_run(run_id, state="running")
            print(f"Continued simulation run_id={run_id}")
            thread = threading.Thread(target=self._run_loop, args=(run_id,), daemon=True)
            thread.start()
            return run

    def compare_runs(self, left_run_id: str, right_run_id: str) -> dict[str, object]:
        """Compare two completed runs by normalized message fingerprints."""
        return self.repository.compare_runs(left_run_id, right_run_id)


__all__ = ["SimulationManager"]
