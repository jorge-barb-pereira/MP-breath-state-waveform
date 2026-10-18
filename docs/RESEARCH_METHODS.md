# Continuous functions: definitions and interpretation

This independently written module compares general time- and amplitude-based
progress coordinates. The cycle starts at an observed maximum, passes through
an explicitly selected minimum, and ends at the next observed maximum. It accepts
the parsed `Trace` produced by the VXP reader; it does not automatically detect
or clinically validate the cycle anchors.

## Public background

Time/phase sorting and percentage-amplitude sorting are established concepts:
[Wink, Panknin and Solberg (2006)](https://doi.org/10.1120/jacmp.v7i1.2198) and
[Abdelnour et al. (2007)](https://doi.org/10.1088/0031-9155/52/12/012).
Those papers provide background for the distinction between timing and
displacement. They do not validate this implementation or its invented results.
No article text, clinical data, figures, or third-party code is redistributed.

The following equations specify this demonstration's own conventions. They do
not claim equivalence to a private simulator, manuscript, or clinical algorithm.

## Continuous progress coordinates

For cycle start `a`, trough `b`, and stop `c`, with `a < b < c`:

```text
Time phase:       P(t) = (t - a) / (c - a)

Dual phase:       D(t) = 0.5 * (t - a) / (b - a)             for t <= b
                        0.5 + 0.5 * (t - b) / (c - b)       for t > b

Amplitude:        A(t) = 0.5 * (U - s(t)) / (U - L)          for t <= b
                        0.5 + 0.5 * (s(t) - L) / (U - L)    for t > b
```

`L` and `U` are explicit amplitude calibration bounds. If omitted, the selected
trough and first maximum supply them. Values outside those bounds remain
undefined; they are not silently clipped. Anchors must be observed and valid,
with the selected trough/maximum values bounding their respective branches.
Plateaus can have multiple minimum times; the caller chooses and documents `b`.
Continuity at the trough requires `s(b) = L`. An independently supplied
calibration that does not meet this condition introduces a branch jump; sampled
velocities near that jump must not be interpreted as a smooth state velocity.
The included invented examples meet the continuity condition.

The interval used for bin membership is half-open `[a, c)`. The closing sample is
retained only as a left-limit endpoint for integration and one-sided numerical
analysis. An amplitude progress value of one on an in-cycle peak plateau maps to
the final bin. This explicit convention avoids treating a cycle reset as a large
physical velocity or giving the shared closing sample two cycle memberships.

## Differences, derivatives and bins

The signed difference is `P - A`. Absolute difference is its magnitude; the two
terms are not interchangeable. Whole-cycle metrics are:

```text
RMS = sqrt(integral((P - A)^2 dt) / (c - a))
L2  = sqrt(integral((P - A)^2 dt))
```

Integration is exact for the piecewise-linear interpolant of the sampled signed
difference. It is not the exact integral of an unknown underlying waveform.
RMS is dimensionless; L2 scales with the square root of cycle duration. Invalid,
undefined, or excessively separated observations leave the whole-cycle RMS/L2
undefined. The report separately records covered duration and coverage fraction.

Time-phase velocity is `1 / (c - a)`. Amplitude-state velocity uses centered
sample differences within valid contiguous runs, with one-sided run endpoints.
It is a numerical estimate with sampling error, not an analytic or calibrated
physiological velocity. No derivative crosses a missing value, timing gap, or
cycle reset. The gap limit is an illustrative 1.5 nominal sample intervals.

For `N` bins, a defined progress value maps to `min(N-1, floor(N*f))`. Bin indices
are compared directly. A continuous difference smaller than half a bin does
**not** prove equal bin membership: two nearby values can straddle a boundary.
The report includes phase/amplitude histograms and signed bin-offset counts;
these are sample counts, not duration occupancy on irregular time grids.

## Invented examples and exclusions

The examples are independently defined half-cosine branches, optionally joined
by a flat valley. They use invented durations and asymmetry settings. They do
not preserve a professional recording, distribution, operating characteristic,
or private hybrid waveform construction. No original project is executed.

```sh
python -m signal_demo.research --output output/research
# Optional, with Matplotlib installed:
python -m signal_demo.research --output output/research --plot
```

The numeric path uses only the standard library. It generates invented inputs
internally and accepts no recording filename. The optional figure illustrates
continuous state functions and their numerical velocities. It is not an image
reconstruction or a reproduction of an unpublished research figure.

Private waveform engines, clinical quality tiers, scanner sampling prescriptions,
rotational-window rules, proprietary workflows and original data are excluded.
Adding those requires separate rights assessment, precise definitions, tests,
and approval of a newly reviewed release. No clinical superiority, patient
benefit, device compatibility or exhaustive research reproduction is claimed.
