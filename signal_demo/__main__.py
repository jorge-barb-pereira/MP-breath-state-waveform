"""Print a synthetic-only example; accept no files or external connections."""

from .core import SAMPLE_RATE, analyze, ascii_trace, moving_average, synthetic_signal


def main() -> None:
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


if __name__ == "__main__":
    main()
