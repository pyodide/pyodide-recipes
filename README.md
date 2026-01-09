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

See the [Pyodide documentation](https://pyodide.org/en/stable/development/adding-packages-into-pyodide-distribution.html)
for more information on creating package recipes.

## Updating an existing package

Assuming you've already followed the setup instructions above, just run:

```bash
$ pyodide skeleton pypi <package-name> --update
```

## How to use the recipes in Pyodide

There are three ways to use the packages built by this repository in Pyodide:

### 1. Wait until the next Pyodide release

When we release a new version of Pyodide, we include the updated recipes in the Pyodide distribution.
But we don't guarantee that patch releases of Pyodide will include the updated recipes.

### 2. Use Anaconda package index

We also release the recipes to Anaconda package index. You can pass the following indesx URLs to `micropip` to install the packages
from the index.

- `https://pypi.anaconda.org/pyodide/simple`: Contains all the packages built for all stable versions of Pyodide since Pyodide 0.28.0.
- `https://pypi.anaconda.org/pyodide-nightly/simple`: Contains the tip-of-tree packages which exist in the `main` branch of this repository.

### 3. Download the release artifact from GitHub releases

We release the built packages as a tarball in the GitHub releases occassionally.
You can download the tarball and host it on your own server.

## Maintainer information

See [MAINTAINERS.md](docs/MAINTAINERS.md) for information on how to maintain this repository.
