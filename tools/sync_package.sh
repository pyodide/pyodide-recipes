#!/bin/bash

# Usage: ./tools/sync_package.sh

# sync all recipes in pyodide/pyodide into this repository.
# TODO: remoe this script when all recipes are migrated

# Remove all existing recipes (directories)
find packages -mindepth 1 -maxdepth 1 -type d -exec rm -rf {} \;

rm -rf pyodide
git clone https://github.com/pyodide/pyodide --depth 1
find pyodide/packages -mindepth 1 -maxdepth 1 -type d -exec cp -r {} packages/ \;
rm -rf packages/_tests
rm -rf pyodide