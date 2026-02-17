import os
import pandas as pd
import matplotlib.pyplot as plt

CSV = "/home/pawarn/fuzz-thesis/results/tool_comparison_60s_master.csv"
OUTDIR = "/home/pawarn/fuzz-thesis/results/charts"
os.makedirs(OUTDIR, exist_ok=True)

df = pd.read_csv(CSV)

# Means per tool per target (this is what you usually want in thesis charts)
means = (
    df.groupby(["target", "tool"], as_index=False)
      .agg(
          execs_per_sec_mean=("execs_per_sec", "mean"),
          execs_done_mean=("execs_done", "mean"),
          corpus_count_mean=("corpus_count", "mean"),
          coverage_metric_mean=("coverage_metric", "mean"),
          crashes_sum=("crashes", "sum"),
          hangs_sum=("hangs", "sum"),
      )
)

means_path = os.path.join(OUTDIR, "master_summary_means.csv")
means.to_csv(means_path, index=False)
print("Wrote:", means_path)
print(means.to_string(index=False))

def bar_by_target(metric_col, title, ylabel, filename):
    # For each target, create a small bar chart comparing tools using mean metric
    for target in sorted(means["target"].unique()):
        sub = means[means["target"] == target].sort_values("tool")
        labels = sub["tool"].tolist()
        values = sub[metric_col].astype(float).tolist()

        plt.figure()
        plt.bar(labels, values)
        plt.title(f"{target} (60s): {title}")
        plt.ylabel(ylabel)
        plt.tight_layout()

        out = os.path.join(OUTDIR, f"{target}_{filename}")
        plt.savefig(out, dpi=200)
        plt.close()
        print("Wrote:", out)

bar_by_target("execs_per_sec_mean",
              "Mean execution speed (3 seeds)",
              "Executions per second (mean)",
              "master_execs_per_sec_mean.png")

bar_by_target("execs_done_mean",
              "Mean total executions (3 seeds)",
              "Total executions (mean)",
              "master_total_execs_mean.png")

bar_by_target("corpus_count_mean",
              "Mean corpus size (3 seeds)",
              "Corpus entries (mean)",
              "master_corpus_count_mean.png")

bar_by_target("coverage_metric_mean",
              "Mean coverage metric (3 seeds, tool-specific scale)",
              "Coverage metric mean (cov edges / edges_found)",
              "master_coverage_metric_mean.png")

