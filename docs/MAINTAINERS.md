# Maintainer information

## How packages are built and tested in CI

When a PR is opened, the GHA workflow will build submitted packages and run tests on them.
It only builds the packages that have been modified in the PR, and their dependenciesto reduce the build time.
See [tools/calc_diff.py](../tools/calc_diff.py) for the logic used to determine which packages to build.

When the PR is merged, the GHA workflow will build all packages in the repository and run tests on them.
Optionally, you can trigger a full build by adding the `[full build]` in the PR title.

The packages are always built with the tip-of-tree commit of Pyodide, fetching it directly from the CDN.
This is to ensure that the packages in this repository are always compatible with the latest version of Pyodide.

## Releasing a new package set and updating the Pyodide distribution

Adding a new tag to the repository will trigger a release of the package set.
It is recommended to use the calendar versioning scheme for tags, e.g. `20240810`.

```
git tag 20240810
git push origin 20240810
```

After the release is made, you can update the package set in the Pyodide distribution
by updating the `Makefile.envs` file in the pyodide/pyodide repository.

## Building and testing packages locally

To build and test packages locally, you need to prepare the necessary tools and dependencies.

- compatible Python version
- pyodide-build, which is provided by the `pyodide-build` Git submodule in the repository root
- emscripten
- selenium (for testing)

The compatible Python version is specified in the `environment.yml` file in the root directory of the repository.
If you are using conda, you can create a new environment with the following command:

```bash
conda env create -f environment.yml
conda activate pyodide-env
```

After activating the environment, you can install the necessary tools and dependencies with the following command:

```bash
./tools/prepare_pyodide_build.sh
python tools/install_and_patch_emscripten.py
```

This will install the `pyodide-build` and `emscripten` tools in the current environment.
You can then build the packages with the following command:

```bash
pyodide build-recipes "<pkg1>,<pkg2>,..."
```

## Updating the Pyodide xbuildenv

To update the Pyodide xbuildenv, you need to update the `default_cross_build_env_url` variable in the `pyproject.toml` file.

## Supporting stable and nightly Pyodide

> [!NOTE]
> This section is not implemented yet. It mostly describes the intended behavior in the future, and
> is not a description of the current behavior.

The `pyodide-recipes` repository is used to build packages for both stable and nightly versions of Pyodide.

We use different branches for those versions:

- `main`: the default branch, used for nightly versions of Pyodide
  - It uses nightly xbuildenv and the pyodide-build submodule to build packages.
- `<version>`: a branch for stable versions of Pyodide
  - It uses stable xbuildenv and pyodide-build submodule (or a stable version, if there are any breaking changes) to build packages.

Let's say we have a stable Pyodide version `0.27.0`, and we are developing a new version `0.28.0`.

- We use two branches: `0.27.X` and `main`.
- The `0.27.X` branch is used to build packages for the stable version `0.27.X`.
  - If we need any bugfixes or new packages for the stable version, we push them to the `0.27.X` branch.
- The `main` branch is used to build packages for the nightly version.
  - Any new packages or bugfixes that are not compatible with the stable version will be pushed to the `main` branch.
  - The `main` branch will be used to release the package set for `0.28.0`.
- After the release of `0.28.0`, we will create a new branch `0.28.X` from the `main` branch.
  - The `0.28.X` branch will be used to build packages for the stable version `0.28.X`.