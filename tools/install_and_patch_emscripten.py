import shutil
import subprocess as sp
from pathlib import Path
import os

# TODO: Make public CLI for this
from pyodide_build.build_env import get_pyodide_root, get_build_flag


root_dir = Path(__file__).parent.parent
emsdk_dir = root_dir / "emsdk"
emscripten_root = emsdk_dir / "upstream" / "emscripten"


def clone_emsdk():
    sp.run([
        "rm",
        "-rf",
        str(emsdk_dir),
    ])

    sp.run([
        "git",
        "clone",
        "--depth",
        "1",
        "https://github.com/emscripten-core/emsdk.git",
        str(emsdk_dir),
    ])


def install_emsdk(version: str, patch_dir: Path):

    sp.run([
        "./emsdk",
        "install",
        "--build=Release",
        version,
    ], cwd=emsdk_dir, check=True)

    sp.run(f"cat {patch_dir}/*.patch | patch -p1 --verbose", check=True, shell=True, cwd=emscripten_root)

    sp.run([
        "./emsdk",
        "activate",
        "--embedded",
        "--build=Release",
        version,
    ], cwd=emsdk_dir, check=True)

def main():
    print("Cloning emsdk...")

    clone_emsdk()

    print("Installing emsdk...")

    emscripten_version = get_build_flag("PYODIDE_EMSCRIPTEN_VERSION")
    pyodide_root = get_pyodide_root()
    patch_path = pyodide_root / "emsdk" / "patches"

    print(f"Using emscripten version: {emscripten_version}")
    print(f"Using pyodide root: {pyodide_root}")
    print(f"Using patch path: {patch_path}")

    install_emsdk(
        emscripten_version,
        patch_path,
    )

    print("Installing emsdk complete.")
    print(f"Use `source {emsdk_dir}/emsdk_env.sh` to set up the environment.")

if __name__ == "__main__":
    main()