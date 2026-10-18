# Synthetic Signal States

A small, dependency-free Python project with a synthetic signal demonstration
and independently implemented VXP text-processing methods: parsing, relative
timing, amplitude scaling, validity handling, smoothing, and window statistics.
It is an educational software example, not a medical application.

## Run

Requires Python 3.10 or newer. No installation or network access is needed.

```sh
python -m signal_demo
python -m signal_demo --vxp-demo
python -m signal_demo --vxp examples/synthetic.vxp
python -m unittest discover -s tests -v
python tools/check_release.py
```

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

## License

The independently written demonstration is available under the MIT License.
