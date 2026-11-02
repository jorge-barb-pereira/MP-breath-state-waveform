/* Offline interface for the independently generated synthetic experiment. */
'use strict';
(() => {
  const model = globalThis.BreathLab;
  const colors = { displacement: '#087f80', uniform: '#356bd6', branchState: '#2c8b6e', amplitudeState: '#d17b3d' };
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

  function axes(plot, ymin, ymax, xmax, yLabel, xLabel, xTicks = null) {
    const {ctx, left, right, top, bottom} = plot;
    plot.x = value => left + value / xmax * (right - left);
    plot.y = value => bottom - (value - ymin) / (ymax - ymin) * (bottom - top);
    for (let i = 0; i <= 4; i++) {
      const value = ymin + (ymax - ymin) * i / 4, y = plot.y(value);
      ctx.strokeStyle = '#e6edeb'; ctx.beginPath(); ctx.moveTo(left, y); ctx.lineTo(right, y); ctx.stroke();
      ctx.fillStyle = '#607780'; ctx.textAlign = 'right'; ctx.fillText(value.toFixed(ymax <= 1 ? 2 : 1), left - 8, y + 3);
    }
    const ticks = xTicks || Array.from({ length: 7 }, (_, i) => ({ value: xmax * i / 6, label: (xmax * i / 6).toFixed(1) }));
    for (const tick of ticks) {
      ctx.textAlign = 'center'; ctx.fillText(tick.label, plot.x(tick.value), bottom + 16);
    }
    ctx.textAlign = 'left'; ctx.fillText(yLabel, left, top - 3);
    ctx.textAlign = 'right'; ctx.fillText(xLabel, right, plot.height - 1);
  }

  function line(plot, field, circular = false) {
    const { ctx } = plot;
    ctx.strokeStyle = colors[field]; ctx.lineWidth = field === 'displacement' ? 2.3 : 1.8;
    ctx.beginPath();
    let previous;
    for (const point of current.points) {
      const x = plot.x(point.time), y = plot.y(point[field]);
      if (previous === undefined || (circular && Math.abs(point[field] - previous) > 0.5)) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
      previous = point[field];
    }
    ctx.stroke();
  }

  function charts() {
    const p = current.settings;
    const wave = context('waveform');
    axes(wave, -p.amplitude * 0.6, p.amplitude * 0.6, current.duration, 'mm', 'seconds');
    line(wave, 'displacement');
    const state = context('states');
    axes(state, 0, 1, current.duration, 'state', 'seconds');
    for (const field of ['uniform', 'branchState', 'amplitudeState']) line(state, field, true);
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
    current = model.simulate({ ...values, expiration: values.expiration / 100, pause: values.pause / 100 });
    for (const id of controls) {
      const unit = id === 'period' ? ' s' : id === 'amplitude' ? ' mm' : ['expiration', 'pause'].includes(id) ? '%' : '';
      element(id + '-value').textContent = values[id] + unit;
    }
    for (const button of document.querySelectorAll('[data-preset]')) {
      button.setAttribute('aria-pressed', String(controls.every(id => values[id] === presets[button.dataset.preset][id])));
    }
    const format = value => (value * 100).toFixed(2) + '%';
    element('rms').textContent = format(current.comparison.rmsDistance);
    element('maximum').textContent = format(current.comparison.maxDistance);
    element('mismatch').textContent = (current.comparison.binMismatch * 100).toFixed(1) + '%';
    element('balanced-rms').textContent = format(current.branchComparison.rmsDistance);
    element('timing').replaceChildren(...[
      ['Expiration, including pause', current.expirationDuration], ['Inspiration', current.inspirationDuration], ['End-expiratory pause', current.pauseDuration]
    ].map(([name, duration]) => {
      const row = document.createElement('div'), label = document.createElement('span'), value = document.createElement('strong');
      label.textContent = name; value.textContent = duration.toFixed(2) + ' s'; row.append(label, value); return row;
    }));
    element('announcement').textContent = `Synthetic experiment updated. Circular RMS disagreement ${format(current.comparison.rmsDistance)}. ${current.settings.bins} state bins.`;
    charts();
  }
  function apply(values) { for (const id of controls) element(id).value = values[id]; update(); }
  for (const id of controls) element(id).addEventListener('input', update);
  for (const button of document.querySelectorAll('[data-preset]')) button.addEventListener('click', () => apply(presets[button.dataset.preset]));
  element('reset').addEventListener('click', () => apply({ ...model.DEFAULTS, expiration: model.DEFAULTS.expiration * 100, pause: model.DEFAULTS.pause * 100 }));
  element('download').addEventListener('click', () => {
    const url = URL.createObjectURL(new Blob([model.toCSV(current)], { type: 'text/csv;charset=utf-8' }));
    const anchor = document.createElement('a'); anchor.href = url; anchor.download = 'synthetic-breath-state.csv';
    anchor.click(); window.setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
  new ResizeObserver(() => { if (current) charts(); }).observe(element('waveform'));
  update();
})();
