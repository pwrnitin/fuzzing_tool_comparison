#!/usr/bin/env python3
"""
run_one_fuzzgoat.py — Run one Fuzzgoat fuzzing configuration and append one row
to the master CSV.
"""

import argparse
import csv
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path


CSV_HEADER = [
    'tool', 'target', 'budget_s', 'run_id', 'time_s',
    'execs_done', 'execs_per_sec', 'corpus_count', 'coverage_metric',
    'peak_rss_mb', 'crashes_total', 'crashes_unique',
    'time_to_first_crash_s',
]


def run_libfuzzer(project_root, budget, seed, output_dir):
    binary = project_root / 'build' / 'fuzzgoat_lf' / 'fuzzgoat_lf'
    corpus_in = project_root / 'corpus_base' / 'fuzzgoat'
    output_dir.mkdir(parents=True, exist_ok=True)
    log_file = output_dir / 'run.log'

    cmd = [
        str(binary), str(corpus_in),
        f'-max_total_time={budget}',
        '-rss_limit_mb=2048', '-timeout=2',
        '-fork=1', '-ignore_crashes=1',
        f'-seed={seed}',
    ]
    print(f'[lf seed={seed} budget={budget}s] starting', flush=True)
    t0 = time.time()
    with open(log_file, 'w') as logf:
        subprocess.run(cmd, cwd=str(output_dir), stdout=logf,
                       stderr=subprocess.STDOUT)
    elapsed = time.time() - t0

    crash_files = sorted(output_dir.glob('crash-*'))
    crashes_total = len(crash_files)
    ttfc = min((f.stat().st_mtime for f in crash_files), default=None)
    ttfc = (ttfc - t0) if ttfc is not None else ''

    log_text = log_file.read_text(errors='replace')
    execs_done = _last_int(r'#(\d+):\s+cov:', log_text)
    coverage = _last_int(r'cov:\s*(\d+)\s+ft:', log_text)
    corpus_count = _last_int(r'corp:\s*(\d+)\s+exec/s:', log_text)
    execs_per_sec = (execs_done / elapsed) if execs_done and elapsed > 0 else ''
    peak_rss = ''

    return {
        'time_s': round(elapsed, 1),
        'execs_done': execs_done or '',
        'execs_per_sec': round(execs_per_sec, 1) if execs_per_sec else '',
        'corpus_count': corpus_count or '',
        'coverage_metric': coverage or '',
        'peak_rss_mb': peak_rss,
        'crashes_total': crashes_total,
        'crashes_unique': crashes_total,
        'time_to_first_crash_s': round(ttfc, 2) if ttfc != '' else '',
    }


def run_aflpp(project_root, budget, seed, output_dir):
    binary = project_root / 'build' / 'fuzzgoat_afl' / 'fuzzgoat_afl'
    afl_in = project_root / 'afl_in_fuzzgoat'
    if not afl_in.exists():
        afl_in.mkdir(parents=True)
        for f in (project_root / 'corpus_base' / 'fuzzgoat').iterdir():
            shutil.copy(f, afl_in)

    output_dir.mkdir(parents=True, exist_ok=True)
    afl_out = output_dir / 'afl_out'
    if afl_out.exists():
        shutil.rmtree(afl_out)

    cmd = [
        'afl-fuzz', '-i', str(afl_in), '-o', str(afl_out),
        '-V', str(budget), '-t', '2000', '-m', 'none',
        '-s', str(seed),
        '--', str(binary), '@@',
    ]
    env = dict(os.environ)
    env.setdefault('AFL_NO_UI', '1')
    env.setdefault('AFL_SKIP_CPUFREQ', '1')

    print(f'[afl seed={seed} budget={budget}s] starting', flush=True)
    t0 = time.time()
    with open(output_dir / 'run.log', 'w') as logf:
        subprocess.run(cmd, stdout=logf, stderr=subprocess.STDOUT, env=env)
    elapsed = time.time() - t0

    stats_file = afl_out / 'default' / 'fuzzer_stats'
    crashes_dir = afl_out / 'default' / 'crashes'
    crash_files = sorted(p for p in (crashes_dir.glob('id:*') if crashes_dir.exists() else []))
    crashes_total = len(crash_files)

    ttfc = ''
    if crash_files:
        times_ms = []
        for f in crash_files:
            m = re.search(r'time:(\d+)', f.name)
            if m:
                times_ms.append(int(m.group(1)))
        if times_ms:
            ttfc = round(min(times_ms) / 1000.0, 2)

    stats = _parse_kv_file(stats_file) if stats_file.exists() else {}
    bitmap_cvg = stats.get('bitmap_cvg', '').rstrip('%').strip()

    return {
        'time_s': round(elapsed, 1),
        'execs_done': stats.get('execs_done', ''),
        'execs_per_sec': stats.get('execs_per_sec', ''),
        'corpus_count': stats.get('corpus_count', ''),
        'coverage_metric': bitmap_cvg,
        'peak_rss_mb': '',
        'crashes_total': crashes_total,
        'crashes_unique': crashes_total,
        'time_to_first_crash_s': ttfc,
    }


def run_honggfuzz(project_root, budget, seed, output_dir):
    binary = project_root / 'build' / 'fuzzgoat_hf' / 'fuzzgoat_hf'
    hf_in = project_root / 'hfuzz_in_fuzzgoat'
    if not hf_in.exists():
        hf_in.mkdir(parents=True)
        for f in (project_root / 'corpus_base' / 'fuzzgoat').iterdir():
            shutil.copy(f, hf_in)

    output_dir.mkdir(parents=True, exist_ok=True)
    workspace = output_dir / 'hfuzz_ws'
    if workspace.exists():
        shutil.rmtree(workspace)
    workspace.mkdir()

    cmd = [
        'honggfuzz',
        '--input', str(hf_in),
        '--workspace', str(workspace),
        '--run_time', str(budget),
        '--', str(binary), '___FILE___',
    ]
    print(f'[hfuzz seed={seed} budget={budget}s] starting', flush=True)
    t0 = time.time()
    with open(output_dir / 'run.log', 'w') as logf:
        subprocess.run(cmd, stdout=logf, stderr=subprocess.STDOUT)
    elapsed = time.time() - t0

    fuzz_files = sorted(workspace.glob('*.fuzz'))
    crashes_unique = len(fuzz_files)
    ttfc = min((f.stat().st_mtime for f in fuzz_files), default=None)
    ttfc = round(ttfc - t0, 2) if ttfc is not None else ''

    report_file = workspace / 'HONGGFUZZ.REPORT.TXT'
    report = report_file.read_text(errors='replace') if report_file.exists() else ''
    log_text = (output_dir / 'run.log').read_text(errors='replace')
    combined = report + '\n' + log_text

    execs_done = _last_int(r'iterations:(\d+)', combined)
    branch_cvg = _last_float(r'branch_coverage_percent:(\d+)', combined)
    peak_rss = _last_int(r'peak_rss_mb\s*:\s*(\d+)', combined)
    execs_per_sec = (execs_done / elapsed) if execs_done and elapsed > 0 else ''
    new_units = _last_int(r'new_units_added\s*:\s*(\d+)', combined)

    return {
        'time_s': round(elapsed, 1),
        'execs_done': execs_done or '',
        'execs_per_sec': round(execs_per_sec, 1) if execs_per_sec else '',
        'corpus_count': new_units or '',
        'coverage_metric': branch_cvg or '',
        'peak_rss_mb': peak_rss or '',
        'crashes_total': crashes_unique,
        'crashes_unique': crashes_unique,
        'time_to_first_crash_s': ttfc,
    }


def _last_int(pattern, text):
    matches = re.findall(pattern, text)
    return int(matches[-1]) if matches else None


def _last_float(pattern, text):
    matches = re.findall(pattern, text)
    return float(matches[-1]) if matches else None


def _parse_kv_file(path):
    out = {}
    for line in Path(path).read_text(errors='replace').splitlines():
        if ':' in line:
            k, _, v = line.partition(':')
            out[k.strip()] = v.strip()
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--tool', required=True, choices=['lf', 'afl', 'hfuzz'])
    p.add_argument('--budget', required=True, type=int)
    p.add_argument('--seed', required=True, type=int)
    p.add_argument('--target', default='fuzzgoat')
    p.add_argument('--output-root', default='runs/phase2')
    p.add_argument('--csv', default='results/master_all_targets.csv')
    p.add_argument('--project-root', default='.')
    args = p.parse_args()

    project_root = Path(args.project_root).resolve()
    output_dir = Path(args.output_root) / f'{args.budget}s' / f'{args.tool}_seed{args.seed}'
    csv_path = Path(args.csv)
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    runner = {'lf': run_libfuzzer, 'afl': run_aflpp, 'hfuzz': run_honggfuzz}[args.tool]
    metrics = runner(project_root, args.budget, args.seed, output_dir)

    row = {
        'tool': args.tool,
        'target': args.target,
        'budget_s': args.budget,
        'run_id': args.seed,
        **metrics,
    }

    is_new = not csv_path.exists()
    with open(csv_path, 'a', newline='') as f:
        w = csv.DictWriter(f, fieldnames=CSV_HEADER)
        if is_new:
            w.writeheader()
        w.writerow(row)

    print(f'[{args.tool} seed={args.seed} budget={args.budget}s] '
          f'done: {metrics["crashes_total"]} crashes, '
          f'{metrics["execs_done"]} execs in {metrics["time_s"]}s', flush=True)


if __name__ == '__main__':
    main()
