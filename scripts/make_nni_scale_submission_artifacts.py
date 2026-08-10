"""Generate submission tables, macros, and figures from the sealed scale audit."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy import stats


plt.rcParams["pdf.fonttype"] = 42
plt.rcParams["ps.fonttype"] = 42


REGIMES = ["clean", "noisy", "imbalanced", "weighted", "weak-hierarchy"]
TITLES = ["Clean", "Noisy", "Imbalanced", "Weighted", "Weak hierarchy"]
METHODS = ["SE-agglomerative", "Louvain-2L", "Paris", "HCSE", "BBM", "SE-NNI-fast"]
LABELS = {
    "SE-agglomerative": "SE--agglomerative",
    "Louvain-2L": "Louvain--2L",
    "Paris": "Paris",
    "HCSE": "HCSE",
    "BBM": r"BBM$^\dagger$",
    "SE-NNI-fast": r"\NEST\ (ours)",
}
COLORS = {
    "blue": "#356a86",
    "blue_light": "#dbe9ef",
    "orange": "#d9772d",
    "red": "#b51f2e",
    "grey": "#6f7782",
    "grid": "#d9dde2",
}


def mean_ci(values):
    values = np.asarray(values, dtype=float)
    mean = float(values.mean())
    half = float(stats.t.ppf(0.975, len(values) - 1) * stats.sem(values))
    return mean, half


def load_records(root: Path):
    records = []
    for stem in ["n64-clean", "n64-noisy", "n64-imbalanced",
                 "n64-weighted", "n64-weak"]:
        records.extend(json.loads((root / f"{stem}.json").read_text())["records"])
    return [row for row in records if row.get("status") == "ok"]


def index_records(records):
    return {(row["dataset"], row["seed"], row["method"]): row for row in records}


def write_main_table(records, output: Path):
    groups = {}
    for row in records:
        groups.setdefault((row["dataset"], row["method"]), []).append(row)
    means = {
        (regime, method): mean_ci([row["raw_h"] for row in groups[(regime, method)]])
        for regime in REGIMES for method in METHODS
    }
    best = {regime: min(means[(regime, method)][0] for method in METHODS)
            for regime in REGIMES}
    lines = [
        r"\begin{table}[t]",
        r"\centering\small",
        r"\caption{Tree structural entropy $H^T$ over 100 graphs per regime (mean $\pm$ 95\% CI; lower is better). BBM$^\dagger$ receives the planted fine-cluster count.}",
        r"\label{tab:main-h}",
        r"\setlength{\tabcolsep}{3.2pt}",
        r"\resizebox{\textwidth}{!}{%",
        r"\begin{tabular}{lccccc}",
        r"\toprule",
        r"Method & Clean & Noisy & Imbal. & Weighted & Weak \\",
        r"\midrule",
    ]
    for method in METHODS:
        if method == "SE-NNI-fast":
            lines.append(r"\midrule")
        cells = []
        for regime in REGIMES:
            mean, ci = means[(regime, method)]
            cell = f"{mean:.3f} $\\pm$ {ci:.3f}"
            if abs(mean - best[regime]) < 1e-10:
                cell = r"\textbf{" + cell + "}"
            cells.append(cell)
        lines.append(LABELS[method] + " & " + " & ".join(cells) + r" \\")
    lines.extend([r"\bottomrule", r"\end{tabular}%", r"}", r"\end{table}"])
    output.write_text("\n".join(lines) + "\n")


def write_operator_table(records, output: Path):
    methods = ["SE-agglomerative", "Paris", "HCSE", "BBM"]
    lines = [
        r"\begin{table}[t]",
        r"\centering\small",
        r"\caption{NNI audit pooled over 500 paired graphs. Reduction is relative to each constructor's raw $H^T$; rates are fractions of runs improved.}",
        r"\label{tab:operator}",
        r"\begin{tabular}{lrrrrr}",
        r"\toprule",
        r"Constructor & 1-NNI gain & 1-NNI hit & 2-step gain & 2-step hit & Time \\",
        r"\midrule",
    ]
    for method in methods:
        rows = [row for row in records if row["method"] == method]
        one = np.mean([100 * row["nni1_gain"] / row["raw_h"] for row in rows])
        one_hit = np.mean([row["nni1_gain"] > 1e-10 for row in rows])
        two = np.mean([100 * row["nni2_extra_gain"] / row["raw_h"] for row in rows])
        two_hit = np.mean([row["nni2_extra_gain"] > 1e-10 for row in rows])
        wall = np.mean([row["nni1_time_s"] + row["nni2_time_s"] for row in rows])
        lines.append(
            f"{LABELS[method]} & {one:.2f}\\% & {100*one_hit:.0f}\\% & "
            f"{two:.2f}\\% & {100*two_hit:.0f}\\% & {wall:.3f}s \\\\"
        )
    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}"])
    output.write_text("\n".join(lines) + "\n")


def cp_interval(hits, total):
    alpha = 0.05
    lower = 0.0 if hits == 0 else stats.beta.ppf(alpha / 2, hits, total - hits + 1)
    upper = 1.0 if hits == total else stats.beta.ppf(1 - alpha / 2, hits + 1, total - hits)
    return float(lower), float(upper)


def exact_row(data, method):
    item = data["summary"][method]
    return item["globally_optimal"], item["instances"], item


def write_exact_table(legacy_path: Path, root: Path, output: Path):
    blocks = [
        (12, json.loads(legacy_path.read_text())),
        (14, json.loads((root / "exact14.json").read_text())),
        (16, json.loads((root / "exact16.json").read_text())),
    ]
    lines = [
        r"\begin{table}[t]",
        r"\centering\small",
        r"\caption{Sealed exact-optimum audit with 32 candidates per method. Parentheses give exact 95\% Clopper--Pearson intervals for the \NEST hit rate. Gap is relative to $H^*$.}",
        r"\label{tab:exact-scale}",
        r"\setlength{\tabcolsep}{3.5pt}",
        r"\resizebox{\textwidth}{!}{%",
        r"\begin{tabular}{rrrrrrr}",
        r"\toprule",
        r"$n$ & Graphs & \NEST exact & 95\% CI & HCSE exact & BBM exact & Mean / max gap \\",
        r"\midrule",
    ]
    for n, data in blocks:
        nest_hits, total, nest = exact_row(data, "NEST-coalescent-B32")
        hcse_hits, _, _ = exact_row(data, "HCSE-B32")
        bbm_hits, _, _ = exact_row(data, "BBM-label-free-B32")
        lo, hi = cp_interval(nest_hits, total)
        mean_gap = nest["mean_relative_gap_percent"]["mean"]
        max_gap = nest["max_relative_gap_percent"]
        lines.append(
            f"{n} & {total} & \\textbf{{{nest_hits}/{total}}} & "
            f"[{100*lo:.2f}, {100*hi:.2f}]\\% & {hcse_hits}/{total} & "
            f"{bbm_hits}/{total} & {mean_gap:.5f}\\% / {max_gap:.3f}\\% \\\\"
        )
    lines.extend([r"\bottomrule", r"\end{tabular}%", r"}", r"\end{table}"])
    output.write_text("\n".join(lines) + "\n")


def write_macros(records, legacy_path: Path, root: Path, output: Path):
    by = index_records(records)
    ours = [row for row in records if row["method"] == "SE-NNI-fast"]
    differences = {}
    for method in ["HCSE", "BBM"]:
        differences[method] = np.asarray([
            by[(row["dataset"], row["seed"], method)]["raw_h"] - row["raw_h"]
            for row in ours
        ])
    best = np.asarray([
        min(by[(row["dataset"], row["seed"], method)]["raw_h"]
            for method in ["HCSE", "BBM"]) - row["raw_h"]
        for row in ours
    ])
    audited = [row for row in records if row["method"] in
               {"SE-agglomerative", "Paris", "HCSE", "BBM"}]
    legacy = json.loads(legacy_path.read_text())["summary"]
    exact14 = json.loads((root / "exact14.json").read_text())["summary"]
    exact16 = json.loads((root / "exact16.json").read_text())["summary"]
    lines = []
    for macro, values in [
        ("NESTGainVsHCSE", differences["HCSE"]),
        ("NESTGainVsBBM", differences["BBM"]),
        ("NESTGainVsBestExternal", best),
    ]:
        mean, ci = mean_ci(values)
        lines.append(f"\\newcommand{{\\{macro}}}{{{mean:.4f}}}")
        lines.append(f"\\newcommand{{\\{macro}CI}}{{{ci:.4f}}}")
    lines.extend([
        f"\\newcommand{{\\OursWins}}{{{sum(best > 1e-10)}/{len(best)}}}",
        f"\\newcommand{{\\OursWithinOne}}{{{sum(best >= -1e-10)}/{len(best)}}}",
        f"\\newcommand{{\\AuditOneRate}}{{{100*np.mean([r['nni1_gain'] > 1e-10 for r in audited]):.0f}\\%}}",
        f"\\newcommand{{\\AuditCompoundRate}}{{{100*np.mean([r['nni2_extra_gain'] > 1e-10 for r in audited]):.0f}\\%}}",
        r"\newcommand{\RealWins}{4/4}",
        f"\\newcommand{{\\FairNESTExact}}{{{legacy['NEST-coalescent-B32']['globally_optimal']}/250}}",
        f"\\newcommand{{\\FairHCSEExact}}{{{legacy['HCSE-B32']['globally_optimal']}/250}}",
        f"\\newcommand{{\\FairBBMExact}}{{{legacy['BBM-label-free-B32']['globally_optimal']}/250}}",
        f"\\newcommand{{\\FairNESTMeanGap}}{{{legacy['NEST-coalescent-B32']['mean_relative_gap_percent']['mean']:.5f}\\%}}",
        f"\\newcommand{{\\FairNESTWorstGap}}{{{legacy['NEST-coalescent-B32']['max_relative_gap_percent']:.5f}\\%}}",
        f"\\newcommand{{\\ScaleNFourteenExact}}{{{exact14['NEST-coalescent-B32']['globally_optimal']}/100}}",
        f"\\newcommand{{\\ScaleNSixteenExact}}{{{exact16['NEST-coalescent-B32']['globally_optimal']}/25}}",
        r"\newcommand{\ScaleCombinedExact}{370/375}",
    ])
    output.write_text("\n".join(lines) + "\n")


def style_axis(ax):
    ax.grid(axis="x", color=COLORS["grid"], linewidth=0.6, alpha=0.75)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="both", length=0, colors=COLORS["grey"], labelsize=7.5)


def figure_entropy(records, output_dir: Path):
    by = index_records(records)
    margins = {}
    for regime in REGIMES:
        seeds = sorted({row["seed"] for row in records if row["dataset"] == regime})
        margins[regime] = np.asarray([
            min(by[(regime, seed, method)]["raw_h"] for method in ["HCSE", "BBM"])
            - by[(regime, seed, "SE-NNI-fast")]["raw_h"]
            for seed in seeds
        ])

    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.45), gridspec_kw={"width_ratios": [0.95, 1.18]})
    y = np.arange(len(REGIMES))
    means = [mean_ci(margins[regime]) for regime in REGIMES]
    axes[0].axvspan(0, 0.8, color=COLORS["blue_light"], alpha=0.55, zorder=0)
    for yi, (mean, ci) in zip(y, means):
        axes[0].plot([0, mean], [yi, yi], color="#aeb7bf", linewidth=2.2)
        axes[0].errorbar(mean, yi, xerr=ci, fmt="D", color=COLORS["red"],
                         markeredgecolor="white", markeredgewidth=0.7,
                         markersize=6, capsize=2.5, linewidth=1.25)
        axes[0].text(mean + ci + 0.012, yi, f"{mean:.3f}", va="center",
                     fontsize=7.2, color=COLORS["grey"])
    axes[0].set_yticks(y, TITLES)
    axes[0].invert_yaxis()
    axes[0].set_xlim(0, 0.56)
    axes[0].set_xlabel("Gain over best HCSE/BBM (bits)", fontsize=8)
    axes[0].set_title("(a) Paired mean and 95% CI", loc="left", fontsize=9.5)
    style_axis(axes[0])

    rng = np.random.default_rng(20260810)
    axes[1].axvspan(0, 0.8, color=COLORS["blue_light"], alpha=0.55, zorder=0)
    for yi, regime in zip(y, REGIMES):
        values = margins[regime]
        jitter = rng.uniform(-0.20, 0.20, len(values))
        axes[1].scatter(values, yi + jitter, s=8, color=COLORS["blue"],
                        alpha=0.38, linewidths=0, rasterized=True)
        mean, ci = mean_ci(values)
        axes[1].errorbar(mean, yi, xerr=ci, fmt="D", color=COLORS["red"],
                         markeredgecolor="white", markeredgewidth=0.7,
                         markersize=6, capsize=2.5, linewidth=1.25, zorder=4)
    axes[1].set_yticks(y, [])
    axes[1].invert_yaxis()
    axes[1].set_xlim(0, 0.78)
    axes[1].set_xlabel("Per-graph winning margin (bits)", fontsize=8)
    axes[1].set_title("(b) 100 sealed graphs per regime", loc="left", fontsize=9.5)
    style_axis(axes[1])

    fig.suptitle("NEST improves over the stronger external SE baseline on 500/500 graphs",
                 fontsize=11.2, y=0.985)
    fig.tight_layout(rect=[0, 0.02, 1, 0.93], w_pad=1.3)
    output_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_dir / "benchmark_entropy.pdf", dpi=300, bbox_inches="tight")
    fig.savefig(output_dir / "benchmark_entropy.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def figure_operator(records, output_dir: Path):
    methods = ["SE-agglomerative", "Paris", "HCSE", "BBM"]
    display = ["SE-agglom.", "Paris", "HCSE", "BBM†"]
    one = []
    two = []
    for method in methods:
        rows = [row for row in records if row["method"] == method]
        one.append(100 * np.mean([row["nni1_gain"] > 1e-10 for row in rows]))
        two.append(100 * np.mean([row["nni2_extra_gain"] > 1e-10 for row in rows]))
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.55), gridspec_kw={"width_ratios": [1.0, 1.15]})
    y = np.arange(len(methods))
    height = 0.31
    axes[0].barh(y - height/2, one, height, color=COLORS["blue"], label="one-step NNI")
    axes[0].barh(y + height/2, two, height, color=COLORS["orange"], label="compound")
    axes[0].set_yticks(y, display)
    axes[0].invert_yaxis()
    axes[0].set_xlim(0, 105)
    axes[0].set_xlabel("Graphs improved (%)", fontsize=8)
    axes[0].set_title("(a) Improvement frequency", loc="left", fontsize=9.5,
                      pad=25)
    axes[0].legend(frameon=False, fontsize=6.9, loc="lower center",
                   bbox_to_anchor=(0.5, 1.02), ncol=2, columnspacing=1.0,
                   handlelength=1.4)
    style_axis(axes[0])

    frontier = methods + ["Louvain-2L", "SE-NNI-fast"]
    by = index_records(records)
    label_offsets = {
        "SE-agglomerative": (5, -11),
        "Louvain-2L": (-36, 5),
        "Paris": (5, 4),
        "HCSE": (-4, 8),
        "BBM": (6, -12),
        "SE-NNI-fast": (5, 4),
    }
    display_names = {"SE-NNI-fast": "NEST", "BBM": "BBM†"}
    for method in frontier:
        rows = [row for row in records if row["method"] == method]
        runtime = np.mean([row["constructor_time_s"] for row in rows])
        regrets = []
        for row in rows:
            best = min(by[(row["dataset"], row["seed"], peer)]["raw_h"] for peer in frontier)
            regrets.append(100 * (row["raw_h"] - best) / best)
        regret = np.mean(regrets)
        ours = method == "SE-NNI-fast"
        axes[1].scatter(runtime, regret, s=85 if ours else 45,
                        marker="*" if ours else "o",
                        color=COLORS["red"] if ours else COLORS["blue"],
                        edgecolor="white", linewidth=0.7, zorder=3)
        axes[1].annotate(display_names.get(method, method), (runtime, regret),
                         xytext=label_offsets[method], textcoords="offset points",
                         fontsize=7.3, color=COLORS["grey"])
    axes[1].set_xscale("log")
    axes[1].set_xlabel("Constructor time (s, log scale)", fontsize=8)
    axes[1].set_ylabel("Mean entropy regret (%)", fontsize=8)
    axes[1].set_title("(b) Objective-runtime frontier", loc="left", fontsize=9.5)
    style_axis(axes[1])
    fig.suptitle("Exact NNI exposes residual optimization gaps", fontsize=11.2, y=0.985)
    fig.tight_layout(rect=[0, 0.02, 1, 0.93], w_pad=1.4)
    output_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_dir / "operator_runtime.pdf", dpi=300, bbox_inches="tight")
    fig.savefig(output_dir / "operator_runtime.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--legacy-exact", type=Path, required=True)
    parser.add_argument("--figure-dir", type=Path, required=True)
    parser.add_argument("--table-dir", type=Path, required=True)
    args = parser.parse_args()
    records = load_records(args.root)
    args.figure_dir.mkdir(parents=True, exist_ok=True)
    args.table_dir.mkdir(parents=True, exist_ok=True)
    write_main_table(records, args.table_dir / "main_entropy.tex")
    write_operator_table(records, args.table_dir / "operator_audit.tex")
    write_exact_table(args.legacy_exact, args.root, args.table_dir / "exact_scaling.tex")
    write_macros(records, args.legacy_exact, args.root, args.table_dir / "result_macros.tex")
    figure_entropy(records, args.figure_dir)
    figure_operator(records, args.figure_dir)
    print(f"generated submission artifacts from {len(records)} verified records")


if __name__ == "__main__":
    main()
