# Publication scope

This repository contains an independently written, limited demonstration of
general signal-processing methods and a publicly described VXP text subset.
It is not a full reproduction of a professional processing application or a
research dashboard. Only the files in `PUBLICATION_ALLOWLIST.txt` are proposed
for publication.

## Included capabilities

| Component | Included behavior |
| --- | --- |
| Synthetic example | Invented waveform, centered moving average and illustrative labels |
| VXP input | Seven-field Version 1.6 subset, declared layout, bounded UTF-8 text |
| Timing and amplitude | Relative seconds, declared scaling and finite-value checks |
| Quality | Invalid samples, timing gaps, explicit counts and missing statistics |
| Processing | Segment smoothing, mean, population spread, range and adjacent differences |
| Verification | Invented fixture, reviewed text output and automated tests |
| Research functions | Continuous single/dual phase, branch-dependent amplitude progress and state velocity |
| Comparisons | Time-weighted RMS, L2, signed differences, bin counts and disagreements |
| Browser laboratory | Invented periodic half-cosine motion, pause/asymmetry controls, circular state comparisons and duration occupancy |
| Sorting study | Twenty synthetic comparisons, centred ten-bin sorting, circular scores, descriptive regimes and independently generated SVG figures |

The VXP format reference is attributed in [the method documentation](vxp-processing.md).
No third-party parser code, original records, or professional implementation was
transferred. The MIT license applies to this repository's independent materials;
it does not license the referenced manufacturer manual or any original project.

## Excluded capabilities and material

This release documents its own continuous-function conventions, using public
time/amplitude sorting concepts and elementary arithmetic. It does not copy a
private hybrid kinematic engine, clinical tier thresholds, scanner acquisition
rules, reconstruction implementation, or a private interactive dashboard.
Their absence is an explicit scope limit, not evidence that those capabilities
are unnecessary. See [research methods](RESEARCH_METHODS.md).

Unreviewed prototypes, draft manuscripts, original professional code, real
recordings, models, private source mappings, production settings and identifying
metadata remain excluded. No original research figure or manuscript is included. No claim
of mathematical equivalence to an unpublished framework is made.

## Interpretation and future changes

Toy labels are descriptive software outputs without physiological meaning.
The reader does not verify CRC, authenticate recordings, or establish real-device
compatibility. Numeric traces and summaries may remain identifying after headers
are omitted. Passing tests and text scans do not guarantee confidentiality,
anonymity, security, or redistribution permission.

Future methods must have explicit definitions, checked boundary behavior, tests
using invented inputs, suitable provenance, and resolved publication rights.
New files, figures, builds, workflows and material code changes require a fresh
release review and owner approval before publication.

The independently written [browser laboratory](../laboratory/index.html) is a
separate synthetic teaching interface. It imports no recordings and shares no
runtime with the optional Python VXP reader. Its equations, circular metrics,
sample-grid assumptions and exclusions are described in
[laboratory methods](LABORATORY_METHODS.md) and
[laboratory publication scope](LABORATORY_PUBLICATION.md).
