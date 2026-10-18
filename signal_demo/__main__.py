"""Run invented examples or explicitly selected local VXP processing."""

import sys

from .core import SAMPLE_RATE, analyze, ascii_trace, moving_average, synthetic_signal
from .vxp import VXPError, parse_vxp, read_vxp, smooth_valid, synthetic_vxp_text, window_features


def print_vxp_summary(trace) -> None:
    smoothed = smooth_valid(trace)
    windows = window_features(trace)
    print("VXP numeric processing | descriptive statistics only | nonclinical")
    print(f"Samples: {len(trace.samples)}; valid: {sum(sample.valid for sample in trace.samples)}")
    print(f"Smoothed valid samples: {sum(value is not None for value in smoothed)}")
    print("Header identifiers, acquisition dates, phase and digital fields are omitted.")
    print("Numeric traces and summaries can still be sensitive; this is not anonymization.")
    print("\nStart (s)  Rows  Valid  Mean (mm)  Spread (mm)  Range (mm)  Mean step (mm)")
    for window in windows:
        metrics = [window.mean_mm, window.spread_mm, window.range_mm, window.mean_step_mm]
        formatted = [f"{value:.4f}" if value is not None else "n/a" for value in metrics]
        print(f"{window.start_seconds:9.1f}  {window.sample_count:4}  {window.valid_count:5}  "
              + "  ".join(formatted))


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if args in (["--help"], ["-h"]):
        print("Usage: python -m signal_demo [--vxp-demo | --vxp LOCAL_FILE]")
        return 0
    if args:
        try:
            if args == ["--vxp-demo"]:
                trace = parse_vxp(synthetic_vxp_text())
            elif len(args) == 2 and args[0] == "--vxp":
                trace = read_vxp(args[1])
            else:
                print("Usage: python -m signal_demo [--vxp-demo | --vxp LOCAL_FILE]", file=sys.stderr)
                return 2
            print_vxp_summary(trace)
            return 0
        except VXPError as error:
            print(f"VXP processing failed: {error}", file=sys.stderr)
            return 2
    samples = synthetic_signal()
    print("Synthetic Signal States | invented data | nonclinical")
    print(f"{len(samples)} samples at {SAMPLE_RATE} Hz; duration 12 seconds")
    print("Smoothed waveform (fixed display scale -1 to +1):")
    print(ascii_trace(moving_average(samples)))
    print("\nStart (s)  Spread  Mean step  State")
    for window in analyze(samples):
        print(f"{window.start_seconds:9.0f}  {window.spread:6.3f}  "
              f"{window.mean_step:9.3f}  {window.state}")
    print("\nIllustrative labels only; no physiological or diagnostic interpretation.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
