/* Independently written synthetic respiratory-state model. No clinical inputs. */
(function (root) {
  'use strict';
  const DEFAULTS = Object.freeze({ period: 5, expiration: 0.65, pause: 0.15,
    amplitude: 10, baseline: 0, cycles: 3, samples: 240, bins: 10 });

  function settings(overrides = {}) {
    const p = { ...DEFAULTS, ...overrides };
    for (const [key, low, high] of [
      ['period', 1, 15], ['expiration', 0.25, 0.85], ['pause', 0, 0.5],
      ['amplitude', 1, 30], ['baseline', -20, 20], ['cycles', 1, 8],
      ['samples', 60, 1920], ['bins', 4, 20]
    ]) {
      if (typeof p[key] !== 'number' || !Number.isFinite(p[key]) || p[key] < low || p[key] > high) {
        throw new RangeError(`Invalid synthetic parameter: ${key}`);
      }
    }
    for (const key of ['cycles', 'samples', 'bins']) {
      if (!Number.isInteger(p[key])) throw new RangeError(`${key} must be an integer`);
    }
    return p;
  }

  function wrap(value) { const remainder = value % 1; return remainder < 0 ? remainder + 1 : remainder; }

  function circularDistance(a, b) {
    if (!Number.isFinite(a) || !Number.isFinite(b)) throw new RangeError('States must be finite');
    const distance = Math.abs(wrap(a) - wrap(b));
    return Math.min(distance, 1 - distance);
  }

  function pointAt(time, overrides = {}) {
    const p = settings(overrides);
    if (!Number.isFinite(time) || time < 0) throw new RangeError('Time must be finite and nonnegative');
    const uniform = wrap(time / p.period);
    const expirationEnd = p.period * p.expiration;
    const activeEnd = expirationEnd * (1 - p.pause);
    const tau = uniform * p.period;
    let position, velocity, amplitudeState, branchState, branch;
    if (tau < activeEnd) {
      const angle = Math.PI * tau / activeEnd;
      position = p.amplitude / 2 * Math.cos(angle);
      velocity = -p.amplitude / 2 * Math.PI / activeEnd * Math.sin(angle);
      amplitudeState = (1 - Math.cos(angle)) / 4;
      branch = 'expiration';
    } else if (tau < expirationEnd) {
      position = -p.amplitude / 2;
      velocity = 0;
      amplitudeState = 0.5;
      branch = 'pause';
    } else {
      const duration = p.period - expirationEnd;
      const angle = Math.PI * (tau - expirationEnd) / duration;
      position = -p.amplitude / 2 * Math.cos(angle);
      velocity = p.amplitude / 2 * Math.PI / duration * Math.sin(angle);
      amplitudeState = 0.5 + (1 - Math.cos(angle)) / 4;
      branch = 'inspiration';
    }
    branchState = tau < expirationEnd
      ? 0.5 * tau / expirationEnd
      : 0.5 + 0.5 * (tau - expirationEnd) / (p.period - expirationEnd);
    return { time, displacement: p.baseline + position, velocity, uniform,
      branchState: wrap(branchState), amplitudeState: wrap(amplitudeState), branch };
  }

  function bin(state, count) {
    const scaled = wrap(state) * count, nearest = Math.round(scaled);
    // Stabilize exact bin boundaries against floating-point roundoff only.
    const value = Math.abs(scaled - nearest) <= 32 * Number.EPSILON * count ? nearest : scaled;
    return Math.min(count - 1, Math.floor(value));
  }

  function compare(points, left, right, count) {
    const distances = points.map(point => circularDistance(point[left], point[right]));
    return {
      meanDistance: distances.reduce((sum, value) => sum + value, 0) / points.length,
      rmsDistance: Math.sqrt(distances.reduce((sum, value) => sum + value * value, 0) / points.length),
      maxDistance: Math.max(...distances),
      binMismatch: points.filter(point => bin(point[left], count) !== bin(point[right], count)).length / points.length
    };
  }

  function simulate(overrides = {}) {
    const p = settings(overrides);
    // Uniform, left-closed samples exclude the duplicated final cycle endpoint.
    const cycle = Array.from({ length: p.samples }, (_, i) => pointAt(i * p.period / p.samples, p));
    const points = Array.from({ length: p.cycles * p.samples }, (_, i) => ({
      ...cycle[i % p.samples], time: i * p.period / p.samples
    }));
    const occupancy = Object.fromEntries(['uniform', 'branchState', 'amplitudeState'].map(key => {
      const counts = Array(p.bins).fill(0);
      for (const point of points) counts[bin(point[key], p.bins)]++;
      return [key, counts.map(value => value / points.length)];
    }));
    return { settings: p, points, occupancy,
      comparison: compare(points, 'uniform', 'amplitudeState', p.bins),
      branchComparison: compare(points, 'branchState', 'amplitudeState', p.bins),
      duration: p.period * p.cycles,
      interval: p.period / p.samples,
      expirationDuration: p.period * p.expiration,
      inspirationDuration: p.period * (1 - p.expiration),
      pauseDuration: p.period * p.expiration * p.pause };
  }

  function toCSV(result) {
    const fields = ['time', 'displacement', 'velocity', 'uniform', 'branchState', 'amplitudeState'];
    const labels = ['synthetic_time_s', 'synthetic_displacement_mm', 'synthetic_velocity_mm_s',
      'uniform_phase', 'branch_balanced_phase', 'amplitude_state'];
    return '# Entirely invented signal; not a clinical recording\n' + labels.join(',') + '\n'
      + result.points.map(point => fields.map(field => point[field].toPrecision(12)).join(',')).join('\n') + '\n';
  }

  const api = Object.freeze({ DEFAULTS, settings, pointAt, circularDistance, simulate, toCSV });
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.BreathLab = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
