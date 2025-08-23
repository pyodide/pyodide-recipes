#!/bin/bash

PACKAGE_BUILD_DIR=${1:-$(pwd)/dist}
DIST_DIR=$(pyodide config get dist_dir)
mkdir -p ${PACKAGE_BUILD_DIR}
cp -r $DIST_DIR/pyodide.js $DIST_DIR/pyodide.mjs $DIST_DIR/pyodide.asm.js $DIST_DIR/pyodide.asm.wasm $DIST_DIR/python_stdlib.zip ${PACKAGE_BUILD_DIR}/
