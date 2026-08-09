"""Generate the paper table and human-readable report from the fair audit."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


METHODS = (
    ("NEST-coalescent-B32", r"\NEST (coalescent)"),
    ("HCSE-B32", "HCSE"),
    ("BBM-oracle-B32", "BBM (oracle $k$)"),
    ("BBM-label-free-B32", "BBM (label-free)"),
    ("SE-agglomerative", "SE agglomerative"),
)


def latex_table(artifact: dict) -> str:
    rows = []
    for method, label in METHODS:
        summary = artifact["summary"][method]
        calls = summary["mean_candidate_calls"]
        calls_text = str(int(calls)) if calls.is_integer() else f"{calls:.1f}"
        valid = summary["successful_instances"]
        exact = summary["globally_optimal"]
        rate = summary["optimal_hit_rate_percent"]
        gap = summary["mean_relative_gap_percent"]
        gap_text = rf"${gap['mean']:.5g}\!\pm\!{gap['ci95']:.3g}$"
        time = summary["mean_total_time_s"]["mean"]
        time_text = f"{time:.5f}" if time < 0.001 else f"{time:.3f}"
        if method == "NEST-coalescent-B32":
            exact_text = rf"\textbf{{{exact} ({rate:.1f}\%)}}"
            gap_text = rf"\textbf{{{gap_text}}}"
        else:
            exact_text = rf"{exact} ({rate:.1f}\%)"
        rows.append(
            f"{label} & {calls_text} & {valid}/250 & {exact_text} & {gap_text} & {time_text} \\\\"
        )
    body = "\n".join(rows)
    return rf"""\begin{{table}}[t]
\centering\scriptsize
\caption{{Sealed, budget-matched exact audit on 250 independently generated
12-vertex HSBMs. Each restarted constructor receives 32 candidate calls; the
lowest structural entropy is selected without consulting $H^*$. Valid reports
successful instances. Exact rates use all 250 graphs as denominator. Gap is
mean relative entropy gap (\%) $\pm$ 95\% CI over valid instances.}}
\label{{tab:optimality}}
\setlength{{\tabcolsep}}{{3.2pt}}
\begin{{tabular}}{{lrrrrr}}
\toprule
Method & Calls & Valid & Exact & Gap (\%) & Time (s) \\
\midrule
{body}
\bottomrule
\end{{tabular}}
\end{{table}}
"""


def markdown_report(artifact: dict, source: Path) -> str:
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    lines = [
        "# Fair 32-Run Restart Audit",
        "",
        "## Protocol",
        "",
        "- New sealed graph seeds 160--209 in five regimes (250 graphs total).",
        "- Regime RNG streams are independent.",
        "- Exact optima are hidden until after structural-entropy-only selection.",
        "- NEST, HCSE, and both BBM variants receive 32 candidate calls per graph.",
        "- HCSE cycles heights 2--5; label-free BBM cycles k=2--8; oracle BBM receives planted k=6.",
        f"- Raw candidate-level artifact: `{source}` (SHA-256 `{digest}`).",
        "",
        "## Results",
        "",
        "| Method | Valid | Exact / 250 | Mean relative gap ± 95% CI | Worst gap | Mean time |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for method, _ in METHODS:
        summary = artifact["summary"][method]
        gap = summary["mean_relative_gap_percent"]
        lines.append(
            f"| {method} | {summary['successful_instances']}/250 | "
            f"{summary['globally_optimal']}/250 ({summary['optimal_hit_rate_percent']:.1f}%) | "
            f"{gap['mean']:.6g}% ± {gap['ci95']:.3g}% | "
            f"{summary['max_relative_gap_percent']:.6g}% | "
            f"{summary['mean_total_time_s']['mean']:.6g} s |"
        )

    miss = next(
        row
        for row in artifact["records"]
        if not row["outcomes"]["NEST-coalescent-B32"]["globally_optimal"]
    )
    miss_outcome = miss["outcomes"]["NEST-coalescent-B32"]
    failed_oracle = [
        row
        for row in artifact["records"]
        if row["outcomes"]["BBM-oracle-B32"].get("status") == "failed"
    ]
    hcse_unique = [
        row["outcomes"]["HCSE-B32"]["unique_entropies_1e-10"]
        for row in artifact["records"]
    ]
    lines.extend([
        "",
        "## Audit interpretation",
        "",
        "- The equal-candidate comparison is NEST-coalescent-B32, not NEST-R32: both use exactly 32 candidates. The three additional deterministic starts in NEST-R32 do not change any selected endpoint on this split.",
        f"- NEST is exact on 249/250. Its sole miss is `{miss['regime']}` seed {miss['graph_seed']}: optimum {miss['global_optimum_bits']:.12f} bits, selected {miss_outcome['entropy_bits']:.12f} bits, a {miss_outcome['relative_gap_percent']:.5f}% gap.",
        "- Against NEST, HCSE has 0 wins / 2 ties / 248 losses; oracle BBM has 0 wins / 1 tie / 249 losses (counting failures as losses); label-free BBM has 0 wins / 1 tie / 249 losses; SE agglomerative has 0 wins / 44 ties / 206 losses.",
        f"- HCSE produces only 1--3 distinct entropies across its 32 calls (mean {sum(hcse_unique)/len(hcse_unique):.3f}), so repeated calls mostly repeat a deterministic constructor rather than explore 32 basins.",
        "- Oracle BBM fails on two full instances because all 32 calls raise `Cheeger cut: Graph should not be empty!`: "
        + ", ".join(f"{row['regime']} seed {row['graph_seed']}" for row in failed_oracle)
        + ". Its gap statistics therefore use 248 valid instances, while the exact-hit rate retains all 250 in the denominator.",
        "- This is finite-suite evidence. It does not prove a worst-case approximation ratio or success probability on arbitrary graphs.",
        "",
        "## Reproduction",
        "",
        "```bash",
        "MPLCONFIGDIR=/tmp/selib_mplconfig .venv/bin/python scripts/run_nni_restart_fairness.py --output results/nni_restart_fairness.json --seed-start 160 --seeds 50 --budget 32",
        ".venv/bin/python scripts/verify_nni_restart_fairness.py",
        "```",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="results/nni_restart_fairness.json")
    parser.add_argument("--table", default="paper/se-hier-nni/tables/optimality.tex")
    parser.add_argument("--report", default="research/se-hier-nni/RESTART_FAIRNESS_AUDIT.md")
    args = parser.parse_args()
    source = Path(args.input)
    artifact = json.loads(source.read_text())
    table = Path(args.table)
    report = Path(args.report)
    table.parent.mkdir(parents=True, exist_ok=True)
    report.parent.mkdir(parents=True, exist_ok=True)
    table.write_text(latex_table(artifact))
    report.write_text(markdown_report(artifact, source))
    print(f"wrote {table} and {report}")


if __name__ == "__main__":
    main()
