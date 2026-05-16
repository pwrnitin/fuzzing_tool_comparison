#!/usr/bin/env python3
"""One-time migration of old json-c/libpng CSVs to the new schema."""

import csv
from pathlib import Path

OLD_FILES = [
    'results/json_master_60s_all_tools.csv',
    'results/png_master_60s_all_tools.csv',
]
NEW_FILE = 'results/master_all_targets.csv'

NEW_HEADER = [
    'tool', 'target', 'budget_s', 'run_id', 'time_s',
    'execs_done', 'execs_per_sec', 'corpus_count', 'coverage_metric',
    'peak_rss_mb', 'crashes_total', 'crashes_unique',
    'time_to_first_crash_s',
]


def migrate():
    new_path = Path(NEW_FILE)
    new_path.parent.mkdir(parents=True, exist_ok=True)
    rows_out = []
    for old in OLD_FILES:
        p = Path(old)
        if not p.exists():
            print(f'  (skipping {old} — not found)')
            continue
        with open(p, newline='') as f:
            for r in csv.DictReader(f):
                rows_out.append({
                    'tool': r.get('tool', ''),
                    'target': r.get('target', ''),
                    'budget_s': 60,
                    'run_id': r.get('run_id', ''),
                    'time_s': r.get('time_s', ''),
                    'execs_done': r.get('execs_done', ''),
                    'execs_per_sec': r.get('execs_per_sec', ''),
                    'corpus_count': r.get('corpus_count', ''),
                    'coverage_metric': r.get('coverage_metric', ''),
                    'peak_rss_mb': r.get('peak_rss_mb', ''),
                    'crashes_total': 0,
                    'crashes_unique': 0,
                    'time_to_first_crash_s': '',
                })
        print(f'  migrated rows from {old}')

    with open(new_path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=NEW_HEADER)
        w.writeheader()
        w.writerows(rows_out)
    print(f'\nWrote {len(rows_out)} rows to {new_path}')


if __name__ == '__main__':
    migrate()
