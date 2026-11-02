'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const lab = require('../../laboratory/src/model.js');
const near = (actual, expected, tolerance = 1e-10) => assert.ok(Math.abs(actual - expected) < tolerance, `${actual} != ${expected}`);

test('known quarter-cycle positions, velocities and states for a balanced waveform', () => {
  const p = { period: 4, expiration: 0.5, pause: 0, amplitude: 8 };
  const expected = [[0, 4, 0, 0], [1, 0, -2 * Math.PI, 0.25], [2, -4, 0, 0.5], [3, 0, 2 * Math.PI, 0.75], [4, 4, 0, 0]];
  for (const [time, displacement, velocity, state] of expected) {
    const value = lab.pointAt(time, p);
    near(value.displacement, displacement); near(value.velocity, velocity);
    near(value.uniform, state); near(value.branchState, state); near(value.amplitudeState, state);
  }
});

test('position and velocity are continuous at both pause edges and cycle wrap', () => {
  const p = lab.settings(), epsilon = 1e-8;
  const end = p.period * p.expiration;
  for (const time of [end * (1 - p.pause), end, p.period]) {
    const a = lab.pointAt(time - epsilon, p), b = lab.pointAt(time + epsilon, p);
    near(a.displacement, b.displacement, 1e-5);
    near(a.velocity, b.velocity, 1e-5);
    assert.ok(lab.circularDistance(a.amplitudeState, b.amplitudeState) < 1e-5);
  }
});

test('analytic velocity agrees with finite differences away from branch changes', () => {
  for (const time of [0.43, 1.73, 3.02, 3.79, 4.61]) {
    const h = 1e-5;
    const derivative = (lab.pointAt(time + h).displacement - lab.pointAt(time - h).displacement) / (2 * h);
    near(lab.pointAt(time).velocity, derivative, 1e-7);
  }
});

test('pause is flat and does not change total period or expiration duration', () => {
  const p = { period: 5, expiration: 0.6, pause: 0.4 };
  const point = lab.pointAt(2.5, p), result = lab.simulate(p);
  assert.equal(point.branch, 'pause'); near(point.velocity, 0); near(point.amplitudeState, 0.5);
  near(result.pauseDuration, 1.2); near(result.expirationDuration, 3);
  near(result.inspirationDuration, 2); near(result.duration, 15);
});

test('state distance uses circular topology and is symmetric and bounded', () => {
  near(lab.circularDistance(0.99, 0.01), 0.02);
  near(lab.circularDistance(0, 1), 0); near(lab.circularDistance(0, 0.5), 0.5);
  for (let i = 0; i <= 100; i++) {
    const a = i / 100, b = 0.37;
    near(lab.circularDistance(a, b), lab.circularDistance(b, a));
    assert.ok(lab.circularDistance(a, b) <= 0.5);
  }
});

test('sample grid excludes the duplicated end point and occupies exactly one bin per sample', () => {
  const result = lab.simulate();
  assert.equal(result.points.length, 720); near(result.points[0].time, 0);
  near(result.points.at(-1).time, result.duration - result.interval);
  for (const values of Object.values(result.occupancy)) {
    near(values.reduce((a, b) => a + b), 1);
    assert.ok(values.every(x => x >= 0 && x <= 1));
  }
});

test('excursion, baseline and period change physical units but preserve normalized states', () => {
  const a = lab.simulate(), b = lab.simulate({ amplitude: 20, baseline: 7, period: 10 });
  for (let i = 0; i < a.points.length; i++) {
    near(b.points[i].displacement, 7 + 2 * a.points[i].displacement);
    near(b.points[i].velocity, a.points[i].velocity);
    near(b.points[i].time, 2 * a.points[i].time);
    near(b.points[i].amplitudeState, a.points[i].amplitudeState);
  }
  near(a.comparison.rmsDistance, b.comparison.rmsDistance);
});

test('branch-balanced phase puts the inspiration transition at one half', () => {
  const point = lab.pointAt(3.5, { period: 5, expiration: 0.7, pause: 0 });
  near(point.uniform, 0.7); near(point.branchState, 0.5); near(point.amplitudeState, 0.5);
});

test('reported RMS and bin mismatch equal independent calculations', () => {
  const result = lab.simulate({ samples: 137, cycles: 2 });
  let sum = 0, mismatch = 0;
  for (const point of result.points) {
    const distance = Math.abs(point.uniform - point.amplitudeState);
    sum += Math.min(distance, 1 - distance) ** 2;
    if (Math.floor(point.uniform * 10) !== Math.floor(point.amplitudeState * 10)) mismatch++;
  }
  near(result.comparison.rmsDistance, Math.sqrt(sum / result.points.length));
  near(result.comparison.binMismatch, mismatch / result.points.length);
});

test('deterministic output and CSV contain only declared synthetic numeric fields', () => {
  const result = lab.simulate(); assert.deepEqual(result, lab.simulate());
  const lines = lab.toCSV(result).trim().split('\n');
  assert.match(lines[0], /Entirely invented/); assert.equal(lines.length, result.points.length + 2);
  for (const line of lines.slice(2)) {
    const values = line.split(',').map(Number);
    assert.equal(values.length, 6); assert.ok(values.every(Number.isFinite));
  }
});

test('numerical RMS is stable under an eightfold sample-density increase', () => {
  const coarse = lab.simulate(), fine = lab.simulate({ samples: 1920 });
  near(coarse.comparison.rmsDistance, fine.comparison.rmsDistance, 0.002);
});

test('repeated identical cycles have identical states and uniform-phase bin occupancy', () => {
  const result = lab.simulate();
  for (const value of result.occupancy.uniform) near(value, 0.1);
  for (let i = 0; i < result.settings.samples; i++) {
    const a = result.points[i], b = result.points[i + result.settings.samples];
    near(a.uniform, b.uniform); near(a.branchState, b.branchState);
    near(a.amplitudeState, b.amplitudeState); near(a.displacement, b.displacement);
  }
  near(lab.simulate({ cycles: 1 }).comparison.binMismatch, result.comparison.binMismatch);
});

test('invalid values and resource bounds are rejected', () => {
  for (const p of [{ period: NaN }, { amplitude: Infinity }, { period: true }, { expiration: 1 },
    { pause: -1 }, { bins: 9.5 }, { cycles: 1000 }, { samples: 1e7 }, { baseline: '0' }]) {
    assert.throws(() => lab.simulate(p), RangeError);
  }
  assert.throws(() => lab.pointAt(-1), RangeError);
  assert.throws(() => lab.pointAt(Infinity), RangeError);
  assert.throws(() => lab.circularDistance(NaN, 0), RangeError);
});
