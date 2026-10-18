"""Independent, limited VXP 1.6 reader based on a public format description.

No header identifiers are returned. Numeric traces can still be sensitive.
See docs/vxp-processing.md for provenance, supported fields, and limitations.
"""

from dataclasses import dataclass
import math
from pathlib import Path
from statistics import fmean, pstdev

from .core import SAMPLE_RATE, moving_average, synthetic_signal


MAX_TEXT_SIZE = 2_000_000
MAX_ROWS = 20_000
FIELDS = {"amplitude", "phase", "timestamp", "validflag", "ttlin", "mark", "ttlout"}
ALIASES = {"valueofrespiratorywave": "amplitude", "phasevalue": "phase"}


class VXPError(ValueError):
    """A fixed diagnostic that never includes an input value or filename."""


@dataclass(frozen=True)
class Sample:
    seconds: float
    amplitude_mm: float
    valid: bool


@dataclass(frozen=True)
class Trace:
    samples_per_second: float
    samples: tuple[Sample, ...]


@dataclass(frozen=True)
class Features:
    start_seconds: float
    sample_count: int
    valid_count: int
    mean_mm: float | None
    spread_mm: float | None
    range_mm: float | None
    mean_step_mm: float | None


def _number(value: str) -> float:
    try:
        number = float(value)
    except (ValueError, OverflowError):
        raise VXPError("A required numeric field is invalid.") from None
    if not math.isfinite(number):
        raise VXPError("Numeric fields must be finite.")
    return number


def parse_vxp(text: str) -> Trace:
    """Parse a bounded seven-field VXP 1.6 subset, discarding header metadata.

    Return relative seconds and scaled millimeters. Do not validate a checksum,
    retain absolute timestamps, infer missing samples, or interpret phase/TTL.
    """
    if len(text) > MAX_TEXT_SIZE or "\x00" in text:
        raise VXPError("Input exceeds the supported text limits.")
    lines = [line.strip() for line in text.removeprefix("\ufeff").splitlines() if line.strip()]
    if not lines or lines[0] != "[Header]" or any(len(line) > 4096 for line in lines):
        raise VXPError("Expected a bounded header section.")
    header = {}
    data_start = None
    supported_keys = {"version", "data_layout", "samples_per_second", "scale_factor"}
    for index, line in enumerate(lines[1:], 1):
        if line == "[Data]":
            data_start = index + 1
            break
        if "=" not in line:
            raise VXPError("Malformed header section.")
        key, value = line.split("=", 1)
        key = key.strip().lower()
        if key in supported_keys:
            if key in header:
                raise VXPError("Duplicate processing header field.")
            header[key] = value.strip()
        # Other fields, including identity, dates, and CRC, are not retained.
    if data_start is None or not supported_keys <= header.keys():
        raise VXPError("Required processing sections or fields are missing.")
    if header["version"] != "1.6":
        raise VXPError("Only the documented VXP 1.6 subset is supported.")
    layout = []
    for field in header["data_layout"].split(","):
        normalized = field.strip().lower().replace("_", "")
        layout.append(ALIASES.get(normalized, normalized))
    if len(layout) != len(FIELDS) or set(layout) != FIELDS:
        raise VXPError("Unsupported or duplicate data-layout fields.")
    rate = _number(header["samples_per_second"])
    scale = _number(header["scale_factor"])
    if rate <= 0 or scale <= 0 or not math.isfinite(1 / rate):
        raise VXPError("Sample rate and scale must be positive and usable.")
    rows = lines[data_start:]
    if not rows or len(rows) > MAX_ROWS:
        raise VXPError("Unsupported number of data rows.")
    samples = []
    first_ms = None
    previous_ms = None
    for row in rows:
        values = [value.strip() for value in row.split(",")]
        if len(values) != len(layout):
            raise VXPError("Data row does not match the declared layout.")
        fields = dict(zip(layout, values))
        amplitude = _number(fields["amplitude"]) * scale
        timestamp = _number(fields["timestamp"])
        validity = _number(fields["validflag"])
        _number(fields["phase"])
        if validity > 0 or not validity.is_integer():
            raise VXPError("Unsupported validity flag.")
        if fields["ttlin"] not in {"0", "1"} or fields["ttlout"] not in {"0", "1"}:
            raise VXPError("Unsupported digital field.")
        if fields["mark"] not in {"", "Z", "P"}:
            raise VXPError("Unsupported mark field.")
        if timestamp < 0 or (previous_ms is not None and timestamp <= previous_ms):
            raise VXPError("Timestamps must be nonnegative and strictly increasing.")
        if first_ms is None:
            first_ms = timestamp
        seconds = (timestamp - first_ms) / 1000
        if not math.isfinite(amplitude) or not math.isfinite(seconds):
            raise VXPError("Converted values must be finite.")
        samples.append(Sample(seconds, amplitude, validity == 0))
        previous_ms = timestamp
    return Trace(rate, tuple(samples))


def read_vxp(path: str | Path) -> Trace:
    """Read a bounded local UTF-8 file. Never include its path in diagnostics."""
    try:
        with Path(path).open("rb") as stream:
            data = stream.read(MAX_TEXT_SIZE + 1)
        if len(data) > MAX_TEXT_SIZE:
            raise VXPError("Input exceeds the supported text limits.")
        text = data.decode("utf-8-sig")
    except (OSError, UnicodeError, ValueError) as error:
        if isinstance(error, VXPError):
            raise
        raise VXPError("Could not read a supported local UTF-8 file.") from None
    return parse_vxp(text)


def _adjacent(left: Sample, right: Sample, rate: float) -> bool:
    # A teaching continuity limit, not a device-specific tolerance.
    return left.valid and right.valid and right.seconds - left.seconds <= 1.5 / rate


def smooth_valid(trace: Trace, width: int = 3) -> tuple[float | None, ...]:
    """Smooth valid contiguous segments; keep invalid positions as None."""
    moving_average([0.0], width)  # Validate the public width argument.
    result = [None] * len(trace.samples)
    start = 0
    while start < len(trace.samples):
        if not trace.samples[start].valid:
            start += 1
            continue
        stop = start + 1
        while stop < len(trace.samples) and _adjacent(
            trace.samples[stop - 1], trace.samples[stop], trace.samples_per_second
        ):
            stop += 1
        try:
            segment = moving_average(
                [sample.amplitude_mm for sample in trace.samples[start:stop]], width
            )
        except OverflowError:
            raise VXPError("Smoothing exceeds the supported numeric range.") from None
        if not all(math.isfinite(value) for value in segment):
            raise VXPError("Smoothing exceeds the supported numeric range.")
        result[start:stop] = segment
        start = stop
    return tuple(result)


def window_features(trace: Trace, window_seconds: float = 1.0) -> tuple[Features, ...]:
    """Group observed samples by relative time; report valid-only statistics.

    No missing windows are invented. A partial window is retained with counts.
    Mean adjacent differences never bridge invalid samples or timing gaps.
    """
    if not math.isfinite(window_seconds) or window_seconds <= 0:
        raise VXPError("Window duration must be positive and finite.")
    buckets = {}
    for sample in trace.samples:
        position = sample.seconds / window_seconds
        if not math.isfinite(position):
            raise VXPError("Window duration is too small for this trace.")
        buckets.setdefault(math.floor(position), []).append(sample)
    result = []
    for bucket, samples in sorted(buckets.items()):
        values = [sample.amplitude_mm for sample in samples if sample.valid]
        steps = [abs(right.amplitude_mm - left.amplitude_mm)
                 for left, right in zip(samples, samples[1:])
                 if _adjacent(left, right, trace.samples_per_second)]
        try:
            metrics = (
                fmean(values) if values else None,
                pstdev(values) if values else None,
                max(values) - min(values) if values else None,
                fmean(steps) if steps else None,
            )
        except OverflowError:
            raise VXPError("Statistics exceed the supported numeric range.") from None
        if not all(value is None or math.isfinite(value) for value in metrics):
            raise VXPError("Statistics exceed the supported numeric range.")
        result.append(Features(bucket * window_seconds, len(samples), len(values), *metrics))
    return tuple(result)


def synthetic_vxp_text() -> str:
    """Create an invented teaching fixture, not a device-ready clinical file."""
    lines = [
        "[Header]", "Version=1.6",
        "Data_layout=amplitude,phase,timestamp,validflag,ttlin,mark,ttlout",
        "Patient_ID=SYNTHETIC_ONLY", "Samples_per_second=50", "Scale_factor=2",
        "[Data]",
    ]
    for index, value in enumerate(synthetic_signal()):
        # A fixed invalid block illustrates quality handling without real data.
        flag = -1 if 105 <= index < 110 else 0
        lines.append(f"{value / 2:.8f},0,{index * 1000 / SAMPLE_RATE:.0f},{flag},0,,0")
    return "\n".join(lines) + "\n"
