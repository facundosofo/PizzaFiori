"""
Benchmark visualization script.

Reads the most recent JSON produced by --benchmark-autosave and generates
a two-panel report saved to benchmark_results/latest_report.png.

Usage (from backend/):
    python tests/benchmarks/visualize.py

    # Compare two specific runs
    python tests/benchmarks/visualize.py --compare 0001 0002
"""

import argparse
import json
import sys
from pathlib import Path

# ── Resolve paths ─────────────────────────────────────────────────────────────
_BACKEND = Path(__file__).resolve().parent.parent.parent
_RESULTS_ROOT = _BACKEND / "benchmark_results"


def _find_json(name: str | None) -> Path:
    """Return the JSON path for a run name like '0001', or the latest if None."""
    platform_dirs = sorted(_RESULTS_ROOT.glob("*/"))
    if not platform_dirs:
        sys.exit(f"No benchmark results found in {_RESULTS_ROOT}. Run the benchmarks first.")
    platform_dir = platform_dirs[-1]

    if name:
        # Accept '0001', '0001.json', or full path
        candidate = platform_dir / (name if name.endswith(".json") else f"{name}.json")
        if not candidate.exists():
            sys.exit(f"Result file not found: {candidate}")
        return candidate

    jsons = sorted(platform_dir.glob("*.json"))
    if not jsons:
        sys.exit(f"No JSON files found in {platform_dir}. Run the benchmarks first.")
    return jsons[-1]


def _load(path: Path) -> list[dict]:
    """Return list of benchmark dicts from a pytest-benchmark JSON."""
    data = json.loads(path.read_text(encoding="utf-8"))
    return data["benchmarks"]


# ── Color mapping by module group ─────────────────────────────────────────────
_GROUP_COLORS = {
    "products":  "#4C9BE8",
    "sales":     "#E87C4C",
    "expenses":  "#6EC46E",
    "users":     "#C46EBF",
    "stock":     "#E8C74C",
    "audit":     "#4CC4C4",
}

def _group_color(name: str) -> str:
    for key, color in _GROUP_COLORS.items():
        if key in name:
            return color
    return "#AAAAAA"


def _group_label(name: str) -> str:
    for key in _GROUP_COLORS:
        if key in name:
            return key.capitalize()
    return "Other"


# ── Single-run bar chart ───────────────────────────────────────────────────────

def _plot_single(benchmarks: list[dict], title: str, ax) -> None:
    """Horizontal bar chart sorted by mean, colored by module group."""
    import matplotlib.patches as mpatches

    # Sort by mean ascending
    benchmarks = sorted(benchmarks, key=lambda b: b["stats"]["mean"])

    names = [b["name"].replace("bench_db_", "") for b in benchmarks]
    means_us = [b["stats"]["mean"] * 1_000_000 for b in benchmarks]
    stddevs_us = [b["stats"]["stddev"] * 1_000_000 for b in benchmarks]
    colors = [_group_color(b["name"]) for b in benchmarks]

    y = range(len(names))
    ax.barh(y, means_us, xerr=stddevs_us, color=colors, alpha=0.85,
            error_kw={"elinewidth": 0.8, "capsize": 2, "ecolor": "#555555"})

    ax.set_yticks(list(y))
    ax.set_yticklabels(names, fontsize=7)
    ax.set_xlabel("Mean latency (µs)")
    ax.set_title(title, fontsize=10, fontweight="bold")
    ax.axvline(1000, color="#CCCCCC", linestyle="--", linewidth=0.7, label="1 ms")
    ax.axvline(2000, color="#FFAAAA", linestyle="--", linewidth=0.7, label="2 ms")

    # Legend for groups
    patches = [
        mpatches.Patch(color=c, label=lbl)
        for lbl, c in [(_group_label(b["name"]), _group_color(b["name"]))
                       for b in benchmarks]
        if lbl not in [p.get_label() for p in []]  # deduplicate below
    ]
    seen, unique_patches = set(), []
    for p in patches:
        if p.get_label() not in seen:
            seen.add(p.get_label())
            unique_patches.append(p)

    ax.legend(handles=unique_patches, loc="lower right", fontsize=7,
              title="Module", title_fontsize=7)


# ── Compare bar chart ──────────────────────────────────────────────────────────

def _plot_compare(benchmarks_a: list[dict], benchmarks_b: list[dict],
                  label_a: str, label_b: str, ax) -> None:
    """Side-by-side comparison of two runs, sorted by run-A mean."""
    import numpy as np

    # Build lookup for run B
    b_by_name = {b["name"]: b for b in benchmarks_b}

    # Only compare benchmarks present in both runs
    common = [b for b in benchmarks_a if b["name"] in b_by_name]
    common = sorted(common, key=lambda b: b["stats"]["mean"])

    names = [b["name"].replace("bench_db_", "") for b in common]
    means_a = [b["stats"]["mean"] * 1_000_000 for b in common]
    means_b = [b_by_name[b["name"]]["stats"]["mean"] * 1_000_000 for b in common]

    y = np.arange(len(names))
    bar_h = 0.38

    ax.barh(y - bar_h / 2, means_a, bar_h, label=label_a, color="#4C9BE8", alpha=0.85)
    ax.barh(y + bar_h / 2, means_b, bar_h, label=label_b, color="#E87C4C", alpha=0.85)

    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=7)
    ax.set_xlabel("Mean latency (µs)")
    ax.set_title(f"Comparison: {label_a} vs {label_b}", fontsize=10, fontweight="bold")
    ax.axvline(1000, color="#CCCCCC", linestyle="--", linewidth=0.7)
    ax.legend(fontsize=8)


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    try:
        import matplotlib
        matplotlib.use("Agg")  # headless rendering
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches  # noqa: F401 — imported in subplot fn
    except ImportError:
        sys.exit("matplotlib is required. Install it: pip install matplotlib")

    parser = argparse.ArgumentParser(description="Visualize pytest-benchmark results.")
    parser.add_argument(
        "--compare", nargs=2, metavar=("RUN_A", "RUN_B"),
        help="Compare two runs by name (e.g. --compare 0001 0002)"
    )
    parser.add_argument(
        "--run", metavar="RUN",
        help="Specific run to visualize (e.g. --run 0003). Defaults to latest."
    )
    parser.add_argument(
        "--output", metavar="PATH",
        default=str(_RESULTS_ROOT / "latest_report.png"),
        help="Output PNG path (default: benchmark_results/latest_report.png)"
    )
    args = parser.parse_args()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig_width = 14
    fig_height_per_bench = 0.28

    if args.compare:
        path_a = _find_json(args.compare[0])
        path_b = _find_json(args.compare[1])
        benches_a = _load(path_a)
        benches_b = _load(path_b)

        n = max(len(benches_a), len(benches_b))
        fig, axes = plt.subplots(1, 2, figsize=(fig_width * 2, max(8, n * fig_height_per_bench)))
        fig.suptitle("PizzaFiori — Repository Benchmark Report", fontsize=13, fontweight="bold", y=1.01)

        _plot_single(benches_a, f"Run {args.compare[0]}: {path_a.name}", axes[0])
        _plot_compare(benches_a, benches_b, args.compare[0], args.compare[1], axes[1])
    else:
        path = _find_json(args.run)
        benches = _load(path)

        n = len(benches)
        fig, ax = plt.subplots(figsize=(fig_width, max(8, n * fig_height_per_bench)))
        fig.suptitle("PizzaFiori — Repository Benchmark Report", fontsize=13, fontweight="bold")
        _plot_single(benches, f"{path.name} — {n} benchmarks", ax)

    fig.tight_layout()
    fig.savefig(str(output_path), dpi=150, bbox_inches="tight")
    print(f"Report saved to: {output_path}")


if __name__ == "__main__":
    main()
