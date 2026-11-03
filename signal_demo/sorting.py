"""Independent synthetic continuous and centred-bin sorting study.

No source application, recording, manuscript or external dataset is loaded.
The numerical core uses only Python's standard library.
"""

from dataclasses import dataclass
from bisect import bisect_right
import math


@dataclass(frozen=True)
class Case:
    name: str
    label: str
    family: str
    r: float
    methods: tuple[str, ...] = ("single", "dual")
    pause: float = 0.0
    vertices: tuple[tuple[float, float], ...] = ()
    epsilon: float | None = None
    limiting_rms: float | None = None


def phase(x, r, method="single"):
    if not 0 < r < 1 or not 0 <= x <= 1 or method not in ("single", "dual"):
        raise ValueError("Use a valid normalized cycle and phase definition")
    if method == "single":
        return x
    return x / (2 * r) if x < r else 0.5 + (x - r) / (2 * (1 - r))


def interpolate(vertices, x):
    positions = [point[0] for point in vertices]
    i = max(0, min(len(vertices) - 2, bisect_right(positions, x) - 1))
    a, u = vertices[i]
    b, v = vertices[i + 1]
    return u + (v - u) * (x - a) / (b - a)


def amplitude(x, case):
    if not 0 <= x <= 1:
        raise ValueError("Normalized time is outside the cycle")
    if case.vertices:
        return interpolate(case.vertices, x)
    if case.family == "linear":
        return phase(x, case.r, "dual")
    active_end = case.r * (1 - case.pause)
    if x < active_end:
        return (1 - math.cos(math.pi * x / active_end)) / 4
    if x < case.r:
        return 0.5
    return 0.5 + (1 - math.cos(math.pi * (x - case.r) / (1 - case.r))) / 4


def signal(x, case):
    state = amplitude(x, case)
    return 1 - 2 * state if x < case.r else 2 * state - 1


def signed_circular(a, b):
    """Signed a-minus-b difference; antipodal ties retain the unwrapped sign."""
    if not all(math.isfinite(v) and 0 <= v <= 1 for v in (a, b)):
        raise ValueError("States must be finite and in the closed unit interval")
    difference = a - b
    return difference - 1 if difference > 0.5 else difference + 1 if difference < -0.5 else difference


def centred_bin(state, bins=10):
    if isinstance(bins, bool) or not isinstance(bins, int) or not 4 <= bins <= 64:
        raise ValueError("Use four to sixty-four integer bins")
    if not math.isfinite(state) or not 0 <= state <= 1:
        raise ValueError("A bin requires a finite state in the closed unit interval")
    scaled = (state % 1) * bins + 0.5
    nearest = round(scaled)
    if abs(scaled - nearest) <= 32 * math.ulp(1.0) * bins:
        scaled = float(nearest)
    return math.floor(scaled) % bins


def circular_bin_difference(a, b, bins=10):
    difference = centred_bin(a, bins) - centred_bin(b, bins)
    return difference - bins if difference > bins / 2 else difference + bins if difference < -bins / 2 else difference


def regime(distance, bins=10):
    if not math.isfinite(distance) or not 0 <= distance <= 0.5:
        raise ValueError("Use a finite unsigned circular distance")
    return 0 if distance <= 1 / bins + 1e-12 else 1 if distance <= 2 / bins + 1e-12 else 2


def classification(rms, bins=10):
    if not math.isfinite(rms) or not 0 <= rms <= 0.5:
        raise ValueError("Use a finite circular RMSD")
    ratio = rms * bins
    index = 0 if ratio <= 0.5 + 1e-12 else 1 if ratio <= 1.5 + 1e-12 else 2
    return {"index": index, "label": ("Similar Processing", "Some possible differences", "Mostly different processes")[index],
            "rms_in_bin_widths": ratio,
            "status": "User-defined descriptive category; not a clinical or bin-agreement guarantee"}


def cases(epsilon=0.01):
    if not 0 < epsilon < 0.05:
        raise ValueError("Use a finite small positive epsilon below 0.05")
    e = epsilon
    plateau = ((0., 0.), (e, .5), (1-e, .5), (1., 1.))
    monotone = ((0., 0.), (e, .5), (.5, 1-e), (1., 1.))
    nonmonotone = tuple(zip((0., e, 2*e, .5-e, .75-e, .75+e, 1-e, 1.),
                           (0., .5, .5+2*e, 1-e, 1-e, .5+e, .5+e, 1.)))
    # A normalized branch rises rapidly, reverses in its interior and ends at 1.
    r = .35
    z = (0., e, .5-e, .5+e, 1-e, 1.)
    v = (0., 1-e, 1-e, e, e, 1.)
    reverse = tuple((r*t, .5*a) for t, a in zip(z, v)) + tuple(
        (r+(1-r)*t, .5+.5*a) for t, a in zip(z[1:], v[1:]))
    return (
        Case("linear_symmetric", "Linear symmetric", "linear", .5),
        Case("linear_asymmetric", "Linear asymmetric", "linear", .1),
        Case("sine_symmetric", "Sinusoidal symmetric", "sine", .5),
        Case("sine_asymmetric", "Sinusoidal asymmetric", "sine", .1),
        Case("extreme_midpoint", "Monotone with midpoint", "piecewise", .5,
             vertices=plateau, epsilon=e, limiting_rms=math.sqrt(1/12)),
        Case("extreme_monotone_single", "Monotone without midpoint", "piecewise", e, ("single",),
             vertices=monotone, epsilon=e, limiting_rms=math.sqrt(1/6)),
        Case("extreme_nonmonotone_single", "Fixed branches nonmonotone", "piecewise", e, ("single",),
             vertices=nonmonotone, epsilon=e, limiting_rms=math.sqrt(19/96)),
        Case("extreme_monotone_dual", "Monotone without midpoint", "piecewise", .35, ("dual",),
             vertices=plateau, epsilon=e, limiting_rms=math.sqrt(1/12)),
        Case("extreme_nonmonotone_dual", "Fixed branches nonmonotone", "piecewise", .35, ("dual",),
             vertices=reverse, epsilon=e, limiting_rms=math.sqrt(7/48)),
        Case("dashboard_default", "Dashboard default", "sine", .65, pause=.15),
        Case("dashboard_pause", "Dashboard pause", "sine", .65, pause=.30),
        Case("dashboard_asymmetric", "Dashboard asymmetric", "sine", .70),
    )


def extrema(case, method):
    """Candidate times for a maximum, using explicit joins and analytic roots."""
    points = {0., case.r, 1.}
    if case.vertices:
        points.update(t for t, _ in case.vertices)
    if case.family == "sine":
        active = case.r * (1 - case.pause)
        points.add(active)
        for start, duration, slope in ((0., active, 1 if method == "single" else 1/(2*case.r)),
                                       (case.r, 1-case.r, 1 if method == "single" else 1/(2*(1-case.r)))):
            ratio = 4 * duration * slope / math.pi
            if 0 <= ratio <= 1:
                z = math.asin(ratio) / math.pi
                points.update((start+duration*z, start+duration*(1-z)))
    base = sorted(points)
    for left, right in zip(base, base[1:]):
        a = phase(left, case.r, method) - amplitude(left, case)
        b = phase(right, case.r, method) - amplitude(right, case)
        if (a-.5)*(b-.5) < 0 or (a+.5)*(b+.5) < 0:
            low, high = left, right
            target = .5 if max(a,b) > .5 else -.5
            for _ in range(48):
                middle = (low+high)/2
                value = phase(middle, case.r, method) - amplitude(middle, case)
                if (value-target)*(a-target)>0: low=middle
                else: high=middle
            points.add((low+high)/2)
    return sorted(points)


def exact_piecewise_rms(case, method):
    knots = sorted({0., case.r, 1., *(t for t, _ in case.vertices)})
    total = 0.
    for left, right in zip(knots, knots[1:]):
        a = phase(left, case.r, method) - amplitude(left, case)
        b = phase(right, case.r, method) - amplitude(right, case)
        cuts = [left, right]
        if b != a:
            cuts += [left+(threshold-a)*(right-left)/(b-a) for threshold in (-.5, .5)
                     if min(a,b) < threshold < max(a,b)]
        cuts.sort()
        for start, stop in zip(cuts, cuts[1:]):
            midpoint = (start+stop)/2
            raw = phase(midpoint, case.r, method) - amplitude(midpoint, case)
            shift = -1 if raw > .5 else 1 if raw < -.5 else 0
            u = phase(start, case.r, method) - amplitude(start, case) + shift
            v = phase(stop, case.r, method) - amplitude(stop, case) + shift
            total += (stop-start)*(u*u+u*v+v*v)/3
    return math.sqrt(max(0.,total))


def measure(case, method, samples=20000, bins=10):
    if isinstance(samples,bool) or not isinstance(samples,int) or not 100 <= samples <= 200000:
        raise ValueError("Use 100 to 200000 midpoint samples")
    centred_bin(0, bins)
    if method not in case.methods:
        raise ValueError("This constructed case does not specify that comparison")
    squared, mismatch = 0., 0
    counts, offsets = [0,0,0], {}
    phase_counts, amplitude_counts = [0]*bins, [0]*bins
    for i in range(samples):
        x = (i+.5)/samples
        p, a = phase(x,case.r,method), amplitude(x,case)
        distance = abs(signed_circular(p,a))
        squared += distance*distance
        counts[regime(distance,bins)] += 1
        pb, ab = centred_bin(p,bins), centred_bin(a,bins)
        difference = pb-ab
        if difference > bins/2: difference -= bins
        if difference < -bins/2: difference += bins
        offsets[str(difference)] = offsets.get(str(difference),0)+1
        mismatch += pb != ab
        phase_counts[pb] += 1
        amplitude_counts[ab] += 1
    sampled_rms = math.sqrt(squared/samples)
    rms = exact_piecewise_rms(case,method) if case.family != "sine" else sampled_rms
    maximum = max(abs(signed_circular(phase(x,case.r,method),amplitude(x,case))) for x in extrema(case,method))
    return {"case":case.name,"label":case.label,"family":case.family,"method":method,
            "r":case.r,"pause_fraction_of_expiration":case.pause,"epsilon":case.epsilon,
            "samples":samples,"bins":bins,"valid_fraction":1.,"maximum_circular_distance":maximum,
            "circular_rmsd":rms,"midpoint_circular_rmsd":sampled_rms,
            "rms_method":"Exact integration of piecewise-linear difference with circular splits" if case.family != "sine" else "Uniform midpoint quadrature",
            "bin_mismatch_fraction":mismatch/samples,"pointwise_regime_fractions":[v/samples for v in counts],
            "phase_bin_occupancy":[v/samples for v in phase_counts],
            "amplitude_bin_occupancy":[v/samples for v in amplitude_counts],
            "signed_circular_bin_offset_counts":offsets,"classification":classification(rms,bins),
            "constructed_family_rms_limit":case.limiting_rms}


def study_report(samples=20000):
    return {"schema_version":1,"synthetic_only":True,"bins":10,"sampling":"Uniform left-open/right-open midpoint grid on normalized cycle time",
            "bin_convention":"Centred circular bins floor(N*(state mod 1)+1/2) mod N",
            "signed_difference":"Phase minus amplitude; antipodal ties retain unwrapped sign",
            "regime_thresholds_bw":[1,2],"aggregate_rms_thresholds_bw":[.5,1.5],
            "interpretation":"Empirical numerical descriptions of synthetic signals; no clinical or image-quality validation",
            "results":[measure(case,method,samples) for case in cases() for method in case.methods]}
