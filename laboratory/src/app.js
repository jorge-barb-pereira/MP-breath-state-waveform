/* Offline interface for the independently generated synthetic experiment. */
'use strict';
(() => {
  const model = globalThis.BreathLab;
  const colors = { displacement: '#087f80', uniform: '#356bd6', branchState: '#2c8b6e', amplitudeState: '#b8208c',
    selectedPhase: '#356bd6', phaseBin: '#356bd6', amplitudeBin: '#b8208c', signedDifference: '#15323c', signedBinDifference: '#15323c' };
  const binColors = ['#4c78a8', '#f58518', '#e45756', '#72b7b2', '#54a24b', '#eeca3b', '#b279a2', '#ff9da6', '#9d755d', '#79706e',
    '#173f5f', '#914900', '#912c36', '#147874', '#2d5221', '#8b761d', '#6f397a', '#b75e70', '#573b30', '#393e46'];
  const regimeColors = ['#e6f3e9', '#fff1cc', '#fbe4e1'];
  const controls = ['period', 'expiration', 'pause', 'amplitude', 'bins'];
  const presets = {
    balanced: { period: 5, expiration: 50, pause: 0, amplitude: 10, bins: 10 },
    asymmetric: { period: 5, expiration: 70, pause: 0, amplitude: 10, bins: 10 },
    pause: { period: 5, expiration: 65, pause: 30, amplitude: 10, bins: 10 }
  };
  let current;
  const element = id => document.getElementById(id);

  function context(id) {
    const canvas = element(id), width = canvas.clientWidth, height = canvas.clientHeight;
    const scale = Math.min(window.devicePixelRatio || 1, 3);
    canvas.width = Math.round(width * scale); canvas.height = Math.round(height * scale);
    const ctx = canvas.getContext('2d'); ctx.scale(scale, scale);
    ctx.font = '10px system-ui';
    return { ctx, width, height, left: 43, right: width - 12, top: 12, bottom: height - 30 };
  }

  function axes(plot, ymin, ymax, xmax, yLabel, xLabel, xTicks = null, integerY = false) {
    const {ctx, left, right, top, bottom} = plot;
    plot.x = value => left + value / xmax * (right - left);
    plot.y = value => bottom - (value - ymin) / (ymax - ymin) * (bottom - top);
    const yValues = [...new Set(Array.from({ length: 5 }, (_, i) => {
      const value = ymin + (ymax - ymin) * i / 4;
      return integerY ? Math.round(value) : value;
    }))];
    for (const value of yValues) {
      const y = plot.y(value);
      ctx.strokeStyle = '#e6edeb'; ctx.beginPath(); ctx.moveTo(left, y); ctx.lineTo(right, y); ctx.stroke();
      ctx.fillStyle = '#607780'; ctx.textAlign = 'right'; ctx.fillText(integerY ? String(value) : value.toFixed(ymax <= 1 ? 2 : 1), left - 8, y + 3);
    }
    const ticks = xTicks || Array.from({ length: 7 }, (_, i) => ({ value: xmax * i / 6, label: (xmax * i / 6).toFixed(1) }));
    for (const tick of ticks) {
      ctx.textAlign = 'center'; ctx.fillText(tick.label, plot.x(tick.value), bottom + 16);
    }
    ctx.textAlign = 'left'; ctx.fillText(yLabel, left, top - 3);
    ctx.textAlign = 'right'; ctx.fillText(xLabel, right, plot.height - 1);
  }

  function line(plot, field, circular = false, stepped = false) {
    const { ctx } = plot;
    ctx.strokeStyle = colors[field]; ctx.lineWidth = field === 'displacement' ? 2.3 : 1.8;
    ctx.beginPath();
    let previous, previousY;
    for (const point of current.points) {
      const x = plot.x(point.time), y = plot.y(point[field]);
      if (previous === undefined || (circular && Math.abs(point[field] - previous) > 0.5)) ctx.moveTo(x, y);
      else {
        if (stepped) ctx.lineTo(x, previousY);
        ctx.lineTo(x, y);
      }
      previous = point[field]; previousY = y;
    }
    ctx.stroke();
  }

  function timeRegimes(plot) {
    const { ctx, top, bottom } = plot;
    // Each background strip represents one left-closed sample interval.
    for (const point of current.points) {
      const x = plot.x(point.time), end = plot.x(point.time + current.interval);
      ctx.fillStyle = regimeColors[point.regime]; ctx.fillRect(x, top, end - x + 0.3, bottom - top);
    }
  }

  function differenceBands(plot, step, limit) {
    const { ctx, left, right } = plot;
    for (let category = 2; category >= 0; category--) {
      const bound = Math.min(limit, category === 2 ? limit : (category + 1) * step);
      ctx.fillStyle = regimeColors[category];
      ctx.fillRect(left, plot.y(bound), right - left, plot.y(-bound) - plot.y(bound));
    }
    for (const value of [-2 * step, -step, 0, step, 2 * step]) {
      if (Math.abs(value) > limit) continue;
      ctx.strokeStyle = value === 0 ? '#8c9b9f' : '#b4bfc0'; ctx.setLineDash([4, 4]);
      ctx.beginPath(); ctx.moveTo(left, plot.y(value)); ctx.lineTo(right, plot.y(value)); ctx.stroke();
    }
    ctx.setLineDash([]);
  }

  function binTracks(plot) {
    const {ctx, left, bottom} = plot;
    for (const [row, key, label] of [[0, 'phaseBin', 'P'], [1, 'amplitudeBin', 'A']]) {
      const y = bottom + 25 + row * 10;
      ctx.fillStyle = '#607780'; ctx.textAlign = 'right'; ctx.fillText(label, left - 8, y + 6);
      for (const point of current.points) {
        ctx.fillStyle = binColors[point[key] % binColors.length];
        ctx.fillRect(plot.x(point.time), y, plot.x(point.time + current.interval) - plot.x(point.time) + 0.3, 7);
      }
    }
  }

  function charts() {
    const p = current.settings;
    const wave = context('waveform');
    wave.bottom -= 25;
    axes(wave, -p.amplitude * 0.6, p.amplitude * 0.6, current.duration, 'mm', 'seconds');
    timeRegimes(wave);
    line(wave, 'displacement');
    binTracks(wave);
    const state = context('states');
    axes(state, 0, 1, current.duration, 'state', 'seconds');
    for (const field of ['uniform', 'branchState', 'amplitudeState']) line(state, field, true);
    const discrete = context('bin-functions');
    axes(discrete, 0, p.bins - 1, current.duration, 'bin index', 'seconds', null, true);
    line(discrete, 'phaseBin', false, true); line(discrete, 'amplitudeBin', false, true);
    const continuousDifference = context('continuous-difference');
    axes(continuousDifference, -0.5, 0.5, current.duration, 'phase − amplitude', 'seconds');
    differenceBands(continuousDifference, 1 / p.bins, 0.5);
    line(continuousDifference, 'signedDifference', true);
    const discreteDifference = context('bin-difference');
    axes(discreteDifference, -Math.floor(p.bins / 2), Math.floor(p.bins / 2), current.duration, 'circular bin difference', 'seconds', null, true);
    differenceBands(discreteDifference, 1, p.bins / 2);
    line(discreteDifference, 'signedBinDifference', false, true);
    const bars = context('occupancy');
    const peak = Math.max(...Object.values(current.occupancy).flat());
    axes(bars, 0, Math.min(1, Math.max(0.2, peak * 1.2)), p.bins, 'fraction', 'state bin (zero-based)',
      Array.from({ length: p.bins }, (_, i) => ({ value: i + 0.5, label: String(i) })));
    const group = (bars.right - bars.left) / p.bins, barWidth = group * 0.21;
    for (const [j, field] of ['uniform', 'branchState', 'amplitudeState'].entries()) {
      bars.ctx.fillStyle = colors[field];
      current.occupancy[field].forEach((value, i) => {
        const x = bars.left + i * group + group * 0.15 + j * barWidth;
        const y = bars.y(value);
        bars.ctx.fillRect(x, y, barWidth - 1, bars.bottom - y);
      });
    }
  }

  function update() {
    const values = Object.fromEntries(controls.map(id => [id, Number(element(id).value)]));
    current = model.simulate({ ...values, expiration: values.expiration / 100, pause: values.pause / 100,
      phaseMethod: element('phase-method').value });
    for (const id of controls) {
      const unit = id === 'period' ? ' s' : id === 'amplitude' ? ' mm' : ['expiration', 'pause'].includes(id) ? '%' : '';
      element(id + '-value').textContent = values[id] + unit;
    }
    for (const button of document.querySelectorAll('[data-preset]')) {
      button.setAttribute('aria-pressed', String(controls.every(id => values[id] === presets[button.dataset.preset][id])));
    }
    const format = value => (value * 100).toFixed(2) + '%';
    const selected = current.selectedComparison;
    element('rms').textContent = format(selected.rmsDistance);
    element('maximum').textContent = format(selected.maxDistance);
    element('mismatch').textContent = (selected.binMismatch * 100).toFixed(1) + '%';
    element('balanced-rms').textContent = format(current.branchComparison.rmsDistance);
    element('classification').textContent = selected.classification;
    element('rms-bw').textContent = selected.rmsBinWidths.toFixed(3) + ' BW';
    element('regime-fractions').textContent = selected.regimeFractions.map((fraction, i) =>
      `${['≤1 BW', '>1 to ≤2 BW', '>2 BW'][i]}: ${format(fraction)}`).join(' · ');
    element('selected-method-label').textContent = pMethodLabel(current.settings.phaseMethod);
    element('bin-legend').replaceChildren(...Array.from({length: current.settings.bins}, (_, index) => {
      const label = document.createElement('span'), swatch = document.createElement('i');
      swatch.style.backgroundColor = binColors[index % binColors.length];
      label.append(swatch, String(index)); return label;
    }));
    element('timing').replaceChildren(...[
      ['Expiration, including pause', current.expirationDuration], ['Inspiration', current.inspirationDuration], ['End-expiratory pause', current.pauseDuration]
    ].map(([name, duration]) => {
      const row = document.createElement('div'), label = document.createElement('span'), value = document.createElement('strong');
      label.textContent = name; value.textContent = duration.toFixed(2) + ' s'; row.append(label, value); return row;
    }));
    element('announcement').textContent = `Synthetic experiment updated. ${pMethodLabel(current.settings.phaseMethod)}. Circular RMS disagreement ${format(selected.rmsDistance)}. ${current.settings.bins} centred state bins. ${selected.classification}.`;
    charts();
  }
  function pMethodLabel(method) { return method === 'single' ? 'Single phase vs amplitude' : 'Dual phase vs amplitude'; }
  function apply(values) { for (const id of controls) element(id).value = values[id]; update(); }
  for (const id of controls) element(id).addEventListener('input', update);
  element('phase-method').addEventListener('change', update);
  for (const button of document.querySelectorAll('[data-preset]')) button.addEventListener('click', () => apply(presets[button.dataset.preset]));
  element('reset').addEventListener('click', () => {
    element('phase-method').value = model.DEFAULTS.phaseMethod;
    apply({ ...model.DEFAULTS, expiration: model.DEFAULTS.expiration * 100, pause: model.DEFAULTS.pause * 100 });
  });
  element('download').addEventListener('click', () => {
    const url = URL.createObjectURL(new Blob([model.toCSV(current)], { type: 'text/csv;charset=utf-8' }));
    const anchor = document.createElement('a'); anchor.href = url; anchor.download = 'synthetic-breath-state.csv';
    anchor.click(); window.setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
  new ResizeObserver(() => { if (current) charts(); }).observe(element('waveform'));
  update();
})();
