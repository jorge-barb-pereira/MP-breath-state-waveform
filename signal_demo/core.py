"""General arithmetic methods and deliberately invented teaching examples."""

from dataclasses import dataclass
import math
import random
from statistics import fmean, pstdev


SAMPLE_RATE = 50


@dataclass(frozen=True)
class Window:
    start_seconds: float
    spread: float
    mean_step: float
    state: str


def synthetic_signal(seed: int = 7) -> list[float]:
    """Invent three shapes; do not derive parameters from real measurements."""
    rng = random.Random(seed)
    samples = []
    for index in range(12 * SAMPLE_RATE):
        time = index / SAMPLE_RATE
        if time < 4:
            value = rng.uniform(-0.04, 0.04)
        elif time < 8:
            value = 0.8 * math.sin(2 * math.pi * 1.5 * time)
            value += rng.uniform(-0.02, 0.02)
        else:
            value = 0.7 * math.sin(2 * math.pi * 13 * time)
            value += rng.uniform(-0.3, 0.3)
        samples.append(value)
    return samples


def _validated(samples: list[float]) -> list[float]:
    values = list(samples)
    if not values or not all(math.isfinite(value) for value in values):
        raise ValueError("Samples must be nonempty and finite.")
    return values


def moving_average(samples: list[float], width: int = 3) -> list[float]:
    """Centered mean with shorter, normalized windows at the boundaries."""
    values = _validated(samples)
    if isinstance(width, bool) or not isinstance(width, int) or width < 1 or width % 2 == 0:
        raise ValueError("Width must be a positive odd integer.")
    radius = width // 2
    return [
        fmean(values[max(0, index - radius):index + radius + 1])
        for index in range(len(values))
    ]


def analyze(samples: list[float], sample_rate: int = SAMPLE_RATE) -> list[Window]:
    """Assign descriptive, nonclinical labels to complete one-second windows."""
    values = _validated(samples)
    if isinstance(sample_rate, bool) or not isinstance(sample_rate, int) or sample_rate < 2:
        raise ValueError("Sample rate must be an integer of at least two.")
    if len(values) % sample_rate:
        raise ValueError("Samples must contain complete one-second windows.")
    windows = []
    for offset in range(0, len(values), sample_rate):
        segment = values[offset:offset + sample_rate]
        spread = pstdev(segment)
        step = fmean(abs(right - left) for left, right in zip(segment, segment[1:]))
        state = "quiet" if spread < 0.1 else "varying" if step > 0.3 else "oscillating"
        windows.append(Window(offset / sample_rate, spread, step, state))
    return windows


def ascii_trace(samples: list[float], columns: int = 72) -> str:
    """Render evenly selected samples on a fixed, synthetic display scale."""
    values = _validated(samples)
    if isinstance(columns, bool) or not isinstance(columns, int) or columns < 2:
        raise ValueError("Columns must be an integer of at least two.")
    levels = " .:-=+*#%@"
    indices = [round(index * (len(values) - 1) / (columns - 1)) for index in range(columns)]
    return "".join(
        levels[round(max(0.0, min(1.0, (values[index] + 1) / 2)) * (len(levels) - 1))]
        for index in indices
    )
