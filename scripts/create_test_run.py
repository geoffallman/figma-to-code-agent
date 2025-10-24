#!/usr/bin/env python3
"""
Test Run Management System

Creates timestamped test run directories to prevent overwriting results.
Each test run gets its own isolated directory with all artifacts.

Usage:
    python scripts/create_test_run.py <test_name>
"""

import sys
import json
from pathlib import Path
from datetime import datetime


def create_test_run(test_name: str) -> dict:
    """
    Create a new test run directory structure.

    Args:
        test_name: Descriptive name for this test (e.g., "pdp-trimmed-baseline")

    Returns:
        dict with paths to all directories
    """

    # Generate timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    run_id = f"{timestamp}_{test_name}"

    # Base test runs directory
    test_runs_dir = Path("output/test-runs")
    run_dir = test_runs_dir / run_id

    # Create directory structure
    dirs = {
        'base': run_dir,
        'code': run_dir / 'code',
        'screenshots': run_dir / 'screenshots',
        'diffs': run_dir / 'diffs',
        'evaluations': run_dir / 'evaluations',
        'images': run_dir / 'images',
        'metadata': run_dir / 'metadata'
    }

    for dir_path in dirs.values():
        dir_path.mkdir(parents=True, exist_ok=True)

    # Create run manifest
    manifest = {
        'run_id': run_id,
        'test_name': test_name,
        'timestamp': timestamp,
        'created_at': datetime.now().isoformat(),
        'directories': {k: str(v) for k, v in dirs.items()},
        'status': 'initialized'
    }

    manifest_path = run_dir / 'manifest.json'
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)

    print("=" * 70)
    print(f"TEST RUN CREATED: {run_id}")
    print("=" * 70)
    print()
    print("Directory structure:")
    for name, path in dirs.items():
        print(f"  {name:15} {path}")
    print()
    print(f"Manifest: {manifest_path}")
    print()
    print("=" * 70)

    return {
        'run_id': run_id,
        'run_dir': str(run_dir),
        'dirs': {k: str(v) for k, v in dirs.items()},
        'manifest_path': str(manifest_path)
    }


def get_latest_run(test_name: str = None) -> str:
    """Get the path to the most recent test run, optionally filtered by name"""
    test_runs_dir = Path("output/test-runs")

    if not test_runs_dir.exists():
        return None

    runs = sorted(test_runs_dir.iterdir(), reverse=True)

    if test_name:
        runs = [r for r in runs if test_name in r.name]

    return str(runs[0]) if runs else None


def list_test_runs():
    """List all test runs"""
    test_runs_dir = Path("output/test-runs")

    if not test_runs_dir.exists():
        print("No test runs found")
        return

    runs = sorted(test_runs_dir.iterdir(), reverse=True)

    print("\n" + "=" * 70)
    print(f"TEST RUNS ({len(runs)} total)")
    print("=" * 70)

    for run_dir in runs[:10]:  # Show last 10
        manifest_path = run_dir / 'manifest.json'
        if manifest_path.exists():
            with open(manifest_path) as f:
                manifest = json.load(f)

            print(f"\n{manifest['run_id']}")
            print(f"  Created: {manifest['created_at']}")
            print(f"  Status: {manifest.get('status', 'unknown')}")
        else:
            print(f"\n{run_dir.name}")
            print(f"  (no manifest)")

    if len(runs) > 10:
        print(f"\n... and {len(runs) - 10} more")

    print("\n" + "=" * 70)


def update_run_status(run_dir: str, status: str, metadata: dict = None):
    """Update the status of a test run"""
    manifest_path = Path(run_dir) / 'manifest.json'

    if not manifest_path.exists():
        print(f"Error: No manifest found at {manifest_path}")
        return

    with open(manifest_path, 'r') as f:
        manifest = json.load(f)

    manifest['status'] = status
    manifest['updated_at'] = datetime.now().isoformat()

    if metadata:
        manifest.update(metadata)

    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)

    print(f"✓ Updated {Path(run_dir).name} status: {status}")


def main():
    """CLI for test run management"""

    if len(sys.argv) < 2:
        print("Usage:")
        print("  Create new run:  python scripts/create_test_run.py <test_name>")
        print("  List runs:       python scripts/create_test_run.py --list")
        print("  Get latest:      python scripts/create_test_run.py --latest [test_name]")
        print()
        print("Example:")
        print("  python scripts/create_test_run.py pdp-trimmed-baseline")
        sys.exit(1)

    command = sys.argv[1]

    if command == '--list':
        list_test_runs()
    elif command == '--latest':
        test_name = sys.argv[2] if len(sys.argv) > 2 else None
        latest = get_latest_run(test_name)
        if latest:
            print(latest)
        else:
            print("No test runs found")
            sys.exit(1)
    else:
        # Create new run
        test_name = command
        result = create_test_run(test_name)

        # Print helpful next steps
        print("Next steps:")
        print()
        print("1. Generate code:")
        print(f"   python scripts/generate_baseline_code.py \\")
        print(f"     output/screenshots/pdp-trimmed-figma.png \\")
        print(f"     output/pdp-trimmed-metadata.json \\")
        print(f"     {result['dirs']['code']}/{test_name}")
        print()
        print("2. Render:")
        print(f"   python scripts/render_with_viewport_match.py \\")
        print(f"     {result['dirs']['code']}/{test_name}.html \\")
        print(f"     output/pdp-trimmed-metadata.json \\")
        print(f"     {result['dirs']['screenshots']}/{test_name}-rendered.png")
        print()
        print("3. Evaluate:")
        print(f"   python scripts/evaluate_combined.py \\")
        print(f"     output/screenshots/pdp-trimmed-figma.png \\")
        print(f"     {result['dirs']['screenshots']}/{test_name}-rendered.png \\")
        print(f"     {result['dirs']['diffs']}/{test_name}-diff.png")
        print()


if __name__ == "__main__":
    main()
