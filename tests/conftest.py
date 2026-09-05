from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXTRA_PATHS = [
    ROOT / "simulator-python",
    ROOT / "build" / "generated" / "python",
    ROOT / "generated" / "python",
]

for candidate in EXTRA_PATHS:
    candidate_str = str(candidate)
    if candidate.exists() and candidate_str not in sys.path:
        sys.path.insert(0, candidate_str)
