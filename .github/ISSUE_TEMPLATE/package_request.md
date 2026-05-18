---
name: Package request
about: Request a new Python package or a version update
title: ""
labels: new package request
assignees: ""
---

<!--
Important Note:

With the acceptance of PEP 783 (https://peps.python.org/pep-0783/), package maintainers can now
build and publish Pyodide-compatible wheels directly to PyPI. Before requesting a new recipe here,
please consider contacting the package maintainers and asking them to publish Emscripten/Pyodide
wheels from their own repository. This is the preferred approach going forward.

For more details, see:
- Pyodide docs on building packages: https://pyodide-build.readthedocs.io/en/latest/
- cibuildwheel Pyodide support: https://cibuildwheel.pypa.io/en/stable/options/#platform
-->

## 🐍 Package Request

- Package Name and Version <!-- (e.g. pandas / latest) -->:
- Package URL <!--  (e.g. github link, PyPI link) -->:
- Package Dependencies that needs to be resolved first:

## Checklists

- [ ] I have tried to install the package using `micropip.install(...)` and encountered the issue.
- [ ] I have considered contacting the package maintainers to publish Pyodide wheels upstream (see [PEP 783](https://peps.python.org/pep-0783/)).
- [ ] I have read the [documentation](https://pyodide-build.readthedocs.io/en/latest/) and tried building the package myself.
