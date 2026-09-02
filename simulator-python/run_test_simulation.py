"""Run a short seeded simulation through ten steps and print generated telemetry."""

from __future__ import annotations

import random
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SIMULATOR_DIR = PROJECT_ROOT / "simulator-python"
GENERATED_DIR = PROJECT_ROOT / "build" / "debug" / "generated" / "python"

for entry in (str(SIMULATOR_DIR), str(GENERATED_DIR)):
    if entry not in sys.path:
        sys.path.insert(0, entry)

from initialize import initialize_simulation


def main() -> int:
    seed = random.randint(0, 1_000_000)
    simulation = initialize_simulation(num_units=15, seed=seed)
    print(f"Simulation run ID: {simulation.run_id}")
    success_count = 0

    for step in range(1, 11):
        try:
            units = simulation.run_iteration(elapsed_seconds=1.0)
            print(f"\nStep {step}: iteration succeeded (seed={seed})")

            for unit in units:
                simulation.generate_telemetry(unit)
                message = unit.get_telemetry_message()
                print(
                    f"  {unit.unit_id}: OK -> msg={message.envelope.message_id}, "
                    f"lat={message.event.latitude:.4f}, lon={message.event.longitude:.4f}, "
                    f"status={message.event.status}"
                )
                success_count += 1

            print(f"Step {step}: SUCCESS ({len(units)} unit messages generated)")
            if step < 10:
                print("Waiting 3 seconds before the next iteration...")
                time.sleep(3)
        except Exception as exc:  # pragma: no cover - explicit runtime visibility
            print(f"Step {step}: FAILURE -> {exc}")
            print("Simulation run stopping early due to exception.")
            input("Press Enter to close this window... ")
            return 1

    print(f"\nSimulation complete: {success_count} telemetry messages generated across 10 steps.")
    print(f"Seed used: {seed}")
    print("All iterations succeeded.")
    input("Press Enter to close this window... ")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nSimulation interrupted by user.")
        input("Press Enter to close this window... ")
        raise SystemExit(130)
