# pyodide-recipes

Collections of package recipes for Pyodide

## Adding a new package

> Note: Use Python 3.13 or upper to run the following commands.

To add a new package, create a package recipe in the `packages` directory.

It is required to clone the repository with the `--recurse-submodules` option to ensure
that all submodules are initialized. If you have already cloned the repository without
this option, you can run the following command to initialize the submodules:

```bash
$ git submodule update --init --recursive
```

You can then start by creating a boilerplate recipe with the following command:

```bash
$ pip install ./pyodide-build
$ pyodide skeleton pypi <package-name>
```

This will create a new directory in the `packages/` directory with the package name.
You can then edit the `meta.yaml` file in the package directory to add build scripts
and other metadata including the dependencies.

See the [Pyodide documentation](https://pyodide.org/en/stable/development/new-packages.html)
for more information on creating package recipes.

## Maintainer information

See [MAINTAINERS.md](docs/MAINTAINERS.md) for information on how to maintain this repository.
