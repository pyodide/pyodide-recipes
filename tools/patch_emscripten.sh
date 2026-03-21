#!/bin/bash

EMSCRIPTEN_PATH="$(pyodide config get pyodide_root)/../../emsdk/upstream/emscripten"
CURRENT_DIR="$(dirname "$(realpath "$0")")"

echo "EMSCRIPTEN_PATH: $EMSCRIPTEN_PATH"
cp "$CURRENT_DIR/cache.py" "$EMSCRIPTEN_PATH/tools/cache.py"
cp "$CURRENT_DIR/system_libs.py" "$EMSCRIPTEN_PATH/tools/system_libs.py"