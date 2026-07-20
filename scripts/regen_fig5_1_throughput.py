#!/usr/bin/env python3
"""
Regenerate Figure 5.1 — Mean execution throughput per tool across all three targets.
Corrected Fuzzgoat values (30,958 / 1,300 / 815) and canonical tool-name casing
(libFuzzer / honggfuzz per official project spellings).
"""
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Mean execs/sec per (target, tool), 60-second runs, n=3 per condition
targets   = ['json-c', 'libpng', 'fuzzgoat']
libfuzzer = [25588, 18062, 30958]
aflpp     = [ 3458,  2367,  1300]
honggfuzz = [  760,   725,   815]

x = np.arange(len(targets))
width = 0.27

fig, ax = plt.subplots(figsize=(9, 5.5))
b1 = ax.bar(x - width, libfuzzer, width, label='libFuzzer', color='#1f77b4')
b2 = ax.bar(x,         aflpp,     width, label='AFL++',     color='#ff7f0e')
b3 = ax.bar(x + width, honggfuzz, width, label='honggfuzz', color='#2ca02c')

for bars in (b1, b2, b3):
    for bar in bars:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, h,
                f'{int(h):,}', ha='center', va='bottom', fontsize=9)

ax.set_xticks(x)
ax.set_xticklabels(targets)
ax.set_xlabel('Target library')
ax.set_ylabel('Executions per second (mean, 60 s runs)')
ax.set_title('Fuzzer throughput across targets')
ax.legend()
ax.set_ylim(0, max(libfuzzer) * 1.18)
ax.grid(axis='y', linestyle='--', alpha=0.4)

out = Path('results/charts/fig5_1_throughput_across_targets.png')
out.parent.mkdir(parents=True, exist_ok=True)
plt.tight_layout()
plt.savefig(out, dpi=150, bbox_inches='tight')
print(f"Saved: {out}")
