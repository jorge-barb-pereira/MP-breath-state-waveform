# Validation of the synthetic edition

All checks use independently invented inputs. Original professional code and clinical files are neither executed nor included.

Local verification on November 2, 2026: all 16 tests passed. A browser check confirmed initial rendering, the balanced and paused presets, keyboard slider changes and updated numerical results without console warnings or errors. The charts were visually reviewed. No online CI run or public release is claimed by this local record.

The November 3, 2026 candidate adds centred bins, selected single/dual phase,
continuous/discrete difference panels and separate pointwise/RMSD classifications.
Its 21 automated Node tests passed locally. A desktop browser review of the
updated interface confirmed all six charts, waveform bin tracks, integer bin
axes and matching amplitude legend colours. Balanced dual-phase and paused
presets, phase selection and reset updated the displayed scores and labels.
No console warnings or errors were captured. The interactive 240-sample scores
are explicitly distinguished from the saved 20,000-midpoint study. This review
does not claim exhaustive responsive-browser testing or a new online CI result.

## Reproduce the checks

With Node.js 22 or newer:

```bash
npm test
npm run check:release
```

The test suite verifies:

- Hand-calculated quarter-cycle displacement, velocity and state values.
- Continuity of displacement, velocity and circular amplitude state at the pause edges and periodic join.
- Analytic velocity against central finite differences away from branch changes.
- A flat pause, unchanged cycle length and correct expiration/inspiration durations.
- Circular distance symmetry, wraparound and its half-cycle bound.
- A complete uniform sample grid without a repeated final endpoint.
- Exact repetition of identical cycles and stable boundary assignment for uniform-phase occupancy.
- Occupancy normalization and synthetic unit/period transformations.
- The half-state inspiration transition under asymmetric timing.
- Independent recomputation of RMS and sampled bin mismatch.
- Deterministic numeric CSV output, invalid-input rejection and resource limits.
- RMS sensitivity to an eightfold denser grid for one fixed example.
- Centred half-bin thresholds, periodic joins and signed antipodal ties.
- Small-distance bin mismatch, phase selection and separate RMSD/pointwise rules.
- Known half-cosine RMSD, ten-bin assignments and exported regime/bin fields.
- Offline policy, local assets, unique control IDs and explicit control labels.
- Rejection of extra publication files and credential-like test sentinels.

The release checker requires an exact allowlist, valid UTF-8 files, no symbolic links and no unexpected tracked or historical paths. Its pattern checks are limited heuristics. They are not a guarantee of confidentiality, code correctness, anonymity or authorization to distribute.

## Scientific limits

Passing analytic tests validates the included formulas and implementation against the stated conventions. It does not establish physiological realism, clinical utility, scanner compatibility or medical-device commissioning. No performance on patient data is claimed. A bounded software review cannot establish that every possible defect is absent.
