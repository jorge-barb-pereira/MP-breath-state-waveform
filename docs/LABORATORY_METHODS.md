# Mathematical methods

## Invented signal and units

Let `T` be the cycle period in seconds, `e` the expiration fraction, `p` the paused fraction of expiration, `A` the peak-to-trough excursion in invented millimetres, and `b` the baseline. The local cycle time is `tau = T * frac(t/T)`. Define:

```text
E = T e               expiration duration, including the pause
H = E (1 - p)         active expiration duration
I = T - E             inspiration duration
```

The displacement is:

```text
0 <= tau < H:    x = b + A/2 cos(pi tau/H)
H <= tau < E:    x = b - A/2
E <= tau < T:    x = b - A/2 cos(pi (tau-E)/I)
```

The analytic derivative is used for velocity. Position and velocity are continuous at both pause edges and at the periodic join; acceleration need not be continuous. The cycle starts at maximum displacement and expiration begins immediately. Inspiration starts at `tau = E`.

The signal is an illustrative external-surrogate coordinate, with no anatomical interpretation or fitted physiological parameters. Cycle extrema are known by construction. This is not a physical model of internal respiratory motion.

## Three explicit state coordinates

All states occupy `[0,1)` and wrap after a cycle.

1. **Uniform phase:** `u = tau/T`.
2. **Branch-balanced phase:** `q = tau/(2E)` during expiration, including its pause; `q = 1/2 + (tau-E)/(2I)` during inspiration. Each direction receives half the state range despite unequal durations.
3. **Amplitude state:** during expiration, `a = (x_max-x)/(2A)`; during inspiration, `a = 1/2 + (x-x_min)/(2A)`. It remains `1/2` during the end-expiratory pause.

The periodic 0/1 join is continuous on the circle. The selected conventions are educational definitions, not a claim of equivalence to any equipment or proprietary implementation. Adding or removing a pause changes the invented waveform and its state relationships, not a measured clinical outcome.

## Circular comparisons and bin occupancy

For normalized states `r` and `s`, the circular distance is `d = min(abs(r-s), 1-abs(r-s))`, bounded by one half. The dashboard displays `100 * sqrt(mean(d^2))` and `100 * max(d)`. These percentages refer to a full state revolution, not to error in displacement or a clinical risk probability.

For `N` bins, the centred circular bin index is `floor(N * (state mod 1) + 1/2) mod N`, with state 1 wrapped to state 0. Bin zero straddles the wrap and exact half-bin thresholds join the next bin in the increasing-state direction. Values within `32 * Number.EPSILON * N` of an integer after scaling and adding one half are snapped to that integer to stabilize floating-point roundoff. Bin mismatch is the fraction of identical sample times assigned different indices. It is computed directly, rather than inferred from a circular-distance threshold. Zero-based bins share the same origin and width for every method.

Occupancy is the fraction of uniformly spaced samples in each bin. Because sampling is uniform in time, it approximates duration fraction; it is not an exact analytic duration integral. A finite grid can put samples close to bin boundaries and cause small discretization effects.

## Continuous and discrete classification views

The phase selector chooses single or dual phase for the waveform bin track,
summary scores, descriptive RMSD label and difference plots. The continuous
state and occupancy plots retain both phase definitions for comparison.

The waveform has two coloured bin-identity tracks: selected phase and amplitude.
Its time shading uses instantaneous circular distance: green for `D <= BW`,
amber for `BW < D <= 2 BW` and red for `D > 2 BW`, where `BW=1/N`. The
discrete breath-bin panel draws the actual centred-bin indices as step functions.
The signed continuous difference is phase minus amplitude reduced to
`[-1/2,1/2]`, retaining the raw sign at half-cycle ties. Its symmetric shaded
bands are at `+/-BW` and `+/-2 BW`. The signed discrete difference instead
wraps bin-index subtraction to `[-N/2,N/2]` and shades at one and two integer
bins. Signed branch cuts are broken rather than connected as ordinary slopes.

The whole-cycle RMSD label is separate: “Similar Processing” for `RMSD/BW <=
0.5`, “Some possible differences” above 0.5 through 1.5, and “Mostly different
processes” above 1.5. Threshold comparisons allow `1e-12` numerical tolerance.
These user-defined categories are descriptive. They do not guarantee equal
bins or encode clinical severity. The panel also reports each pointwise
regime's sampled duration fraction. Exact bin mismatch remains a separate score.

Synthetic CSV exports contain time, displacement, velocity, both phase states,
amplitude state, selected phase, selected-phase bin, amplitude bin, signed
circular state and bin differences, and the instantaneous regime index 0/1/2.

## Sampling

The interface uses three identical cycles at 240 samples per cycle on a uniform left-closed, right-open grid. One cycle is computed and repeated exactly to avoid roundoff differences between identical cycles. The final repeated endpoint is excluded, so no cycle boundary is counted twice. Quantitative summaries use all points; the state plots break their lines at the circular wrap.

The model API permits 60-1,920 samples per cycle and one to eight cycles. The RMS sensitivity test compares the default grid to an eightfold denser grid for the fixed default example. This does not prove convergence for every configuration. The displayed maximum is a sampled maximum, not a rigorous continuous supremum or an acquisition-safety bound. The plots and sample grid must not be used to recommend clinical acquisition settings.

The [saved synthetic sorting study](SORTING_RESULTS.md) uses 20,000 midpoint
samples per cycle, exact piecewise-linear RMSD where applicable and explicit
continuous-maximum candidates. It also includes linear and constructed limiting
families that the interactive half-cosine dashboard does not implement. Its
bin convention and classifications match this interface, while its grid,
fixture coverage and integration methods differ. The [full formalism](SORTING_METHODS.md)
documents those choices; the dashboard does not load or claim to reproduce a
private application.

## Scope limitations

There are no real recordings, image reconstruction, dose or margin calculations, scanner-specific acquisition models, model training or clinical validation. Extrema are known, every cycle is identical, and no stochastic noise or inter-cycle drift is present. This intentionally narrow example demonstrates numerical definitions and software verification. Generalizing it requires a separately authorized research protocol, independent observations and an appropriate validation study.
