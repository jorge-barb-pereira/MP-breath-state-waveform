# Validation

The implementation is exercised using invented signals, invented VXP text and
temporary test files only. Tests do not execute original applications, notebooks,
clinical integrations, models, macros, or database connections.

## Automated coverage

The suite contains 29 tests covering:

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

## Limits

Local validation uses Python 3.12.14 on Windows. Python 3.10 is the documented
minimum, but separate testing of every supported interpreter/platform has not
been performed. No CI run is claimed, and no CI, package build, release upload,
or artifact publishing workflow is configured.

These checks establish behavior on invented inputs only. They do not establish
clinical validity, real-device compatibility, CRC integrity, mathematical parity
with another implementation, or confidentiality. The file allowlist does not
inspect history or artifact contents; those require manual release review.
