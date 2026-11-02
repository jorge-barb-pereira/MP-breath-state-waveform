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

For `N` bins, the bin index is `floor(N * state)`, with state 1 wrapped to state 0. Values within `32 * Number.EPSILON * N` of an integer scaled index are snapped to that integer to stabilize exact boundaries against floating-point roundoff. Bin mismatch is the fraction of identical sample times assigned different indices. It is computed directly, rather than inferred from a circular-distance threshold. Zero-based bins share the same origin and width for every method.

Occupancy is the fraction of uniformly spaced samples in each bin. Because sampling is uniform in time, it approximates duration fraction; it is not an exact analytic duration integral. A finite grid can put samples close to bin boundaries and cause small discretization effects.

## Sampling

The interface uses three identical cycles at 240 samples per cycle. One cycle is computed and repeated exactly to avoid roundoff differences between identical cycles. The final repeated endpoint is excluded, so no cycle boundary is counted twice. Quantitative summaries use all points; the state plots break their lines at the circular wrap.

The model API permits 60-1,920 samples per cycle and one to eight cycles. The RMS sensitivity test compares the default grid to an eightfold denser grid for the fixed default example. This does not prove convergence for every configuration. The displayed maximum is a sampled maximum, not a rigorous continuous supremum or an acquisition-safety bound. The plots and sample grid must not be used to recommend clinical acquisition settings.

## Scope limitations

There are no real recordings, image reconstruction, dose or margin calculations, scanner-specific acquisition models, model training or clinical validation. Extrema are known, every cycle is identical, and no stochastic noise or inter-cycle drift is present. This intentionally narrow example demonstrates numerical definitions and software verification. Generalizing it requires a separately authorized research protocol, independent observations and an appropriate validation study.
