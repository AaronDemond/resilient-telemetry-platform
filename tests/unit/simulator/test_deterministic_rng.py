"""Verify the project-owned deterministic PRNG remains stable and resumable."""

from __future__ import annotations

import unittest

import tempfile
from decimal import Decimal
from pathlib import Path

from deterministic_rng import StablePRNG
from simulation_repository import SimulationRepository


class StablePRNGTest(unittest.TestCase):
    """Check deterministic, restore-safe generator behavior."""

    def test_seed_reproduces_same_sequence(self) -> None:
        left = StablePRNG(12345)
        right = StablePRNG(12345)
        left_values = [left.random() for _ in range(25)]
        right_values = [right.random() for _ in range(25)]
        self.assertEqual(left_values, right_values)

    def test_state_restore_matches_interrupted_execution(self) -> None:
        original = StablePRNG(4242)
        checkpoint = []
        for _ in range(12):
            checkpoint.append(original.random())
        state = original.state_dict()

        resumed = StablePRNG.from_state(state)
        next_original = [original.random() for _ in range(6)]
        next_resumed = [resumed.random() for _ in range(6)]

        self.assertEqual(next_original, next_resumed)

    def test_randint_and_choice_are_stable(self) -> None:
        rng = StablePRNG(9)
        value = rng.randint(1, 5)
        choice = rng.choice(["one", "two", "three"])
        self.assertIn(value, [1, 2, 3, 4, 5])
        self.assertIn(choice, ["one", "two", "three"])

    def test_random_samples_cover_the_expected_range(self) -> None:
        rng = StablePRNG(123)
        samples = [rng.uniform(0.0, 100.0) for _ in range(10)]
        self.assertTrue(all(0.0 <= value <= 100.0 for value in samples))
        self.assertTrue(any(0.0 < value < 100.0 for value in samples))

    def test_repository_can_persist_large_rng_state(self) -> None:
        rng = StablePRNG(42)
        for _ in range(50):
            rng.random()

        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / 'simulations.sqlite3'
            with SimulationRepository(db_path) as repo:
                run = repo.create_run(
                    run_id='11111111-1111-4111-8111-111111111111',
                    seed=42,
                    unit_count=2,
                    interval_ms=1000,
                    iteration_count=5,
                    state='running',
                    rng_seed=42,
                    rng_state=rng.state,
                    rng_draw_count=rng.draw_count,
                    checkpoint_json='{}',
                )

            self.assertEqual(int(run['rng_state']), rng.state)

    def test_repository_normalizes_scientific_notation_rng_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / 'simulations.sqlite3'
            with SimulationRepository(db_path) as repo:
                run = repo.create_run(
                    run_id='22222222-2222-4222-8222-222222222222',
                    seed=7,
                    unit_count=2,
                    interval_ms=500,
                    iteration_count=3,
                    state='running',
                    rng_seed=7,
                    rng_state='1.157338211246538e+19',
                    rng_draw_count=27,
                    checkpoint_json='{}',
                )
                self.assertEqual(run['rng_state'], int(Decimal('1.157338211246538E+19')))


if __name__ == "__main__":
    unittest.main()
