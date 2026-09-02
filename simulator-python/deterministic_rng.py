"""A stable, project-owned PRNG used to keep simulations reproducible."""

from __future__ import annotations

from typing import Iterable, Sequence, overload


class StablePRNG:
    """A deterministic PRNG with a 64-bit state and exact resume support."""

    _MASK64 = (1 << 64) - 1
    _UINT53_MASK = (1 << 53) - 1

    def __init__(self, seed: int | None = None, *, state: int | None = None, draw_count: int = 0) -> None:
        if seed is None:
            seed = 0
        if not 0 <= int(seed) <= 0xFFFFFFFF:
            raise ValueError("seed must be an unsigned 32-bit integer")
        self.seed = int(seed) & 0xFFFFFFFF
        self.state = int(state) & self._MASK64 if state is not None else (self.seed ^ 0x9E3779B97F4A7C15) & self._MASK64
        self.draw_count = int(draw_count)

    def clone(self) -> "StablePRNG":
        """Return a detached copy that preserves the exact current state."""
        return StablePRNG(seed=self.seed, state=self.state, draw_count=self.draw_count)

    def _next_u64(self) -> int:
        """Advance the generator and return the next unsigned 64-bit value."""
        x = self.state & self._MASK64
        x = (x + 0x9E3779B97F4A7C15) & self._MASK64
        z = x
        z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9 & self._MASK64
        z = (z ^ (z >> 27)) * 0x94D049BB133111EB & self._MASK64
        self.state = (z ^ (z >> 31)) & self._MASK64
        self.draw_count += 1
        return self.state

    def random(self) -> float:
        """Return a float in the range [0.0, 1.0)."""
        return ((self._next_u64() >> 11) & self._UINT53_MASK) / float(1 << 53)

    def uniform(self, low: float, high: float) -> float:
        """Return a uniform float between low and high, inclusive of low, exclusive of high."""
        if low > high:
            low, high = high, low
        return low + (high - low) * self.random()

    def randint(self, low: int, high: int) -> int:
        """Return a random integer in [low, high]."""
        if low > high:
            low, high = high, low
        return low + self._randbelow(high - low + 1)

    def _randbelow(self, limit: int) -> int:
        if limit <= 0:
            raise ValueError("limit must be positive")
        if limit == 1:
            return 0

        bits = limit.bit_length()
        while True:
            value = self._next_u64() >> (64 - bits)
            if value < limit:
                return int(value)

    def choice(self, sequence: Sequence[object]) -> object:
        """Return one item from the sequence, preserving deterministic behavior."""
        if not sequence:
            raise IndexError("Cannot choose from an empty sequence")
        return sequence[self._randbelow(len(sequence))]

    def choices(self, population: Sequence[object], weights: Sequence[float] | None = None, *, k: int = 1) -> list[object]:
        """Select k items using the supplied weights, matching the random.Random API."""
        if k < 0:
            raise ValueError("k must be non-negative")
        if not population:
            raise IndexError("Cannot choose from an empty population")
        if weights is None:
            return [self.choice(population) for _ in range(k)]
        if len(population) != len(weights):
            raise ValueError("weights and population lengths must match")
        total_weight = sum(float(weight) for weight in weights)
        if total_weight <= 0.0:
            raise ValueError("sum of weights must be positive")
        selected: list[object] = []
        for _ in range(k):
            threshold = self.random() * total_weight
            cumulative = 0.0
            for item, weight in zip(population, weights, strict=True):
                cumulative += float(weight)
                if threshold <= cumulative:
                    selected.append(item)
                    break
            else:
                selected.append(population[-1])
        return selected

    def state_dict(self) -> dict[str, int]:
        """Return the generator state that can be saved for exact continuation."""
        return {"seed": self.seed, "state": self.state, "draw_count": self.draw_count}

    @classmethod
    def from_state(cls, payload: dict[str, int]) -> "StablePRNG":
        """Restore a generator from its persisted state."""
        return cls(seed=int(payload.get("seed", 0)), state=int(payload.get("state", 0)), draw_count=int(payload.get("draw_count", 0)))


__all__ = ["StablePRNG"]
