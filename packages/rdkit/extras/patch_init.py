"""Patch rdkit/__init__.py for emscripten/Pyodide support.

The librdkit_core.so shared library is pre-loaded by Pyodide via the librdkit
shared_library package (asynchronously during loadPackage, avoiding Chrome's
8MB sync WebAssembly.Compile limit). However, Pyodide loads it with RTLD_NOW
(no RTLD_GLOBAL), so we need to re-open it with RTLD_GLOBAL to make symbols
available to the wrapper modules. Re-opening is instant since the module is
already compiled and cached.

This patch also registers a custom MetaPathFinder to load .so.wasm wrapper
modules.
"""

init_path = "rdkit/__init__.py"
init = open(init_path).read()

loader = '''import sys as _sys

if _sys.platform == 'emscripten':
    import os as _os
    import importlib.abc
    import importlib.machinery

    # Set RDBASE so RDConfig.py finds Data/, Docs/, etc. relative to this package
    _os.environ['RDBASE'] = _os.path.dirname(__file__)

    # Re-open librdkit_core.so with {global: true} so wrapper modules can
    # resolve symbols. The library was already loaded (and WASM-compiled) by
    # Pyodide via the librdkit shared_library package, so this re-open is
    # instant — no recompilation, just promoting symbols to global scope.
    from pyodide_js._module import loadDynamicLibrary as _ldl
    import js as _js
    _ldl("/usr/lib/librdkit_core.so", _js.JSON.parse('{"global": true}'))
    del _ldl, _js

    class _RDKitExtensionFinder(importlib.abc.MetaPathFinder):
        def find_spec(self, fullname, path, target=None):
            parts = fullname.split('.')
            if parts[0] != 'rdkit':
                return None
            modname = parts[-1]
            if path:
                for d in path:
                    candidate = _os.path.join(d, modname + '.so.wasm')
                    if _os.path.exists(candidate):
                        loader = importlib.machinery.ExtensionFileLoader(
                            fullname, candidate
                        )
                        return importlib.util.spec_from_file_location(
                            fullname, candidate, loader=loader,
                        )
            return None

    import importlib.util
    _sys.meta_path.insert(0, _RDKitExtensionFinder())

'''

open(init_path, "w").write(loader + init)
print("Patched rdkit/__init__.py")
