# Continuous and discrete breath state sorting

This independent synthetic study makes continuous state disagreement, exact
ten-bin assignment disagreement and descriptive classifications separately
observable. Its [results](SORTING_RESULTS.md) comprise 20 comparisons on 12
constructed cycles. No recording, original application, manuscript, trained
model or external dataset is read by the generator.

## Cycle and state definitions

For a selected maximum, trough and next maximum at times `a < b < c`, set
`T = c-a`, `x = (t-a)/T` and `r = (b-a)/T`. Cycle membership is half-open:
`a <= t < c`. A closing state of one is used only as an integration left limit;
periodic bin assignment wraps it to zero. The known anchors are inputs to the
mathematical examples, not results of an automatic landmark detector.

Uniform single phase and branch-balanced dual phase are

```text
P(x) = x
Q(x) = x/(2r)                         when x < r
       1/2 + (x-r)/(2(1-r))           when x >= r
```

For explicit amplitude bounds `L < U`, with `R = U-L`, the direction-dependent
amplitude coordinate is

```text
A(t) = (U-s(t))/(2R)                  before the selected trough
       1/2 + (s(t)-L)/(2R)            from the selected trough onward
```

These formulas distinguish two occurrences of the same amplitude by their
selected cycle branch. In a monotone maximum-to-trough-to-maximum cycle the
coordinate increases from zero through one half to one. Nonmonotone constructed
branches can reverse their amplitude coordinate.

A state is undefined if its input is nonfinite, calibration has zero range,
the amplitude is outside calibration, or the selected branch/observation is
unsupported. Its codomain is the unit circle together with an undefined marker
`bottom`; undefined is not zero. The current synthetic fixtures are defined
throughout the cycle, so their valid-duration fraction is exactly one.

Continuity at the selected trough requires `s(b) = L`. With a fixed reference
that does not meet this condition, the right-minus-left amplitude-state jump is
`(s(b)-L)/R`. A derivative or whole-interval velocity bound must not cross that
jump. Such partial-validity inputs are not generated in this study.

## Continuous circular disagreement

For either selected phase `F` equal to `P` or `Q`, define raw difference
`d = F-A`. The signed circular difference retains the raw sign at antipodal ties:

```text
delta = d-1       when d >  1/2
        d+1       when d < -1/2
        d         otherwise
D = abs(delta) = min(abs(F-A), 1-abs(F-A))
```

Thus `0 <= D <= 1/2`. In particular, the second term is `1-abs(F-A)`;
`abs(1-(F-A))` is not a valid general replacement for negative raw differences.
The phase-minus-amplitude orientation fixes the sign of every difference plot.
The unsigned metric remains continuous at the signed circular branch cut.

For a valid time domain `V` of positive duration, use

```text
RMSD = sqrt(integral over V of D(t)^2 dt / duration(V))
coverage = duration(V)/T
```

RMSD is dimensionless. A zero RMSD establishes equality almost everywhere on
the scored domain; continuity on valid intervals strengthens this to pointwise
equality on those intervals.
It does not establish agreement on an excluded or undefined interval. If no
duration is valid, the score is undefined rather than zero. No clinical
displacement, image-quality or dose error follows from this coordinate score.

## Centred ten-bin sorting

For `N = 10`, bin width is `BW = 1/N = 0.1` of a state revolution. The shared
centred quantizer is

```text
B_N(f) = floor(N*(f mod 1) + 1/2) mod N
```

Bins are numbered zero through nine. Bin zero straddles the periodic join;
thresholds are `(k+1/2)/N` modulo one. An exact threshold joins the bin in the
increasing-state direction. Values within `32 * machine_epsilon * N` of an
integer after scaling and adding one half are snapped to that integer only to
stabilize floating-point threshold arithmetic.

The signed discrete difference is `B_N(F)-B_N(A)`, reduced by adding or
subtracting `N` when it lies outside `[-N/2,N/2]`. Antipodal ties again retain
the unreduced sign. Exact bin mismatch is the fraction of scored sample times
with different bin identities. Occupancy gives each method's fraction of
sample times in each bin. Uniform time sampling makes these duration-fraction
approximations; they are not event probabilities from a population.

A small continuous difference does not guarantee identical bins. For example,
states `0.049` and `0.051` differ by only `0.002` but map to bins zero and one.
Rounding moves each coordinate by at most half a bin width, giving the broad
metric bound `abs(abs(discrete_difference)/N-D) <= BW`; this is not an exact
bin-agreement criterion.

## Two distinct descriptive classifications

Waveform shading uses the instantaneous continuous distance:

| Pointwise regime | Definition | Time shading |
| --- | --- | --- |
| Within one bin width | `D <= BW` | Green |
| Between one and two bin widths | `BW < D <= 2 BW` | Amber |
| Beyond two bin widths | `D > 2 BW` | Red |

Signed continuous difference panels shade symmetric bands at `+/-BW` and
`+/-2 BW`. Discrete panels instead use integer offsets with bands at `+/-1`
and `+/-2` bins. The labels and units identify which quantity is being shown.

The separate whole-cycle RMSD label is user-defined:

| Label | RMSD divided by BW |
| --- | --- |
| Similar Processing | `<= 0.5` |
| Some possible differences | `> 0.5` and `<= 1.5` |
| Mostly different processes | `> 1.5` |

Threshold comparisons allow a `1e-12` numerical tolerance. These labels describe
the chosen synthetic scores. Neither these thresholds nor the colours represent
clinical severity, device acceptance criteria or guaranteed bin equality.
Always inspect exact mismatch and occupancy alongside RMSD.

## Synthetic families and numerical protocol

The canonical fixtures use symmetric (`r=0.5`) and asymmetric (`r=0.1`)
linear or half-cosine branches. Without a pause, amplitude state is

```text
Linear:    A = Q
Half cosine:
           A = (1-cos(pi*x/r))/4                         for x < r
               1/2 + (1-cos(pi*(x-r)/(1-r)))/4            otherwise
```

The normalized surrogate is `s_n=1-2A` before the selected trough and
`s_n=2A-1` thereafter. The additional dashboard fixtures use `r=0.65` with
pauses of 0.15 or 0.30 of expiration, and `r=0.70` without a pause. A pause
shortens the active expiratory half cosine, holds `A=1/2`, and retains the
original inspiration start time.

Six further comparisons use explicit piecewise-linear amplitude constructions
at `epsilon=0.01`. Their vertices and selected branch times are declared in
`signal_demo/sorting.py`. These constructions investigate selected constraints,
including reversals and increasingly steep transitions; they are not fitted
physiological waveforms. Single- and dual-phase extreme examples can use
different waveforms. Their limiting RMSD values describe those specified
families and are not a proof of a sharp universal bound over every possible
function class.

Each comparison scores 20,000 equally spaced midpoint times on a normalized
cycle. Piecewise-linear RMSD is integrated exactly, splitting at every segment,
phase join and circular half-cycle crossing. Smooth RMSD, regime fractions,
bin occupancy and mismatch use midpoint sampling. Maximum distance is evaluated
at explicit joins, analytic stationary points and any circular half-cycle
crossings. Percentages remain grid approximations. Tests compare selected
10,000- and 20,000-sample results; this sensitivity check does not establish
uniform convergence for arbitrary unseen waveforms or discontinuities.

## Analytic checks and interpretation

For linear branches, single-phase maximum distance is `abs(1/2-r)` and RMSD
is `abs(1/2-r)/sqrt(3)`. Dual phase equals amplitude throughout this family.
For unpaused half-cosine branches, dual-phase RMSD is independent of `r`:

```text
RMSD = sqrt(5/96 - 1/(2*pi^2)) = 0.0377192459...
maximum D = asin(2/pi)/(2*pi) - 1/4 + sqrt(1-4/pi^2)/4
          = 0.0526284156...
```

These identities validate specific mathematical cases. They do not imply
universal dual-phase superiority. A long pause can produce a higher dual-phase
RMSD than single-phase RMSD in the included examples.

On a locally absolutely continuous valid interval, a state velocity satisfies
`abs(f(t+h)-f(t)) <= integral(abs(f')) <= vmax*h`. Consequently
`h <= BW/vmax` limits state excursion on that interval when `vmax` is finite
and bounds the entire interval. This condition does not imply equal quantized
bins and is not a scanner acquisition prescription. It does not extend across
undefined regions, calibration jumps or a coordinate reset.

## Reproduction and relationship to earlier tools

```sh
python tools/generate_sorting_study.py
# Optional figure generation requires NumPy and Matplotlib:
python tools/generate_sorting_study.py --plot
python -m unittest discover -s tests -v
```

Outputs go to ignored `output/sorting-study/`. Reviewed copies are stored in
`docs/results/`, `docs/figures/` and [the readable report](SORTING_RESULTS.md).
The numerical core uses the Python standard library only. Figures are generated
from its declared synthetic fixtures, without reading external source material.

The older [research module](RESEARCH_METHODS.md) intentionally retains its
left-edge quantizer, nonperiodic closing-endpoint convention and signed linear
RMS/L2 metric. Its earlier report is a separate software example. Do not compare
its numbers directly with this centred circular study. The independent browser
laboratory uses the centred circular convention but a smaller interactive sample
grid; its displayed scores are sampled approximations, not the saved study's
analytic maxima or piecewise-exact RMSD.
