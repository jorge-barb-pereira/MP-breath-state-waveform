# Validation

The implementation is exercised using invented signals, invented VXP text and
temporary test files only. Tests do not execute original applications, notebooks,
clinical integrations, models, macros, or database connections.

## Automated coverage

The Python suite contains 40 tests covering:

- Deterministic finite signal generation and simple descriptive state labels.
- Moving-average edge normalization, constant preservation and variation reduction.
- Hand-calculated features, invalid inputs and incomplete demo windows.
- VXP layout reordering, documented aliases, line endings and text encoding.
- Relative time origin, amplitude scaling and discarded identifying headers.
- Invalid samples, timing gaps, partial windows and all-invalid windows.
- Unsupported versions, columns, flags, malformed rows and resource limits.
- Non-finite values and arithmetic overflow with fixed diagnostics.
- Local-file and CLI errors that omit filenames and malformed field values.
- Exact reproduction of the invented VXP fixture and both VXP CLI summaries.
- Maximum/trough/maximum continuous states, time phase and asymmetric dual phase.
- Normalized time-weighted RMS, duration-dependent L2 and linear-interpolant integration.
- Missing-interval coverage, undefined out-of-calibration samples and plateau velocities.
- Bin-boundary disagreement, distribution counts and VXP-to-cycle API integration.
- Centred circular-bin wraparound, exact thresholds and antipodal sign ties.
- Separate pointwise regimes, RMSD labels and exact bin mismatch.
- Analytic linear/half-cosine values and finite constructed-family limits.
- Sorting-study occupancy normalization, input limits and grid sensitivity.
- Passive SVG release fixtures and rejection of active content, external
  resources, unreviewed metadata and XML entity declarations.

Run the suite from the repository root:

```sh
python -m unittest discover -s tests -v
```

## Reproducible examples

```sh
python -m signal_demo
python -m signal_demo --vxp-demo
python -m signal_demo --vxp examples/synthetic.vxp
python tools/check_release.py
python -m signal_demo.research --output output/research
python tools/generate_sorting_study.py
# Optional figure plates, with NumPy and Matplotlib installed:
python tools/generate_sorting_study.py --plot
```

The commands' expected summaries are stored in `examples/`. The fixture contains
600 invented samples, including an invented five-sample invalid block; 595 are
valid. This checks quality handling rather than any real recording's behavior.

The independent research generator uses three invented half-cosine examples.
The saved report has RMS differences of approximately 0.0377 (balanced), 0.0901
(asymmetric timing), and 0.0889 (valley plateau). These are software checks on
invented functions, not measurements or evidence of imaging performance.
The included PNG was generated locally and visually inspected; the metadata
contains only neutral software/description fields and pixel resolution.

The [centred circular study](SORTING_RESULTS.md) is a separate report with 20
comparisons on 12 synthetic cycles. Its default grid contains 20,000 midpoint
samples per cycle. Piecewise-linear RMSD is integrated analytically and smooth
RMSD is sampled; explicit joins and stationary points supply maximum-distance
candidates. The eight sorting tests check known analytic cases and selected
10,000/20,000-sample sensitivity. Percentages approximate duration fractions;
they have no population confidence-interval interpretation. See the
[method reference](SORTING_METHODS.md) for its quantizer, thresholds and limits.

The release checker regenerates the two saved numeric reports from the public
generators. It also parses the four synthetic SVG plates, rejecting active
content, external resources and unexpected metadata. These structural checks
do not replace scientific or visual review. The figures do not contain patient
data or outputs imported from an original application.

## Limits

Local validation uses Python 3.12.14 on Windows. Python 3.10 is the documented
minimum, but separate testing of every supported interpreter/platform has not
been performed. A synthetic-only CI workflow is now configured for Python
3.11/3.12 and Node.js 22/24. Local checks do not establish a successful online CI
run. No package build, release upload or artifact-publishing step is configured.

These checks establish behavior on invented inputs only. They do not establish
clinical validity, real-device compatibility, CRC integrity, mathematical parity
with another implementation, or confidentiality. The file allowlist does not
inspect history or artifact contents; those require manual release review.

## Interactive laboratory extension

The browser laboratory has 21 Node.js tests for its analytic waveform, continuous
joins, derivatives, normalized/circular states, sampled metrics, repeatability,
resource limits, offline assets and release boundaries. Its local browser review
is described in [laboratory validation](LABORATORY_VALIDATION.md). These tests are
separate from the 40 Python tests and require no dependency installation.

Run `npm test` and `npm run check:release` from the repository root. The Node
release checker inspects text patterns and local tracked/historical paths; the
Python release checker validates PNG/SVG structure and both synthetic reports.
Neither substitutes for an exact-file, staged-content and publication-rights
review.
