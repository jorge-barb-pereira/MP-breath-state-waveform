"""Independent continuous cycle functions and numerical comparisons.

General time/amplitude normalization only; no original simulator or clinical
processing logic is imported. Definitions and public references are in docs.
"""

import argparse
from dataclasses import dataclass
import json
import math
from pathlib import Path
import sys

from .vxp import Sample, Trace


@dataclass(frozen=True)
class Cycle:
    start: float
    trough: float
    stop: float


def _derivative(times, values, max_gap):
    """Sampled derivatives within valid runs; no gap or cyclic-reset crossing."""
    result = [None] * len(times)
    for index, value in enumerate(values):
        if value is None:
            continue
        left = index - 1 if index and values[index - 1] is not None and times[index] - times[index - 1] <= max_gap else index
        right = index + 1 if index + 1 < len(times) and values[index + 1] is not None and times[index + 1] - times[index] <= max_gap else index
        if left != right:
            result[index] = (values[right] - values[left]) / (times[right] - times[left])
    return result


def difference_metrics(times, differences, max_gap):
    """Time-weighted metrics of the piecewise-linear signed difference.

    Whole-interval RMS/L2/mean remain undefined if coverage is incomplete.
    A signed difference is not described as an absolute difference.
    """
    if len(times) != len(differences) or len(times) < 2:
        raise ValueError('At least two aligned times and differences are required.')
    if not math.isfinite(max_gap) or max_gap <= 0:
        raise ValueError('A finite positive gap limit is required.')
    if any(not math.isfinite(t) for t in times) or any(b <= a for a, b in zip(times, times[1:])):
        raise ValueError('Times must be finite and strictly increasing.')
    if any(value is not None and not math.isfinite(value) for value in differences):
        raise ValueError('Differences must be finite or undefined.')
    area = square_area = coverage = 0.0
    complete = True
    for index, (left, right) in enumerate(zip(differences, differences[1:])):
        duration = times[index + 1] - times[index]
        if left is None or right is None or duration > max_gap:
            complete = False
            continue
        coverage += duration
        area += duration * (left + right) / 2
        square_area += duration * (left * left + left * right + right * right) / 3
    duration = times[-1] - times[0]
    return {'duration_seconds': duration, 'covered_seconds': coverage,
            'coverage_fraction': min(1.0, coverage / duration),
            'mean_signed_difference': area / duration if complete else None,
            'rms_difference': math.sqrt(square_area / duration) if complete else None,
            'l2_difference': math.sqrt(square_area) if complete else None}


def evaluate_cycle(trace: Trace, cycle: Cycle, bins: int = 10, calibration=None):
    """Evaluate a maximum/trough/next-maximum interval on observed samples.

    The closing sample is a left-limit analysis endpoint, not a new bin member.
    Calibration is explicit (lower, upper), or trough/first-maximum amplitudes.
    """
    if isinstance(bins, bool) or not isinstance(bins, int) or not 2 <= bins <= 64:
        raise ValueError('Bin count must be an integer between two and 64.')
    if not all(math.isfinite(value) for value in (cycle.start, cycle.trough, cycle.stop)) or not cycle.start < cycle.trough < cycle.stop:
        raise ValueError('Finite increasing cycle anchors are required.')
    rate = trace.samples_per_second
    if not math.isfinite(rate) or rate <= 0 or not math.isfinite(1.5 / rate):
        raise ValueError('A finite positive sample rate is required.')
    previous = -math.inf
    for sample in trace.samples:
        if not all(math.isfinite(value) for value in (sample.seconds, sample.amplitude_mm)) or sample.seconds <= previous:
            raise ValueError('Trace values must be finite with strictly increasing times.')
        previous = sample.seconds
    samples = [sample for sample in trace.samples if cycle.start <= sample.seconds <= cycle.stop]
    lookup = {sample.seconds: sample for sample in samples}
    if any(anchor not in lookup or not lookup[anchor].valid for anchor in (cycle.start, cycle.trough, cycle.stop)):
        raise ValueError('All cycle anchors must be observed and valid.')
    before = [sample.amplitude_mm for sample in samples if sample.valid and sample.seconds <= cycle.trough]
    after = [sample.amplitude_mm for sample in samples if sample.valid and sample.seconds >= cycle.trough]
    if (lookup[cycle.trough].amplitude_mm != min(before + after)
            or lookup[cycle.start].amplitude_mm < max(before)
            or lookup[cycle.stop].amplitude_mm < max(after)):
        raise ValueError('Cycle anchors must bound a maximum/trough/maximum interval.')
    lower, upper = calibration if calibration is not None else (lookup[cycle.trough].amplitude_mm, lookup[cycle.start].amplitude_mm)
    span = upper - lower
    if not all(math.isfinite(value) for value in (lower, upper, span)) or span <= 0:
        raise ValueError('Finite increasing amplitude calibration is required.')
    duration = cycle.stop - cycle.start
    if not math.isfinite(duration):
        raise ValueError('Cycle duration exceeds the supported numeric range.')
    times = [sample.seconds for sample in samples]
    phase = [(time - cycle.start) / duration if sample.valid else None for time, sample in zip(times, samples)]
    dual = [((.5 * (time - cycle.start) / (cycle.trough - cycle.start)) if time <= cycle.trough
             else .5 + .5 * (time - cycle.trough) / (cycle.stop - cycle.trough)) if sample.valid else None
            for time, sample in zip(times, samples)]
    amplitude = []
    for sample in samples:
        value = (.5 * (upper - sample.amplitude_mm) / span if sample.seconds <= cycle.trough
                 else .5 + .5 * (sample.amplitude_mm - lower) / span)
        amplitude.append(value if sample.valid and lower <= sample.amplitude_mm <= upper else None)
    difference = [p - a if p is not None and a is not None else None for p, a in zip(phase, amplitude)]
    phase_velocity = [1 / duration if sample.valid else None for sample in samples]
    amplitude_velocity = _derivative(times, amplitude, 1.5 / rate)
    rows = []
    comparisons = disagreements = 0
    phase_counts, amplitude_counts = [0] * bins, [0] * bins
    bin_offsets = {}
    for index, sample in enumerate(samples):
        # Include the left limit in integrals, exclude it from cycle bin counts.
        def bin_index(value):
            return None if value is None or sample.seconds == cycle.stop else min(bins - 1, int(value * bins))
        p_bin, a_bin = bin_index(phase[index]), bin_index(amplitude[index])
        if p_bin is not None:
            phase_counts[p_bin] += 1
        if a_bin is not None:
            amplitude_counts[a_bin] += 1
        if p_bin is not None and a_bin is not None:
            comparisons += 1
            disagreements += p_bin != a_bin
            offset = str(p_bin - a_bin)
            bin_offsets[offset] = bin_offsets.get(offset, 0) + 1
        rows.append({'seconds': sample.seconds, 'signal': sample.amplitude_mm, 'valid': sample.valid,
                     'phase': phase[index], 'dual_phase': dual[index], 'amplitude_state': amplitude[index],
                     'signed_difference': difference[index], 'phase_velocity_per_second': phase_velocity[index],
                     'amplitude_velocity_per_second': amplitude_velocity[index], 'phase_bin': p_bin, 'amplitude_bin': a_bin})
    metrics = difference_metrics(times, difference, 1.5 / rate)
    metrics.update({'bins': bins, 'compared_samples': comparisons, 'disagreeing_samples': disagreements,
                    'bin_disagreement_fraction': disagreements / comparisons if comparisons else None,
                    'phase_bin_counts': phase_counts, 'amplitude_bin_counts': amplitude_counts,
                    'bin_offset_counts': bin_offsets,
                    'amplitude_calibration': [lower, upper]})
    return {'metrics': metrics, 'rows': rows}


def invented_cases():
    """Independent half-cosine examples, not the original hybrid waveform engine."""
    result = {}
    duration, intervals = 6.0, 400
    for name, fraction, plateau in [('balanced', .5, 0.0), ('asymmetric', .35, 0.0), ('valley_plateau', .45, .3)]:
        samples = []
        for index in range(intervals + 1):
            time = duration * index / intervals
            x = index / intervals
            if x <= fraction:
                active = fraction * (1 - plateau)
                value = math.cos(math.pi * x / active) if x < active else -1.0
            else:
                value = -math.cos(math.pi * (x - fraction) / (1 - fraction))
            samples.append(Sample(time, value, True))
        trace = Trace(intervals / duration, tuple(samples))
        # Select the observed trough by index, avoiding float anchor ambiguity.
        cycle = Cycle(samples[0].seconds, samples[round(fraction * intervals)].seconds, samples[-1].seconds)
        result[name] = evaluate_cycle(trace, cycle, calibration=(-1.0, 1.0))
    return result


def render_figure(cases, target: Path):
    """Optional Matplotlib preview of continuous functions, not integer labels."""
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except ImportError:
        raise RuntimeError('Matplotlib is required for the optional figure.') from None
    figure, axes = plt.subplots(4, 3, figsize=(12, 10), sharex='col')
    figure.patch.set_facecolor('#f7f9fb')
    titles = ['Balanced cycle', 'Asymmetric timing', 'Exhalation plateau']
    for column, ((name, case), title) in enumerate(zip(cases.items(), titles)):
        rows = case['rows']
        times = [row['seconds'] for row in rows]
        axes[0, column].plot(times, [row['signal'] for row in rows], color='#263f55', lw=1.6)
        axes[0, column].set_title(title, fontsize=12, weight='bold')
        for key, label, color, style in [('phase', 'Time phase', '#346da0', '--'),
                                         ('dual_phase', 'Dual phase', '#b87932', ':'),
                                         ('amplitude_state', 'Amplitude state', '#008991', '-')]:
            axes[1, column].plot(times, [row[key] for row in rows], label=label, color=color, ls=style)
        axes[2, column].plot(times, [row['signed_difference'] for row in rows], color='#835fa2', lw=1.5)
        axes[2, column].axhline(0, color='#778896', lw=.7)
        rms = case['metrics']['rms_difference']
        axes[2, column].text(.03, .06, f'Time-weighted RMS = {rms:.4f}', transform=axes[2, column].transAxes, fontsize=9)
        axes[3, column].plot(times, [row['phase_velocity_per_second'] for row in rows], color='#346da0', ls='--', label='Phase velocity')
        axes[3, column].plot(times, [row['amplitude_velocity_per_second'] for row in rows], color='#008991', label='Amplitude velocity')
        axes[3, column].set_xlabel('Relative time (s)')
        for row in range(4):
            axes[row, column].grid(alpha=.17)
            axes[row, column].spines[['top', 'right']].set_visible(False)
            axes[row, column].set_xlim(0, 6)
    for row, label in enumerate(['Invented signal (a.u.)', 'Continuous state f(t)', 'Phase minus amplitude', 'State velocity (1/s)']):
        axes[row, 0].set_ylabel(label)
    axes[1, 0].legend(frameon=False, fontsize=8, loc='upper left')
    axes[3, 0].legend(frameon=False, fontsize=8, loc='lower left')
    figure.suptitle('Continuous breath-state functions and kinematics', x=.07, y=.98, ha='left', fontsize=20, weight='bold')
    figure.text(.07, .94, 'Maximum → trough → next maximum | Independent half-cosine examples | Entirely invented data', fontsize=10)
    figure.text(.07, .02, 'Illustrative public-method demonstration. No original recordings, private simulator, scanner validation, or clinical claims.', fontsize=9)
    figure.subplots_adjust(left=.085, right=.98, top=.9, bottom=.075, hspace=.32, wspace=.28)
    figure.savefig(target, dpi=150, metadata={'Software': 'Synthetic Signal States', 'Description': 'Independent invented continuous-function comparison.'})
    plt.close(figure)


def main(argv=None):
    parser = argparse.ArgumentParser(description='Compare continuous state functions on invented cycles only.')
    parser.add_argument('--output', type=Path, default=Path('output/research'))
    parser.add_argument('--plot', action='store_true')
    args = parser.parse_args(argv)
    cases = invented_cases()
    report = {'schema_version': 1, 'synthetic_only': True, 'difference_convention': 'phase minus amplitude',
              'cases': {name: case['metrics'] for name, case in cases.items()}}
    try:
        args.output.mkdir(parents=True, exist_ok=True)
        (args.output / 'metrics.json').write_text(json.dumps(report, indent=2, allow_nan=False) + '\n', encoding='utf-8', newline='\n')
        if args.plot:
            render_figure(cases, args.output / 'breath-state-functions.png')
    except (OSError, RuntimeError):
        print('Could not write the invented report; check the output directory and optional plotting dependency.', file=sys.stderr)
        return 2
    for name, case in cases.items():
        print(f"{name}: RMS difference {case['metrics']['rms_difference']:.4f}; bin disagreement {case['metrics']['bin_disagreement_fraction']:.1%}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
