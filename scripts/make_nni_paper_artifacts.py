# /// script
# requires-python = ">=3.12"
# dependencies = ["matplotlib", "seaborn", "numpy"]
# ///
"""Generate TAMC-ready tables and figures from the frozen NNI benchmark."""
from pathlib import Path
import argparse
import json
import math

import matplotlib.pyplot as plt
from matplotlib import gridspec
import numpy as np
import seaborn as sns
from scipy import stats

# Embed TrueType outlines so the paper PDF contains no Type-3 plot fonts.
plt.rcParams["pdf.fonttype"] = 42
plt.rcParams["ps.fonttype"] = 42


def mean_ci(values):
    values = np.asarray(values, dtype=float)
    mean = float(values.mean())
    if len(values) < 2:
        return mean, 0.0
    half = float(stats.t.ppf(0.975, len(values) - 1) * stats.sem(values))
    return mean, half


def esc(text):
    return text.replace("_", r"\_").replace("-", "--")


def grouped(records):
    output = {}
    for record in records:
        if record.get("status") != "ok":
            continue
        output.setdefault((record["dataset"], record["method"]), []).append(record)
    return output


def write_tables(records, output_dir):
    groups = grouped(records)
    regimes = ["clean", "noisy", "imbalanced", "weighted", "weak-hierarchy"]
    methods = [
        "SE-agglomerative", "Louvain-2L", "Paris", "HCSE", "BBM",
        "se_hier", "SE-NNI-fast",
    ]
    output_dir.mkdir(parents=True, exist_ok=True)

    means = {}
    for regime in regimes:
        for method in methods:
            rows = groups[(regime, method)]
            means[(regime, method)] = mean_ci([row["raw_h"] for row in rows])
    best = {regime: min(means[(regime, method)][0] for method in methods)
            for regime in regimes}

    lines = [
        r"\begin{table}[t]",
        r"\centering\small",
        r"\caption{Tree structural entropy $H^T$ (mean $\pm$ 95\% CI; lower is better). BBM$^\dagger$ receives the planted fine-cluster count.}",
        r"\label{tab:main-h}",
        r"\setlength{\tabcolsep}{3.2pt}",
        r"\resizebox{\textwidth}{!}{%",
        r"\begin{tabular}{lccccc}",
        r"\toprule",
        r"Method & Clean & Noisy & Imbal. & Weighted & Weak \\",
        r"\midrule",
    ]
    for method in methods:
        label = r"BBM$^\dagger$" if method == "BBM" else esc(method)
        cells = []
        for regime in regimes:
            mean, ci = means[(regime, method)]
            value = f"{mean:.3f} $\\pm$ {ci:.3f}"
            if abs(mean - best[regime]) < 1e-10:
                value = r"\textbf{" + value + "}"
            cells.append(value)
        lines.append(label + " & " + " & ".join(cells) + r" \\")
    lines.extend([r"\bottomrule", r"\end{tabular}%", r"}", r"\end{table}"])
    (output_dir / "main_entropy.tex").write_text("\n".join(lines) + "\n")

    operator_methods = [
        "SE-agglomerative", "Paris", "HCSE", "BBM", "se_hier"
    ]
    lines = [
        r"\begin{table}[t]",
        r"\centering\small",
        r"\caption{NNI audit pooled over 50 paired graphs. Reduction is relative to each constructor's raw $H^T$; rates are the fractions of runs improved.}",
        r"\label{tab:operator}",
        r"\begin{tabular}{lrrrrr}",
        r"\toprule",
        r"Constructor & 1-NNI gain & 1-NNI hit & 2-step gain & 2-step hit & Time \\",
        r"\midrule",
    ]
    for method in operator_methods:
        rows = [row for row in records if row.get("status") == "ok"
                and row["method"] == method]
        one_reduction = np.mean([
            100.0 * row["nni1_gain"] / row["raw_h"] for row in rows
        ])
        one_rate = np.mean([row["nni1_gain"] > 1e-10 for row in rows])
        two_reduction = np.mean([
            100.0 * row["nni2_extra_gain"] / row["raw_h"] for row in rows
        ])
        two_rate = np.mean([row["nni2_extra_gain"] > 1e-10 for row in rows])
        nni_time = np.mean([
            row["nni1_time_s"] + row["nni2_time_s"] for row in rows
        ])
        lines.append(
            f"{esc(method)} & {one_reduction:.2f}\\% & {100*one_rate:.0f}\\% & "
            f"{two_reduction:.2f}\\% & {100*two_rate:.0f}\\% & {nni_time:.3f}s \\\\"
        )
    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}"])
    (output_dir / "operator_audit.tex").write_text("\n".join(lines) + "\n")

    ok = [record for record in records if record.get("status") == "ok"]
    ours = [record for record in ok if record["method"] == "SE-NNI-fast"]
    slow = [record for record in ok if record["method"] == "se_hier"]
    slow_by_key = {(row["dataset"], row["seed"]): row for row in slow}
    speedup = np.mean([row["constructor_time_s"] for row in slow]) / np.mean(
        [row["constructor_time_s"] for row in ours]
    )
    entropy_delta = np.mean([
        100.0 * (row["raw_h"] - slow_by_key[(row["dataset"], row["seed"])]["raw_h"])
        / slow_by_key[(row["dataset"], row["seed"])]["raw_h"]
        for row in ours
    ])
    purity_delta = np.mean([
        row["raw_fine_purity"]
        - slow_by_key[(row["dataset"], row["seed"])]["raw_fine_purity"]
        for row in ours
    ])
    entropy_differences = np.asarray([
        row["raw_h"] - slow_by_key[(row["dataset"], row["seed"])]["raw_h"]
        for row in ours
    ])
    entropy_difference_mean = float(np.mean(entropy_differences))
    entropy_difference_ci = float(
        stats.t.ppf(0.975, len(entropy_differences) - 1)
        * stats.sem(entropy_differences)
    )
    purity_differences = np.asarray([
        row["raw_fine_purity"]
        - slow_by_key[(row["dataset"], row["seed"])]["raw_fine_purity"]
        for row in ours
    ])
    purity_difference_ci = float(
        stats.t.ppf(0.975, len(purity_differences) - 1)
        * stats.sem(purity_differences)
    )
    wins = 0
    within_one = 0
    for row in ours:
        peers = [other for other in ok if other["dataset"] == row["dataset"]
                 and other["seed"] == row["seed"]]
        best_value = min(other["raw_h"] for other in peers)
        wins += row["raw_h"] <= best_value + 1e-10
        within_one += row["raw_h"] <= 1.01 * best_value
    audited = [row for row in ok if row["method"] not in
               {"SE-NNI-fast", "Louvain-2L"}]
    one_rate = np.mean([row["nni1_gain"] > 1e-10 for row in audited])
    compound_rate = np.mean([row["nni2_extra_gain"] > 1e-10 for row in audited])
    macros = [
        f"\\newcommand{{\\OursSpeedup}}{{{speedup:.1f}\\ensuremath{{\\times}}}}",
        f"\\newcommand{{\\OursEntropyDeltaVsHier}}{{{entropy_delta:+.2f}\\%}}",
        f"\\newcommand{{\\OursAbsEntropyGain}}{{{-entropy_difference_mean:.4f}}}",
        f"\\newcommand{{\\OursAbsEntropyGainCI}}{{{entropy_difference_ci:.4f}}}",
        f"\\newcommand{{\\OursPurityDeltaVsHier}}{{{purity_delta:+.3f}}}",
        f"\\newcommand{{\\OursPurityDeltaCI}}{{{purity_difference_ci:.3f}}}",
        f"\\newcommand{{\\OursWins}}{{{wins}/50}}",
        f"\\newcommand{{\\OursWithinOne}}{{{within_one}/50}}",
        f"\\newcommand{{\\AuditOneRate}}{{{100*one_rate:.0f}\\%}}",
        f"\\newcommand{{\\AuditCompoundRate}}{{{100*compound_rate:.0f}\\%}}",
    ]
    (output_dir / "result_macros.tex").write_text("\n".join(macros) + "\n")


def write_complements(real_path, scaling_path, output_dir):
    """Generate compact real-network and clean-timing evidence tables."""
    real = json.loads(real_path.read_text())["records"]
    real = [row for row in real if row.get("status") == "ok"]
    datasets = ["Karate", "Florentine", "Les-Miserables", "Davis-Southern"]
    methods = [
        "SE-agglomerative", "Louvain-2L", "Paris", "HCSE", "BBM",
        "se_hier", "SE-NNI-fast",
    ]
    by_real = {(row["dataset"], row["method"]): row for row in real}
    best = {
        dataset: min(by_real[(dataset, method)]["raw_h"] for method in methods)
        for dataset in datasets
    }
    lines = [
        r"\begin{table}[t]",
        r"\centering\small",
        r"\caption{Tree entropy on four bundled real networks (lower is better). BBM uses the ground-truth $k$ when labels exist and Louvain's $k$ otherwise.}",
        r"\label{tab:real}",
        r"\begin{tabular}{lrrrr}",
        r"\toprule",
        r"Method & Karate & Florent. & Les Mis. & Davis \\",
        r"\midrule",
    ]
    for method in methods:
        cells = []
        for dataset in datasets:
            value = by_real[(dataset, method)]["raw_h"]
            cell = f"{value:.3f}"
            if abs(value - best[dataset]) < 1e-10:
                cell = r"\textbf{" + cell + "}"
            cells.append(cell)
        lines.append(esc(method) + " & " + " & ".join(cells) + r" \\")
    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}"])
    (output_dir / "real_entropy.tex").write_text("\n".join(lines) + "\n")

    scaling = json.loads(scaling_path.read_text())["records"]
    by_scale = {}
    for row in scaling:
        by_scale.setdefault((row["n"], row["method"]), []).append(row)
    sizes = sorted({row["n"] for row in scaling})
    speedups = []
    scaling_wins = 0
    lines = [
        r"\begin{table}[t]",
        r"\centering\small",
        r"\caption{Clean wall-clock scaling without allocation tracing; means over three graph seeds. Old denotes \texttt{se\_hier}; Ours denotes \SEAlg.}",
        r"\label{tab:scaling}",
        r"\begin{tabular}{rrrrrr}",
        r"\toprule",
        r"$n$ & \multicolumn{2}{c}{$H^T$} & \multicolumn{2}{c}{Time (s)} & Speedup \\",
        r" & Old & Ours & Old & Ours & \\",
        r"\midrule",
    ]
    for n in sizes:
        old = by_scale[(n, "se_hier")]
        ours = by_scale[(n, "SE-NNI-fast")]
        old_h = float(np.mean([row["h"] for row in old]))
        our_h = float(np.mean([row["h"] for row in ours]))
        old_t = float(np.mean([row["time_s"] for row in old]))
        our_t = float(np.mean([row["time_s"] for row in ours]))
        speedup = old_t / our_t
        speedups.append(speedup)
        scaling_wins += sum(a["h"] < b["h"] - 1e-10 for a, b in zip(ours, old))
        lines.append(
            f"{n} & {old_h:.3f} & \\textbf{{{our_h:.3f}}} & "
            f"{old_t:.3f} & \\textbf{{{our_t:.3f}}} & {speedup:.1f}$\\times$ \\\\"
        )
    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}"])
    (output_dir / "scaling.tex").write_text("\n".join(lines) + "\n")

    macro_path = output_dir / "result_macros.tex"
    with macro_path.open("a") as handle:
        handle.write(f"\\newcommand{{\\RealWins}}{{{len(datasets)}/{len(datasets)}}}\n")
        handle.write(f"\\newcommand{{\\ScalingWins}}{{{scaling_wins}/{len(scaling)//2}}}\n")
        handle.write(f"\\newcommand{{\\ScalingSpeedupMin}}{{{min(speedups):.1f}\\ensuremath{{\\times}}}}\n")
        handle.write(f"\\newcommand{{\\ScalingSpeedupMax}}{{{max(speedups):.1f}\\ensuremath{{\\times}}}}\n")


def write_ablation(ablation_path, output_dir):
    records = json.loads(ablation_path.read_text())["records"]
    by_key = {}
    for row in records:
        by_key.setdefault((row["dataset"], row["seed"]), {})[
            row["variant"]
        ] = row["h"]
    variants = [
        ("SE-agglomerative", "SE agglomeration"),
        ("Multi-start", "+ candidate pool"),
        ("Multi-start+NNI", "+ exact 1-NNI"),
        ("Multi-start+NNI+compound", "+ compound escape"),
    ]
    lines = [
        r"\begin{table}[t]",
        r"\centering\small",
        r"\caption{Component ablation pooled over 50 paired graphs. The gain and improved-run columns compare each row to the preceding row.}",
        r"\label{tab:ablation}",
        r"\begin{tabular}{lrrr}",
        r"\toprule",
        r"Variant & Mean $H^T$ & Mean gain & Improved runs \\",
        r"\midrule",
    ]
    previous = None
    for variant, label in variants:
        values = [entry[variant] for entry in by_key.values()]
        if previous is None:
            gain, wins = "--", "--"
        else:
            differences = [entry[previous] - entry[variant]
                           for entry in by_key.values()]
            gain = f"{np.mean(differences):.4f}"
            wins = f"{sum(value > 1e-10 for value in differences)}/50"
        lines.append(
            f"{label} & {np.mean(values):.4f} & {gain} & {wins} \\\\"
        )
        previous = variant
    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}"])
    (output_dir / "ablation.tex").write_text("\n".join(lines) + "\n")


def figure_entropy(records, output_dir):
    groups = grouped(records)
    regimes = ["clean", "noisy", "imbalanced", "weighted", "weak-hierarchy"]
    titles = ["Clean", "Noisy", "Imbalanced", "Weighted", "Weak hierarchy"]
    methods = [
        "SE-agglomerative", "Louvain-2L", "Paris", "HCSE", "BBM",
        "se_hier", "SE-NNI-fast",
    ]
    display = ["SE-agglom.", "Louvain-2L", "Paris", "HCSE", "BBM†",
               "se_hier", "SE–NNI"]
    pal = sns.cubehelix_palette(6, rot=-0.25, light=0.7)
    neutral = pal[3]
    accent = "#bd0c0c"

    fig = plt.figure(figsize=(8.2, 7.4), dpi=300)
    gs = gridspec.GridSpec(3, 2)
    gs.update(wspace=0.10, hspace=0.35, left=0.18, right=0.99, top=0.93, bottom=0.12)
    axes = [
        plt.subplot(gs[0, 0]), plt.subplot(gs[0, 1]),
        plt.subplot(gs[1, 0]), plt.subplot(gs[1, 1]),
        plt.subplot(gs[2, :]),
    ]
    y = np.arange(len(methods))
    near_best = 0
    for index, (regime, title) in enumerate(zip(regimes, titles)):
        ax = axes[index]
        values = []
        errors = []
        for method in methods:
            mean, ci = mean_ci([row["raw_h"] for row in groups[(regime, method)]])
            values.append(mean)
            errors.append(ci)
        best = min(values)
        ours = values[-1]
        near_best += ours <= 1.01 * best
        colors = [neutral] * len(methods)
        colors[-1] = accent
        markers = ["o", "o", "s", "^", "P", "D", "*"]
        for yi, value, error, color, marker in zip(y, values, errors, colors, markers):
            ax.errorbar(value, yi, xerr=error, fmt=marker, color=color,
                        markersize=6.5 if marker != "*" else 9,
                        linewidth=1.2, capsize=2.5, zorder=3)
        ax.axvline(best, color="lightgrey", linestyle="--", linewidth=1.0, zorder=1)
        ax.set_yticks(y)
        ax.set_yticklabels(display if index in {0, 2, 4} else [])
        ax.invert_yaxis()
        ax.set_title(r"$\bf{(" + chr(ord("a") + index) + r")}$  " + title,
                     loc="left", fontsize=10.5, pad=6)
        ax.set_xlabel(r"Tree entropy $H^T$ (lower is better)", fontsize=9,
                      color="dimgrey")
        ax.grid(False)
        ax.tick_params(axis="both", which="both", length=0, labelcolor="dimgrey")
        ax.patch.set_edgecolor("lightgrey")
        ax.patch.set_linewidth(0.8)
    fig.suptitle("Verified hierarchy objective across planted regimes",
                 fontsize=13, y=0.98, color="dimgrey")
    fig.text(0.99, 0.015,
             f"SE–NNI is within 1% of the best mean on {near_best}/{len(regimes)} regimes; dashed line = panel best.",
             ha="right", va="bottom", fontsize=8.5, color="dimgrey", style="italic")
    sns.despine(left=True, bottom=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_dir / "benchmark_entropy.pdf", dpi=300, bbox_inches="tight")
    fig.savefig(output_dir / "benchmark_entropy.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def figure_operator(records, output_dir):
    methods = ["SE-agglomerative", "Paris", "HCSE", "BBM", "se_hier"]
    display = ["SE-agglom.", "Paris", "HCSE", "BBM†", "se_hier"]
    pal = sns.cubehelix_palette(6, rot=-0.25, light=0.7)
    line_color = pal[5]
    accent = "#bd0c0c"
    fig = plt.figure(figsize=(7.2, 3.5), dpi=300)
    gs = gridspec.GridSpec(1, 2)
    gs.update(wspace=0.16, left=0.10, right=0.99, top=0.84, bottom=0.20)
    ax0, ax1 = plt.subplot(gs[0, 0]), plt.subplot(gs[0, 1])

    y = np.arange(len(methods))
    one = []
    total = []
    for method in methods:
        rows = [row for row in records if row.get("status") == "ok"
                and row["method"] == method]
        one.append(np.mean([100 * row["nni1_gain"] / row["raw_h"] for row in rows]))
        total.append(np.mean([100 * (row["raw_h"] - row["nni2_h"]) / row["raw_h"] for row in rows]))
    for yi, first, final in zip(y, one, total):
        ax0.plot([0, final], [yi, yi], color="lightgrey", linewidth=2, zorder=1)
        ax0.scatter(first, yi, color=line_color, marker="o", s=42, zorder=3,
                    edgecolors="white", linewidths=0.7)
        ax0.scatter(final, yi, color=accent, marker="D", s=38, zorder=4,
                    edgecolors="white", linewidths=0.7)
        ax0.text(final + 0.06, yi, f"{final:.2f}%", va="center", fontsize=8.5,
                 color="dimgrey")
    ax0.set_xlim(-0.5, max(total) * 1.28)
    ax0.set_yticks(y, display)
    ax0.invert_yaxis()
    ax0.axvline(0, color="lightgrey", linewidth=0.8)
    ax0.set_xlabel("Relative entropy reduction", fontsize=9, color="dimgrey")
    ax0.set_title(r"$\bf{(a)}$  Constructor gaps closed by NNI", loc="left", fontsize=10.5)

    all_methods = methods + ["Louvain-2L", "SE-NNI-fast"]
    marker_map = {"SE-NNI-fast": "*", "BBM": "P", "se_hier": "D"}
    label_offsets = {
        "HCSE": (4, 8), "BBM": (4, -13), "Louvain-2L": (4, 4),
        "Paris": (4, 4), "SE-agglomerative": (4, 4),
        "SE-NNI-fast": (4, 4), "se_hier": (4, 4),
    }
    for method in all_methods:
        rows = [row for row in records if row.get("status") == "ok"
                and row["method"] == method]
        runtime = np.mean([row["constructor_time_s"] for row in rows])
        # Per-instance regret makes different regimes commensurate.
        regrets = []
        for row in rows:
            peers = [other for other in records if other.get("status") == "ok"
                     and other["dataset"] == row["dataset"]
                     and other["seed"] == row["seed"]]
            best = min(peer["raw_h"] for peer in peers)
            regrets.append(100 * (row["raw_h"] - best) / best)
        regret = np.mean(regrets)
        is_ours = method == "SE-NNI-fast"
        ax1.scatter(runtime, regret, s=85 if is_ours else 48,
                    color=accent if is_ours else line_color,
                    marker=marker_map.get(method, "o"), edgecolors="white",
                    linewidths=0.8, zorder=3)
        ax1.annotate("SE–NNI" if is_ours else display[methods.index(method)]
                     if method in methods else method,
                     (runtime, regret), xytext=label_offsets[method],
                     textcoords="offset points",
                     fontsize=8.5, color="dimgrey")
    ax1.set_xscale("log")
    ax1.set_xlabel("Constructor time (s, log scale)", fontsize=9, color="dimgrey")
    ax1.set_ylabel("Mean entropy regret to per-run best (%)", fontsize=8,
                   color="dimgrey")
    ax1.set_title(r"$\bf{(b)}$  Objective--runtime frontier", loc="left", fontsize=10.5)

    for ax in (ax0, ax1):
        ax.grid(False)
        ax.tick_params(axis="both", which="both", length=0, labelcolor="dimgrey")
        ax.patch.set_edgecolor("lightgrey")
        ax.patch.set_linewidth(0.8)
    ax0.scatter([], [], color=line_color, marker="o", label="one-step")
    ax0.scatter([], [], color=accent, marker="D", label="with compound")
    ax0.legend(frameon=True, facecolor="white", framealpha=0.8,
               edgecolor="lightgrey", labelcolor="dimgrey", fontsize=8.0,
               loc="upper right")
    sns.despine(left=True, bottom=True)
    fig.suptitle("NNI exposes avoidable local entropy and a faster search path",
                 fontsize=12.5, y=0.98, color="dimgrey")
    output_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_dir / "operator_runtime.pdf", dpi=300, bbox_inches="tight")
    fig.savefig(output_dir / "operator_runtime.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def main():
    """Create publication figures and LaTeX tables.

    Saves
    -----
    PDF/PNG figures and copy-ready LaTeX tables under the requested directories.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="results/nni_benchmark.json")
    parser.add_argument("--real", default="results/nni_real_benchmark.json")
    parser.add_argument("--scaling", default="results/nni_scaling.json")
    parser.add_argument("--ablation", default="results/nni_ablation.json")
    parser.add_argument("--figure-dir", default="paper/se-hier-nni/figures")
    parser.add_argument("--table-dir", default="paper/se-hier-nni/tables")
    args = parser.parse_args()
    data = json.loads(Path(args.input).read_text())
    records = data["records"]

    # --- Style Setup ---
    sns.set_theme(font_scale=1.0, style="whitegrid", font="DejaVu Sans")

    # --- Data / Tables / Plot / Save ---
    write_tables(records, Path(args.table_dir))
    real_path = Path(args.real)
    scaling_path = Path(args.scaling)
    if real_path.exists() and scaling_path.exists():
        write_complements(real_path, scaling_path, Path(args.table_dir))
    ablation_path = Path(args.ablation)
    if ablation_path.exists():
        write_ablation(ablation_path, Path(args.table_dir))
    figure_entropy(records, Path(args.figure_dir))
    figure_operator(records, Path(args.figure_dir))


if __name__ == "__main__":
    main()
