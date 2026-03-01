import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

ROOT = Path("/home/pawarn/fuzz-thesis/results")
CHARTS = ROOT / "charts"
CHARTS.mkdir(parents=True, exist_ok=True)

FILES = {
    "json-c": ROOT / "json_master_60s_all_tools.csv",
    "libpng": ROOT / "png_master_60s_all_tools.csv",
}

METRICS = {
    "execs_per_sec": "Executions per second",
    "coverage_metric": "Coverage metric",
    "corpus_count": "Corpus metric",
    "peak_rss_mb": "Peak RSS (MB)",
}

def stats_table(df: pd.DataFrame, target: str) -> pd.DataFrame:
    # Ensure numeric columns are numeric
    for col in METRICS.keys():
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    rows = []
    for tool, g in df.groupby("tool"):
        for metric in METRICS.keys():
            if metric not in g.columns:
                continue
            s = g[metric].dropna()
            if s.empty:
                continue
            rows.append({
                "target": target,
                "tool": tool,
                "metric": metric,
                "mean": float(s.mean()),
                "std": float(s.std(ddof=1)) if len(s) > 1 else 0.0,
                "min": float(s.min()),
                "max": float(s.max()),
                "n": int(s.shape[0]),
            })
    return pd.DataFrame(rows)

def errorbar_chart(df: pd.DataFrame, target: str, metric: str, ylabel: str, outname: str):
    d = df.copy()
    d[metric] = pd.to_numeric(d[metric], errors="coerce")
    g = d.groupby("tool")[metric].agg(["mean", "std", "count"]).sort_values("mean", ascending=False)

    plt.figure()
    # bar with yerr
    plt.bar(g.index, g["mean"], yerr=g["std"])
    plt.ylabel(f"{ylabel} (mean ± std, n={int(g['count'].max())})")
    plt.xlabel("tool")
    plt.title(f"{target}: {ylabel}")
    plt.tight_layout()
    plt.savefig(CHARTS / outname, dpi=200)
    plt.close()

def main():
    all_stats = []
    for target, path in FILES.items():
        if not path.exists():
            print(f"Missing: {path}")
            continue

        df = pd.read_csv(path)

        # Save per-target stats table
        st = stats_table(df, target)
        out_csv = ROOT / f"{target}_tool_stats_60s.csv"
        st.to_csv(out_csv, index=False)
        all_stats.append(st)

        # Generate errorbar charts for each metric
        for metric, label in METRICS.items():
            if metric not in df.columns:
                continue
            outname = f"{target}_tools_{metric}_mean_std.png".replace("/", "_")
            errorbar_chart(df, target, metric, label, outname)

        print(f"Wrote stats: {out_csv}")

    if all_stats:
        master = pd.concat(all_stats, ignore_index=True)
        out_master = ROOT / "tool_stats_60s_all_targets.csv"
        master.to_csv(out_master, index=False)
        print(f"Wrote combined stats: {out_master}")

    print(f"Charts saved in: {CHARTS}")

if __name__ == "__main__":
    main()
