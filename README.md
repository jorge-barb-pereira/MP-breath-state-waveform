# Synthetic Signal States

A Python signal-processing portfolio project demonstrating strict VXP text
parsing, relative timing, amplitude scaling, quality-aware smoothing, and
window statistics. A separate, invented signal example illustrates simple
descriptive state labels. The runtime uses Python's standard library only.

Maintained by [Jorge Barbosa Pereira](https://github.com/jorge-barb-pereira).
This independent edition uses entirely invented examples and makes no clinical
validation or equipment-compatibility claim.

## What this release demonstrates

- A bounded VXP 1.6 reader that follows declared column order and rejects
  malformed, non-finite, duplicate-time, and unsupported inputs.
- Relative seconds and scaled amplitudes, without returning identifying headers.
- Explicit invalid-sample handling and smoothing that does not bridge timing gaps.
- Time-window statistics with valid/total counts and partial-window visibility.
- Continuous cycle functions, state velocities, time-weighted RMS/L2 comparisons,
  and explicit bin-disagreement histograms.
- Deterministic invented fixtures, reproducible CLI examples, and 29 tests.
- An explicit publication allowlist and documented limitations.

The research module uses independently defined maximum/trough/next-maximum
cycles and general time/amplitude normalization. It does not reproduce a private
simulator or claim complete parity with another research implementation.
See [research definitions](docs/RESEARCH_METHODS.md) and
[publication scope](docs/PUBLICATION_SCOPE.md).

![Independent continuous-function examples](docs/figures/breath-state-functions.png)

## Run

Requires Python 3.10 or newer. No installation or network access is needed.

```sh
python -m signal_demo
python -m signal_demo --vxp-demo
python -m signal_demo --vxp examples/synthetic.vxp
python -m signal_demo.research --output output/research
python -m unittest discover -s tests -v
python tools/check_release.py
```

Run these commands from a Git checkout. No account, network connection, package
installation, hardware, or original recording is required. The optional local
reader is demonstrated with the included invented fixture, not clinical data.

To regenerate the optional figure, install Matplotlib from its official package
distribution, then run `python -m signal_demo.research --output output/research --plot`.
The numeric research report and test suite require no plotting dependency.

The command generates twelve seconds of invented samples in memory, prints an
ASCII waveform, and reports one-second windows as `quiet`, `oscillating`, or
`varying`. See [the example output](examples/demo-output.txt). The VXP commands
use invented VXP content and report numeric features without clinical labels.
See [VXP processing methods](docs/vxp-processing.md) and
[the VXP example output](examples/vxp-output.txt).

## Design

- A seeded local random generator makes the example reproducible.
- Three invented four-second segments illustrate different waveform shapes.
- A centered three-sample moving average illustrates smoothing.
- Window features use the original synthetic samples: population standard
  deviation and mean absolute difference between adjacent samples.
- Arbitrary educational cutoffs assign descriptive labels: standard deviation
  below 0.1 means `quiet`; otherwise mean adjacent difference above 0.3 means
  `varying`; remaining windows are `oscillating`.
- The ASCII trace displays the smoothed waveform. Features use unsmoothed data
  so smoothing does not conceal the deliberately introduced variation.

Sample rate, shapes, durations, noise, and cutoffs are invented teaching choices.
They are not fitted to measurements or intended to represent a real population,
device, facility, or operating environment. The states have no physiological or
diagnostic meaning. This project makes no clinical validation claim.

## Repository map

| Path | Purpose |
| --- | --- |
| `signal_demo/core.py` | Invented signal generator, smoothing, features and descriptive labels |
| `signal_demo/vxp.py` | Bounded VXP subset reader and quality-aware numeric processing |
| `signal_demo/__main__.py` | Offline demos and explicitly selected local-file CLI |
| `signal_demo/research.py` | Continuous cycle functions, derivatives, RMS/L2 and bin comparisons |
| `examples/` | Invented VXP fixture and reviewed command output |
| `tests/` | Numerical checks, malformed-input rejection and CLI regressions |
| `docs/` | Format reference, scope, validation and limitations |
| `tools/check_release.py` | Explicit public-file boundary check |

Read the [VXP method reference](docs/vxp-processing.md),
[validation record](docs/VALIDATION.md), and
[contributing guide](CONTRIBUTING.md) for interpretation and maintenance details.

## Scope and provenance

This implementation was written independently for this demonstration. It uses
general arithmetic and Python's standard library. The limited VXP reader is
based on a publicly accessible manufacturer format description, attributed in
the VXP documentation. No professional project code,
records, trained models, configurations, images, or outputs were transferred.
There are no external datasets or third-party code dependencies to redistribute.

The default CLI uses invented samples only. The optional `--vxp LOCAL_FILE`
command reads one explicitly selected local text file and prints a numeric
summary. Metadata removal does not anonymize numeric traces or their summaries.
Use only separately approved inputs. No models, network, or database integrations
are present, and the application writes no result files.

The dimensionless demo rejects incomplete final analysis windows. VXP windows
use timestamps and retain partial windows with counts, excluding invalid rows
from statistics. Non-finite input values are rejected in both paths.

## Release discipline

`PUBLICATION_ALLOWLIST.txt` lists the exact public files, including the invented
VXP fixture. Other VXP recordings are ignored by default. The release check
rejects additional non-ignored files, symlinks, and mismatches between the
allowlist and Git's tracked files. It does not prove confidentiality or inspect
historical commits, staged blob contents, packages, or remote artifacts.

Python bytecode caches and common local configuration files are ignored. No CI,
package-build configuration, external integrations, or upload workflows are
included. Review every file, the staged diff, and the intended commit before
publication; an allowlist and text checks do not establish redistribution rights
or guarantee confidentiality. Any changed release requires a new review.

The sole included PNG is generated from the built-in invented research examples.
Its pixels and metadata require review in addition to text and file checks.

## License

The independently written demonstration is available under the MIT License.
