#!/usr/bin/env python3
"""Phase 4 — generate the four key figures for Chapter 5."""

import csv
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


MASTER_CSV = 'results/master_all_targets.csv'
PHASE3_CSV = 'results/phase3_per_run.csv'
OUT_DIR = Path('results/charts')

TOOL_DISPLAY = {'lf': 'LibFuzzer', 'afl': 'AFL++', 'hfuzz': 'Honggfuzz',
                'libfuzzer': 'LibFuzzer', 'aflplusplus': 'AFL++',
                'honggfuzz': 'Honggfuzz'}
TOOL_COLOR = {'LibFuzzer': '#1f77b4', 'AFL++': '#ff7f0e', 'Honggfuzz': '#2ca02c'}
TOOL_ORDER = ['LibFuzzer', 'AFL++', 'Honggfuzz']


def read_csv(path):
    with open(path, newline='') as f:
        return list(csv.DictReader(f))


def to_float(x, default=None):
    try:
        return float(x)
    except (ValueError, TypeError):
        return default


def normalise_tool(t):
    return TOOL_DISPLAY.get(t.lower(), t)


def fig1_bugs_per_budget(phase3_rows):
    budgets = [60, 300, 1800]
    budget_labels = ['60 s', '5 min', '30 min']
    by = defaultdict(list)
    for r in phase3_rows:
        by[(normalise_tool(r['tool']), int(r['budget_s']))].append(int(r['bugs_found_count']))

    fig, ax = plt.subplots(figsize=(8, 5))
    x = np.arange(len(budgets))
    width = 0.25
    for i, tool in enumerate(TOOL_ORDER):
        means = [np.mean(by.get((tool, b), [0])) for b in budgets]
        stds = [np.std(by.get((tool, b), [0])) for b in budgets]
        ax.bar(x + (i - 1) * width, means, width, yerr=stds, label=tool,
               color=TOOL_COLOR[tool], capsize=4, edgecolor='black', linewidth=0.5)

    ax.axhline(4, color='red', linestyle='--', linewidth=1, alpha=0.6,
               label='4 planted bugs (max)')
    ax.set_xticks(x); ax.set_xticklabels(budget_labels)
    ax.set_xlabel('Time budget')
    ax.set_ylabel('Unique planted bugs found (out of 4)')
    ax.set_title('Bug discovery vs. time budget (mean over 3 seeds)')
    ax.set_ylim(0, 5); ax.set_yticks(range(0, 6))
    ax.legend(loc='lower right'); ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    out = OUT_DIR / 'fig1_bugs_per_budget.png'
    plt.savefig(out, dpi=150); plt.close()
    return out


def fig2_crashes_per_budget(master_rows):
    budgets = [60, 300, 1800]
    budget_labels = ['60 s', '5 min', '30 min']
    by = defaultdict(list)
    for r in master_rows:
        if r['target'] != 'fuzzgoat':
            continue
        c = to_float(r.get('crashes_total'), 0)
        by[(normalise_tool(r['tool']), int(r['budget_s']))].append(c)

    fig, ax = plt.subplots(figsize=(8, 5))
    x = np.arange(len(budgets))
    width = 0.25
    for i, tool in enumerate(TOOL_ORDER):
        means = [np.mean(by.get((tool, b), [0]) or [0]) for b in budgets]
        ax.bar(x + (i - 1) * width, means, width, label=tool,
               color=TOOL_COLOR[tool], edgecolor='black', linewidth=0.5)
        for j, v in enumerate(means):
            if v > 0:
                ax.text(x[j] + (i - 1) * width, v * 1.15, f'{int(v):,}',
                        ha='center', va='bottom', fontsize=8)

    ax.set_yscale('log')
    ax.set_xticks(x); ax.set_xticklabels(budget_labels)
    ax.set_xlabel('Time budget')
    ax.set_ylabel('Crash inputs saved (mean of 3 seeds, log scale)')
    ax.set_title('Raw crash artifact count on Fuzzgoat')
    ax.legend(); ax.grid(axis='y', alpha=0.3, which='both')
    plt.tight_layout()
    out = OUT_DIR / 'fig2_crashes_per_budget.png'
    plt.savefig(out, dpi=150); plt.close()
    return out


def fig3_throughput(master_rows):
    targets = ['json-c', 'libpng', 'fuzzgoat']
    by = defaultdict(list)
    for r in master_rows:
        target = r['target']
        if target not in targets:
            continue
        b = to_float(r.get('budget_s'))
        if b is not None and b != 60:
            continue
        eps = to_float(r.get('execs_per_sec'))
        if eps and eps > 0:
            by[(normalise_tool(r['tool']), target)].append(eps)

    fig, ax = plt.subplots(figsize=(9, 5))
    x = np.arange(len(targets))
    width = 0.25
    for i, tool in enumerate(TOOL_ORDER):
        means = [np.mean(by.get((tool, t), [0]) or [0]) for t in targets]
        ax.bar(x + (i - 1) * width, means, width, label=tool,
               color=TOOL_COLOR[tool], edgecolor='black', linewidth=0.5)
        for j, v in enumerate(means):
            if v > 0:
                ax.text(x[j] + (i - 1) * width, v * 1.05, f'{int(v):,}',
                        ha='center', va='bottom', fontsize=8)

    ax.set_xticks(x); ax.set_xticklabels(targets)
    ax.set_xlabel('Target library')
    ax.set_ylabel('Executions per second (mean, 60 s runs)')
    ax.set_title('Fuzzer throughput across targets')
    ax.legend(); ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    out = OUT_DIR / 'fig3_throughput.png'
    plt.savefig(out, dpi=150); plt.close()
    return out


def fig4_bug_heatmap(phase3_rows):
    runs_per_tool = defaultdict(int)
    found_per_tool_bug = defaultdict(int)
    for r in phase3_rows:
        tool = normalise_tool(r['tool'])
        runs_per_tool[tool] += 1
        for bug in (1, 2, 3, 4):
            if int(r[f'bug_{bug}']) == 1:
                found_per_tool_bug[(tool, bug)] += 1

    matrix = np.zeros((len(TOOL_ORDER), 4))
    annotations = [['' for _ in range(4)] for _ in TOOL_ORDER]
    for i, tool in enumerate(TOOL_ORDER):
        n = runs_per_tool.get(tool, 1)
        for j, bug in enumerate((1, 2, 3, 4)):
            f = found_per_tool_bug.get((tool, bug), 0)
            matrix[i, j] = f / n if n else 0
            annotations[i][j] = f'{f}/{n}'

    fig, ax = plt.subplots(figsize=(8, 4))
    im = ax.imshow(matrix, cmap='RdYlGn', vmin=0, vmax=1, aspect='auto')
    ax.set_xticks(range(4))
    ax.set_xticklabels(['Bug #1\n(UAF)', 'Bug #2\n(heap-overflow)',
                        'Bug #3\n(bad-free)', 'Bug #4\n(NULL deref)'])
    ax.set_yticks(range(len(TOOL_ORDER))); ax.set_yticklabels(TOOL_ORDER)
    for i in range(len(TOOL_ORDER)):
        for j in range(4):
            col = 'white' if matrix[i, j] < 0.4 else 'black'
            ax.text(j, i, annotations[i][j], ha='center', va='center',
                    color=col, fontsize=11, fontweight='bold')
    ax.set_title('Per-planted-bug discovery rate across all 9 runs per tool')
    cbar = plt.colorbar(im, ax=ax, fraction=0.04, pad=0.02)
    cbar.set_label('Fraction of runs')
    plt.tight_layout()
    out = OUT_DIR / 'fig4_bug_heatmap.png'
    plt.savefig(out, dpi=150); plt.close()
    return out


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    master = read_csv(MASTER_CSV)
    phase3 = read_csv(PHASE3_CSV)
    print(f'Loaded {len(master)} master rows, {len(phase3)} phase3 rows')
    outputs = [
        fig1_bugs_per_budget(phase3),
        fig2_crashes_per_budget(master),
        fig3_throughput(master),
        fig4_bug_heatmap(phase3),
    ]
    print('\nGenerated:')
    for p in outputs:
        print(f'  {p}')


if __name__ == '__main__':
    main()
