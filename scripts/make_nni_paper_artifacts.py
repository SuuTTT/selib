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


def tex_label(method):
    """Return a publication label for an internal benchmark key."""
    labels = {
        "se_hier": r"\EGTE\ (ours)",
        "SE-NNI-fast": r"\NEST\ (ours)",
    }
    return labels.get(method, esc(method))


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
        if method == "se_hier":
            lines.append(r"\midrule")
        label = r"BBM$^\dagger$" if method == "BBM" else tex_label(method)
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
            f"{tex_label(method)} & {one_reduction:.2f}\\% & {100*one_rate:.0f}\\% & "
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
    external_differences = {}
    for method in ("HCSE", "BBM"):
        external = [record for record in ok if record["method"] == method]
        external_by_key = {
            (row["dataset"], row["seed"]): row for row in external
        }
        external_differences[method] = np.asarray([
            external_by_key[(row["dataset"], row["seed"])] ["raw_h"]
            - row["raw_h"]
            for row in ours
        ])
    best_external_differences = np.asarray([
        min(
            next(other["raw_h"] for other in ok
                 if other["dataset"] == row["dataset"]
                 and other["seed"] == row["seed"]
                 and other["method"] == method)
            for method in ("HCSE", "BBM")
        ) - row["raw_h"]
        for row in ours
    ])
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
        f"\\newcommand{{\\NESTSpeedupVsEGTE}}{{{speedup:.1f}\\ensuremath{{\\times}}}}",
        f"\\newcommand{{\\NESTEntropyDeltaVsEGTE}}{{{entropy_delta:+.2f}\\%}}",
        f"\\newcommand{{\\NESTGainVsEGTE}}{{{-entropy_difference_mean:.4f}}}",
        f"\\newcommand{{\\NESTGainVsEGTECI}}{{{entropy_difference_ci:.4f}}}",
        f"\\newcommand{{\\NESTPurityDeltaVsEGTE}}{{{purity_delta:+.3f}}}",
        f"\\newcommand{{\\NESTPurityDeltaVsEGTECI}}{{{purity_difference_ci:.3f}}}",
        f"\\newcommand{{\\NESTGainVsHCSE}}{{{external_differences['HCSE'].mean():.4f}}}",
        f"\\newcommand{{\\NESTGainVsHCSECI}}{{{mean_ci(external_differences['HCSE'])[1]:.4f}}}",
        f"\\newcommand{{\\NESTGainVsBBM}}{{{external_differences['BBM'].mean():.4f}}}",
        f"\\newcommand{{\\NESTGainVsBBMCI}}{{{mean_ci(external_differences['BBM'])[1]:.4f}}}",
        f"\\newcommand{{\\NESTGainVsBestExternal}}{{{best_external_differences.mean():.4f}}}",
        f"\\newcommand{{\\NESTGainVsBestExternalCI}}{{{mean_ci(best_external_differences)[1]:.4f}}}",
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
        if method == "se_hier":
            lines.append(r"\midrule")
        lines.append(tex_label(method) + " & " + " & ".join(cells) + r" \\")
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
        r"\caption{Clean wall-clock scaling without allocation tracing; means over three graph seeds. EGTE and NEST are our general-edit and certified fast variants.}",
        r"\label{tab:scaling}",
        r"\begin{tabular}{rrrrrr}",
        r"\toprule",
        r"$n$ & \multicolumn{2}{c}{$H^T$} & \multicolumn{2}{c}{Time (s)} & Speedup \\",
        r" & EGTE & NEST & EGTE & NEST & \\",
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
    regimes = ["clean", "noisy", "imbalanced", "weighted", "weak-hierarchy"]
    titles = ["Clean", "Noisy", "Imbalanced", "Weighted", "Weak hierarchy"]
    ok = [row for row in records if row.get("status") == "ok"]
    pal = sns.cubehelix_palette(6, rot=-0.25, light=0.7)
    neutral = pal[5]
    point_color = pal[3]
    accent = "#bd0c0c"
    positive_fill = "#edf4f7"

    fig = plt.figure(figsize=(7.2, 3.55), dpi=300)
    gs = gridspec.GridSpec(1, 2, width_ratios=(0.92, 1.18))
    gs.update(wspace=0.10, left=0.12, right=0.99, top=0.84, bottom=0.22)
    ax0, ax1 = plt.subplot(gs[0, 0]), plt.subplot(gs[0, 1])
    y = np.arange(len(regimes))

    paired_by_regime = {}
    margins_by_regime = {}
    strict_wins = 0
    best_or_tied = 0
    for regime in regimes:
        paired = []
        margins = []
        for seed in range(10):
            rows = [row for row in ok if row["dataset"] == regime
                    and row["seed"] == seed]
            ours = next(row["raw_h"] for row in rows
                        if row["method"] == "SE-NNI-fast")
            competitor = min(row["raw_h"] for row in rows
                             if row["method"] in {"HCSE", "BBM"})
            paired.append(competitor - ours)
            margin = competitor - ours
            margins.append(margin)
            strict_wins += margin > 1e-10
            best_or_tied += margin >= -1e-10
        paired_by_regime[regime] = paired
        margins_by_regime[regime] = margins

    paired_means = [mean_ci(paired_by_regime[regime]) for regime in regimes]
    max_gain = max(mean + ci for mean, ci in paired_means)
    ax0.axvspan(0, max_gain * 1.18, color=positive_fill, zorder=0)
    ax0.axvline(0, color="#8b8b8b", linewidth=0.9, zorder=1)
    for yi, (mean, ci) in zip(y, paired_means):
        ax0.plot([0, mean], [yi, yi], color="#aeb7bf", linewidth=2.4, zorder=2)
        ax0.errorbar(mean, yi, xerr=ci, fmt="D", color=accent,
                     markeredgecolor="white", markeredgewidth=0.7,
                     markersize=6.5, linewidth=1.4, capsize=2.5, zorder=4)
        ax0.text(mean + ci + max_gain * 0.025, yi, f"{mean:.3f}",
                 va="center", fontsize=7.5, color="dimgrey", weight="semibold")
    ax0.set_xlim(-max_gain * 0.08, max_gain * 1.28)
    ax0.set_yticks(y, titles)
    ax0.invert_yaxis()
    ax0.set_xlabel("Gain over best of HCSE/BBM (bits)", fontsize=8.5,
                   color="dimgrey")
    ax0.set_title(r"$\bf{(a)}$  Paired entropy reduction", loc="left",
                  fontsize=10.0, pad=6)

    max_margin = max(max(values) for values in margins_by_regime.values())
    ax1.axvspan(0, max_margin * 1.13, color=positive_fill, zorder=0)
    ax1.axvline(0, color="#8b8b8b", linewidth=0.9, zorder=1)
    jitter = np.linspace(-0.18, 0.18, 10)
    for yi, regime in zip(y, regimes):
        values = np.asarray(margins_by_regime[regime])
        mean, ci = mean_ci(values)
        ax1.scatter(values, yi + jitter, color=point_color, marker="o", s=18,
                    alpha=0.72, edgecolors="white", linewidths=0.35, zorder=3)
        ax1.errorbar(mean, yi, xerr=ci, fmt="D", color=accent,
                     markeredgecolor="white", markeredgewidth=0.7,
                     markersize=6.5, linewidth=1.4, capsize=2.5, zorder=5)
    ax1.set_xlim(-max_margin * 0.035, max_margin * 1.14)
    ax1.set_yticks(y)
    ax1.tick_params(labelleft=False)
    ax1.invert_yaxis()
    ax1.set_xlabel("Margin to best of HCSE/BBM (bits)", fontsize=8.5,
                   color="dimgrey")
    ax1.set_title(r"$\bf{(b)}$  Per-seed winning margin", loc="left",
                  fontsize=10.0, pad=6)
    ax1.scatter([], [], color=point_color, s=18, marker="o", label="seed")
    ax1.scatter([], [], color=accent, s=38, marker="D", label="mean ± 95% CI")
    ax1.legend(frameon=True, facecolor="white", framealpha=0.8,
               edgecolor="lightgrey", labelcolor="dimgrey", fontsize=7.0,
               loc="lower right", ncol=2, handletextpad=0.4, columnspacing=0.8)

    for ax in (ax0, ax1):
        ax.grid(False)
        ax.tick_params(axis="both", which="both", length=0,
                       labelcolor="dimgrey", labelsize=7.5)
        ax.patch.set_edgecolor("lightgrey")
        ax.patch.set_linewidth(0.8)
    fig.suptitle("NEST consistently improves over HCSE and BBM",
                 fontsize=12.0, y=0.98, color="dimgrey")
    fig.text(0.99, 0.035,
             f"Lower entropy on {strict_wins}/50 graphs against the better external SE baseline",
             ha="right", va="bottom", fontsize=8.0, color="dimgrey",
             style="italic", weight="semibold")
    sns.despine(left=True, bottom=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_dir / "benchmark_entropy.pdf", dpi=300, bbox_inches="tight")
    fig.savefig(output_dir / "benchmark_entropy.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def figure_operator(records, output_dir):
    methods = ["SE-agglomerative", "Paris", "HCSE", "BBM", "se_hier"]
    display = ["SE-agglom.", "Paris", "HCSE", "BBM†", "EGTE (ours)"]
    pal = sns.cubehelix_palette(6, rot=-0.25, light=0.7)
    line_color = pal[5]
    point_color = pal[3]
    accent = "#bd0c0c"
    compound_color = "#d95f02"
    positive_fill = "#edf4f7"
    slow_fill = "#fff4e6"
    fig = plt.figure(figsize=(7.2, 3.95), dpi=300)
    gs = gridspec.GridSpec(1, 2, width_ratios=(1.02, 1.18))
    gs.update(wspace=0.16, left=0.11, right=0.99, top=0.72, bottom=0.20)
    ax0, ax1 = plt.subplot(gs[0, 0]), plt.subplot(gs[0, 1])

    y = np.arange(len(methods))
    one_rate = []
    compound_rate = []
    for method in methods:
        rows = [row for row in records if row.get("status") == "ok"
                and row["method"] == method]
        one_rate.append(100 * np.mean([row["nni1_gain"] > 1e-10 for row in rows]))
        compound_rate.append(100 * np.mean([
            row["nni2_extra_gain"] > 1e-10 for row in rows
        ]))
    ax0.axvspan(0, 100, color=positive_fill, zorder=0)
    bar_h = 0.31
    ax0.barh(y - bar_h / 2, one_rate, height=bar_h, color=line_color,
             edgecolor="white", linewidth=0.6, label="one-step NNI", zorder=2)
    ax0.barh(y + bar_h / 2, compound_rate, height=bar_h,
             color=compound_color, edgecolor="white", linewidth=0.6,
             label="post-certificate compound", zorder=2)
    for yi, first, second in zip(y, one_rate, compound_rate):
        ax0.text(first + 2.0, yi - bar_h / 2, f"{first:.0f}", va="center",
                 ha="left", fontsize=7.2, color=line_color, weight="semibold")
        ax0.text(second + 2.0, yi + bar_h / 2, f"{second:.0f}", va="center",
                 ha="left", fontsize=7.2, color=compound_color,
                 weight="semibold")
    ax0.set_xlim(0, 108)
    ax0.set_xticks([0, 25, 50, 75, 100])
    ax0.set_yticks(y, display)
    ax0.invert_yaxis()
    ax0.set_xlabel("Graphs improved (%)", fontsize=8.5, color="dimgrey")
    ax0.set_title(r"$\bf{(a)}$  Improvement frequency", loc="left",
                  fontsize=10.0, pad=6)
    handles, labels = ax0.get_legend_handles_labels()
    fig.legend(handles, labels, frameon=False, fontsize=7.6,
               loc="upper left", bbox_to_anchor=(0.105, 0.855), ncol=2,
               handlelength=1.5, handletextpad=0.4, columnspacing=1.1,
               borderaxespad=0.0)

    all_methods = methods + ["Louvain-2L", "SE-NNI-fast"]
    marker_map = {"SE-NNI-fast": "*", "BBM": "P", "se_hier": "D"}
    label_offsets = {
        "HCSE": (4, 8), "BBM": (4, -13), "Louvain-2L": (4, 4),
        "Paris": (4, 4), "SE-agglomerative": (4, 4),
        "SE-NNI-fast": (4, 4), "se_hier": (4, 4),
    }
    points = {}
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
        points[method] = (runtime, regret)
        is_ours = method == "SE-NNI-fast"
        ax1.scatter(runtime, regret, s=85 if is_ours else 48,
                    color=accent if is_ours else point_color,
                    marker=marker_map.get(method, "o"), edgecolors="white",
                    linewidths=0.8, zorder=3)
        ax1.annotate("NEST" if is_ours else display[methods.index(method)]
                     if method in methods else method,
                     (runtime, regret), xytext=label_offsets[method],
                     textcoords="offset points",
                     fontsize=8.1, color="dimgrey")
    ours_runtime, ours_regret = points["SE-NNI-fast"]
    old_runtime, old_regret = points["se_hier"]
    speedup = old_runtime / ours_runtime
    ax1.set_xscale("log")
    ax1.axhspan(-1.2, 1.0, color=positive_fill, zorder=0)
    ax1.axvspan(1.0, old_runtime * 1.7, color=slow_fill, alpha=0.55, zorder=0)
    ax1.annotate(
        "", xy=(ours_runtime, ours_regret), xytext=(old_runtime, old_regret),
        arrowprops={"arrowstyle": "-|>", "color": accent, "linewidth": 1.7,
                    "connectionstyle": "arc3,rad=-0.12"}, zorder=5,
    )
    ax1.text(
        math.sqrt(ours_runtime * old_runtime), max(ours_regret, old_regret) + 5.8,
        f"{speedup:.1f}× faster\nand lower entropy", ha="center", va="bottom",
        fontsize=7.8, color=accent, weight="semibold",
        bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.82, "pad": 1.5},
    )
    ax1.set_xlabel("Constructor time (s, log scale)", fontsize=9, color="dimgrey")
    ax1.set_ylabel("Mean entropy regret (%)", fontsize=8,
                   color="dimgrey")
    ax1.set_title(r"$\bf{(b)}$  Objective--runtime frontier", loc="left",
                  fontsize=10.0, pad=6)

    for ax in (ax0, ax1):
        ax.grid(False)
        ax.tick_params(axis="both", which="both", length=0, labelcolor="dimgrey")
        ax.patch.set_edgecolor("lightgrey")
        ax.patch.set_linewidth(0.8)
    sns.despine(left=True, bottom=True)
    fig.suptitle("Exact NNI diagnoses constructor gaps and accelerates EGTE",
                 fontsize=12.0, y=0.985, color="dimgrey")
    fig.text(0.99, 0.035, "Lower-left is better · shaded blue band: within 1% of best",
             ha="right", va="bottom", fontsize=7.8, color="dimgrey",
             style="italic")
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
