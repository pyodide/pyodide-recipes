#!/usr/bin/env python
"""Restore cached wheels from the .wheel-cache directory and apply the mtime trick.

This script is run after `actions/cache/restore` has restored .wheel-cache/.
For each package whose cached fingerprint matches the current build-plan.json,
it copies the wheel into packages/{name}/dist/ and sets the mtime to the far
future (year 2099) so that needs_rebuild() skips it.

Cross-build-env packages are always skipped (they must be rebuilt for their
host-environment side effects).
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
PACKAGES_DIR = BASE_DIR / "packages"

# 2099-12-31T00:00:00Z — guaranteed newer than any git checkout mtime
FUTURE_MTIME = 4_102_444_800


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Restore cached wheels and apply mtime trick"
    )
    parser.add_argument(
        "--cache-dir",
        type=str,
        required=True,
        help="Path to the .wheel-cache directory",
    )
    parser.add_argument(
        "--build-plan",
        type=str,
        required=True,
        help="Path to build-plan.json",
    )
    parser.add_argument(
        "--packages-dir",
        type=str,
        default=str(PACKAGES_DIR),
        help="Path to the packages directory",
    )
    return parser.parse_args()


def _cleanup_stale_pc_files(libs_dir: Path) -> None:
    """Remove .pc files whose includedir references non-existent paths.

    Some packages (e.g. healpy) bundle C subprojects that install .pc files
    to .libs/lib/pkgconfig/ with prefix pointing into a per-package build temp
    directory. After cache restore, those build temp dirs don't exist, but the
    stale .pc files cause pkg-config to report libraries as 'found', skipping
    the source build and causing missing-header errors at compile time.

    Real library packages install with prefix=.libs/ so their paths survive
    cache restore. Only stale entries (pointing outside .libs/) are removed.
    """
    removed = 0
    for pc_dir in [libs_dir / "lib" / "pkgconfig", libs_dir / "lib64" / "pkgconfig"]:
        if not pc_dir.is_dir():
            continue
        for pc_file in pc_dir.glob("*.pc"):
            prefix = _parse_pc_variable(pc_file, "prefix")
            if prefix and not Path(prefix).is_dir():
                pc_file.unlink()
                removed += 1
    if removed:
        print(f"  Removed {removed} stale .pc file(s) from {libs_dir}")


def _parse_pc_variable(pc_file: Path, var_name: str) -> str | None:
    """Extract a top-level variable assignment from a .pc file.

    Reads lines like 'prefix=/some/path' (not ${...} references).
    """
    try:
        for line in pc_file.read_text().splitlines():
            line = line.strip()
            if line.startswith(f"{var_name}="):
                return line.split("=", 1)[1].strip()
    except OSError:
        pass
    return None

def main() -> None:
    args = parse_args()
    cache_dir = Path(args.cache_dir)
    build_plan_path = Path(args.build_plan)
    packages_dir = Path(args.packages_dir)

    # Load build plan
    if not build_plan_path.exists():
        print(f"Error: build plan not found at {build_plan_path}", file=sys.stderr)
        sys.exit(1)

    build_plan = json.loads(build_plan_path.read_text())
    current_fingerprints: dict[str, str] = build_plan["fingerprints"]
    cross_build_packages: list[str] = build_plan.get("cross_build_packages", [])
    library_packages: set[str] = set(build_plan.get("library_packages", []))

    manifest_path = cache_dir / "manifest.json"
    if not manifest_path.exists():
        print("No cache manifest found — cold start, nothing to restore.")
        print(f"  Cache dir: {cache_dir}")
        print(f"  Expected manifest at: {manifest_path}")
        return

    cached_manifest = json.loads(manifest_path.read_text())
    cached_fingerprints: dict[str, str] = cached_manifest.get("fingerprints", {})

    restored_wheels = 0
    restored_libraries = 0
    skipped_cross_build = 0
    skipped_stale = 0
    skipped_missing = 0
    skipped_no_fingerprint = 0

    for pkg_name, current_fp in sorted(current_fingerprints.items()):
        if pkg_name in cross_build_packages:
            skipped_cross_build += 1
            continue

        cached_fp = cached_fingerprints.get(pkg_name)
        if cached_fp is None:
            skipped_no_fingerprint += 1
            continue

        if cached_fp != current_fp:
            skipped_stale += 1
            continue

        if pkg_name in library_packages:
            # Library packages (static_library/shared_library) don't produce wheels.
            # needs_rebuild() checks build/.packaged token mtime instead.
            # Create the token with future mtime so needs_rebuild() returns False.
            build_dir = packages_dir / pkg_name / "build"
            build_dir.mkdir(parents=True, exist_ok=True)
            packaged_token = build_dir / ".packaged"
            packaged_token.touch()
            os.utime(packaged_token, (FUTURE_MTIME, FUTURE_MTIME))
            restored_libraries += 1
            continue

        cached_pkg_dir = cache_dir / pkg_name
        if not cached_pkg_dir.exists():
            skipped_missing += 1
            continue

        dist_dir = packages_dir / pkg_name / "dist"
        dist_dir.mkdir(parents=True, exist_ok=True)

        files_restored = 0
        for cached_file in cached_pkg_dir.iterdir():
            if cached_file.is_file():
                dest = dist_dir / cached_file.name
                shutil.copy2(cached_file, dest)
                os.utime(dest, (FUTURE_MTIME, FUTURE_MTIME))
                files_restored += 1

        if files_restored > 0:
            restored_wheels += 1

    libs_cache_dir = cache_dir / ".libs"
    if libs_cache_dir.exists():
        libs_dest = packages_dir / ".libs"
        libs_dest.mkdir(parents=True, exist_ok=True)
        for cached_file in libs_cache_dir.rglob("*"):
            if cached_file.is_file():
                rel = cached_file.relative_to(libs_cache_dir)
                dest = libs_dest / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(cached_file, dest)
                os.utime(dest, (FUTURE_MTIME, FUTURE_MTIME))

    # Some packages (e.g. healpy) bundle C libraries and install .pc files
    # to .libs/lib/pkgconfig/ with prefix pointing into their build temp dir.
    # On rebuild, the build temp is clean but stale .pc files trick pkg-config
    # into thinking libraries are installed, causing missing header errors.
    _cleanup_stale_pc_files(packages_dir / ".libs")

    total = len(current_fingerprints)
    restored = restored_wheels + restored_libraries
    will_build = total - restored - skipped_cross_build
    print(f"Cache restore summary:")
    print(f"  Total packages in build plan: {total}")
    print(f"  Restored wheel packages: {restored_wheels}")
    print(f"  Restored library packages: {restored_libraries}")
    print(f"  Skipped (cross-build-env, always rebuild): {skipped_cross_build}")
    print(f"  Skipped (fingerprint changed): {skipped_stale}")
    print(f"  Skipped (not in cache): {skipped_no_fingerprint}")
    print(f"  Skipped (cached files missing): {skipped_missing}")
    print(f"  Will need to build: {will_build}")


if __name__ == "__main__":
    main()
