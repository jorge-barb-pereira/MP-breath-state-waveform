# Contributing

Keep changes small, reproducible, and consistent with the documented scope.
Public source, comments, examples, and documentation must be in English.

## Verify a change

From the repository root, using Python 3.10 or newer:

```sh
python -m unittest discover -s tests -v
python -m signal_demo
python -m signal_demo --vxp-demo
python -m signal_demo --vxp examples/synthetic.vxp
python tools/check_release.py
```

The release checker compares Git's tracked inventory with the explicit
allowlist. A contributor must still inspect the full diff and file contents.
It does not validate staged blobs, historical commits, image pixels, packages,
or confidentiality. Do not treat passing tests as clinical validation.

## Input and disclosure boundaries

Use invented fixtures or separately approved public material with suitable
attribution. Do not add professional source code, real recordings, local
configuration, identifiers, credentials, saved notebook outputs, trained models,
or private reports to files, commits, issues, screenshots, or workflow artifacts.
Removing a header does not anonymize numeric samples or summaries.

For parser regressions, construct the smallest invented example demonstrating
the issue. Describe errors without including private filenames or field values.
Do not attach an original recording to an issue report.

Changing the implementation or adding a public artifact requires review of the
exact files and commit before publication. Update the allowlist deliberately;
stage individually named files and inspect the staged diff. Any future package
build or CI artifact must receive its own content review. No publishing workflow
is currently configured.

Original professional code and research-specific frameworks need independently
established redistribution permission. Authorship or possession alone does not
establish those rights. Keep uncertain material outside this repository.
