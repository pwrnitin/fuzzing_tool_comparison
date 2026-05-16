#!/usr/bin/env python3
"""
phase3_dedup.py — Post-hoc deduplication and bug mapping for Phase 2 runs.

For each Phase 2 configuration:
  1. Finds all crash artifacts
  2. Runs each through the LibFuzzer binary to get sanitizer output
  3. Extracts error type + stack signature
  4. Maps to one of the 4 planted bugs in fuzzgoat.c
  5. Emits a per-run summary CSV

Run from project root:
    python3 scripts/phase3_dedup.py
"""

import argparse
import csv
import hashlib
import multiprocessing as mp
import re
import subprocess
from pathlib import Path

PLANTED_BUGS = {
    1: 'use-after-free in json_value_free() (line 134)',
    2: 'invalid free via length-- decrement (line 255)',
    3: 'invalid free on decremented string pointer (line 275)',
    4: 'NULL pointer dereference (line 297)',
}


def classify_crash(sanitizer_output):
    """Return (bug_id, stack_hash) for a sanitizer output."""
    # Find the SUMMARY line
    summary = re.search(r'SUMMARY:\s+(\w+):\s+([\w-]+)\s+(\S+)', sanitizer_output)
    if not summary:
        return 0, None
    sanitizer = summary.group(1)  # AddressSanitizer / UndefinedBehaviorSanitizer
    error_type = summary.group(2)
    location = summary.group(3)

    # Bug classification: matches what we observed in Phase 1 validation
    bug_id = 0
    if 'heap-use-after-free' in error_type:
        bug_id = 1
    elif 'heap-buffer-overflow' in error_type:
        bug_id = 2
    elif 'bad-free' in error_type:
        bug_id = 3
    elif 'undefined-behavior' in error_type:
        # bug 2 manifests as UBSan on line 258 or 529; bug 4 on line 298
        if ':298' in location:
            bug_id = 4
        elif ':258' in location or ':529' in location:
            bug_id = 2
    elif 'SEGV' in error_type or 'segv' in error_type.lower():
        bug_id = 4

    # Stack hash: hash the top 3 named stack frames
    frames = re.findall(r'#\d+\s+0x[0-9a-fA-F]+\s+in\s+(\w+)', sanitizer_output)
    stack_hash = hashlib.md5(' '.join(frames[:3]).encode()).hexdigest()[:12]

    return bug_id, stack_hash


def process_one_crash(args):
    crash_file, binary_path = args
    try:
        result = subprocess.run(
            [binary_path, str(crash_file)],
            capture_output=True, timeout=10,
            env={'ASAN_OPTIONS': 'detect_leaks=0:abort_on_error=0:halt_on_error=1',
                 'UBSAN_OPTIONS': 'print_stacktrace=1:halt_on_error=1'},
        )
        output = (result.stdout + result.stderr).decode('utf-8', errors='replace')
        return classify_crash(output)
    except Exception:
        return 0, None


def find_crash_files(tool, budget, seed, output_root):
    run_dir = Path(output_root) / f'{budget}s' / f'{tool}_seed{seed}'
    if tool == 'lf':
        return sorted(run_dir.glob('crash-*'))
    elif tool == 'afl':
        crashes_dir = run_dir / 'afl_out' / 'default' / 'crashes'
        return sorted(crashes_dir.glob('id:*')) if crashes_dir.exists() else []
    elif tool == 'hfuzz':
        return sorted((run_dir / 'hfuzz_ws').glob('*.fuzz'))
    return []


def process_run(tool, budget, seed, output_root, binary, workers):
    crashes = find_crash_files(tool, budget, seed, output_root)
    if not crashes:
        return {'total': 0, 'unique_stacks': 0, 'bugs_found': set(), 'sampled': 0}

    args = [(c, str(binary)) for c in crashes]
    with mp.Pool(workers) as pool:
        results = pool.map(process_one_crash, args)

    stacks = set()
    bugs = set()
    for bug_id, stack_hash in results:
        if stack_hash:
            stacks.add(stack_hash)
        if bug_id > 0:
            bugs.add(bug_id)
    return {'total': len(crashes), 'unique_stacks': len(stacks),
            'bugs_found': bugs, 'sampled': len(results)}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--output-root', default='runs/phase2')
    p.add_argument('--binary', default='build/fuzzgoat_lf/fuzzgoat_lf')
    p.add_argument('--out', default='results/phase3_per_run.csv')
    p.add_argument('--workers', type=int, default=4)
    args = p.parse_args()

    binary = Path(args.binary).resolve()
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    header = ['tool', 'budget_s', 'run_id', 'crashes_total',
              'unique_stacks', 'bugs_found_count', 'bug_1', 'bug_2', 'bug_3', 'bug_4']

    rows = []
    for budget in (60, 300, 1800):
        for tool in ('lf', 'afl', 'hfuzz'):
            for seed in (1, 2, 3):
                print(f'[{tool} b={budget}s seed={seed}] processing...', flush=True)
                r = process_run(tool, budget, seed, args.output_root, binary, args.workers)
                row = {
                    'tool': tool, 'budget_s': budget, 'run_id': seed,
                    'crashes_total': r['total'],
                    'unique_stacks': r['unique_stacks'],
                    'bugs_found_count': len(r['bugs_found']),
                    'bug_1': 1 if 1 in r['bugs_found'] else 0,
                    'bug_2': 1 if 2 in r['bugs_found'] else 0,
                    'bug_3': 1 if 3 in r['bugs_found'] else 0,
                    'bug_4': 1 if 4 in r['bugs_found'] else 0,
                }
                rows.append(row)
                print(f'    crashes={r["total"]} unique_stacks={r["unique_stacks"]} '
                      f'bugs_found={sorted(r["bugs_found"])}', flush=True)

    with open(out_path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=header)
        w.writeheader()
        w.writerows(rows)
    print(f'\nWrote {len(rows)} rows to {out_path}')


if __name__ == '__main__':
    main()
