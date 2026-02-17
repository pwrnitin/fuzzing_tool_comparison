import os
import pandas as pd
import matplotlib.pyplot as plt

CSV = "/home/pawarn/fuzz-thesis/results/png_tool_comparison_60s.csv"
OUTDIR = "/home/pawarn/fuzz-thesis/results/charts"
os.makedirs(OUTDIR, exist_ok=True)

df = pd.read_csv(CSV)

def save_bar(df_in, ycol, title, ylabel, filename):
    df_in = df_in.sort_values(["tool", "seed"])
    labels = [f'{r.tool}-s{int(r.seed)}' for r in df_in.itertuples()]
    values = df_in[ycol].astype(float).tolist()

    plt.figure()
    plt.bar(labels, values)
    plt.title(title)
    plt.ylabel(ylabel)
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    outpath = os.path.join(OUTDIR, filename)
    plt.savefig(outpath, dpi=200)
    plt.close()
    print("Wrote:", outpath)

save_bar(df, "execs_per_sec",
         "libpng (60s): Execution speed by tool and seed",
         "Executions per second",
         "png_execs_per_sec.png")

save_bar(df, "execs_done",
         "libpng (60s): Total executions by tool and seed",
         "Total executions",
         "png_total_execs.png")

save_bar(df, "corpus_count",
         "libpng (60s): Corpus size by tool and seed",
         "Corpus entries",
         "png_corpus_count.png")

save_bar(df, "coverage_metric",
         "libpng (60s): Coverage metric by tool and seed (tool-specific scale)",
         "Coverage metric (cov edges / edges_found)",
         "png_coverage_metric.png")

summary = df.groupby("tool").agg(
    execs_per_sec_mean=("execs_per_sec", "mean"),
    execs_done_mean=("execs_done", "mean"),
    corpus_count_mean=("corpus_count", "mean"),
    coverage_metric_mean=("coverage_metric", "mean"),
).reset_index()

summary_path = os.path.join(OUTDIR, "png_summary_means.csv")
summary.to_csv(summary_path, index=False)
print("Wrote:", summary_path)
print(summary.to_string(index=False))

