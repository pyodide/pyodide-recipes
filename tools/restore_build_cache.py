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

    # Load cached manifest
    manifest_path = cache_dir / "manifest.json"
    if not manifest_path.exists():
        print("No cache manifest found — this is a cold start, nothing to restore.")
        print(f"  Cache dir: {cache_dir}")
        print(f"  Expected manifest at: {manifest_path}")
        return

    cached_manifest = json.loads(manifest_path.read_text())
    cached_fingerprints: dict[str, str] = cached_manifest.get("fingerprints", {})

    # Restore packages
    restored = 0
    skipped_cross_build = 0
    skipped_stale = 0
    skipped_missing = 0
    skipped_no_fingerprint = 0

    for pkg_name, current_fp in sorted(current_fingerprints.items()):
        # Skip cross-build-env packages — they must always be rebuilt
        if pkg_name in cross_build_packages:
            skipped_cross_build += 1
            continue

        # Check if cache has this package
        cached_fp = cached_fingerprints.get(pkg_name)
        if cached_fp is None:
            skipped_no_fingerprint += 1
            continue

        # Check fingerprint match
        if cached_fp != current_fp:
            skipped_stale += 1
            continue

        # Check if cached artifacts exist
        cached_pkg_dir = cache_dir / pkg_name
        if not cached_pkg_dir.exists():
            skipped_missing += 1
            continue

        # Restore artifacts
        dist_dir = packages_dir / pkg_name / "dist"
        dist_dir.mkdir(parents=True, exist_ok=True)

        files_restored = 0
        for cached_file in cached_pkg_dir.iterdir():
            if cached_file.is_file():
                dest = dist_dir / cached_file.name
                shutil.copy2(cached_file, dest)
                # Apply mtime trick — set to far future
                os.utime(dest, (FUTURE_MTIME, FUTURE_MTIME))
                files_restored += 1

        if files_restored > 0:
            restored += 1

    # Also restore .libs/ if cached (for static/shared library packages)
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

    # Summary
    total = len(current_fingerprints)
    will_build = total - restored
    print(f"Cache restore summary:")
    print(f"  Total packages in build plan: {total}")
    print(f"  Restored from cache: {restored}")
    print(f"  Skipped (cross-build-env, always rebuild): {skipped_cross_build}")
    print(f"  Skipped (fingerprint changed): {skipped_stale}")
    print(f"  Skipped (not in cache): {skipped_no_fingerprint}")
    print(f"  Skipped (cached files missing): {skipped_missing}")
    print(f"  Will need to build: {will_build}")


if __name__ == "__main__":
    main()
