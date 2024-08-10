# Maintainer information

## How packages are built and tested in CI

When a PR is opened, the GHA workflow will build submitted packages and run tests on them.
It only builds the packages that have been modified in the PR, and their dependenciesto reduce the build time.
See [tools/calc_diff.py](../tools/calc_diff.py) for the logic used to determine which packages to build.

When the PR is merged, the GHA workflow will build all packages in the repository and run tests on them.
Optionally, you can trigger a full build by adding the `[full build]` commit message to the PR.

The packages are always built with the tip-of-tree commit of Pyodide, fetching it directly from the CDN.
This is to ensure that the packages in this repository are always compatible with the latest version of Pyodide.

## Releasing a new package set and updating the Pyodide distribution

Adding a new tag to the repository will trigger a release of the package set.
It is recommended to use the calendar versioning scheme for tags, e.g. `20240810`.

```
git tag 20240810
git push origin 20240810
```

__(THIS IS NOT YET IMPLEMENTED)__

After the release is done, you can update the package set in the Pyodide distribution
by updating the `Makefile.envs` file in the pyodide/pyodide repository.

## Building and testing packages locally

To build and test packages locally, you need to prepare the necessary tools and dependencies.

- compatible Python version
- pyodide-build
- emscripten
- selenium (for testing)

if you need to use a tip-of-tree commit of Pyodide,
you can install it manually from the following url:

```
pyodide xbuildenv install --url http://pyodide-cache.s3-website-us-east-1.amazonaws.com/xbuildenv/dev/xbuildenv.tar.bz2
```