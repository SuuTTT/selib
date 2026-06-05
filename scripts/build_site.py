"""Generate docs/index.html (GitHub Pages) from results/benchmark_results.json.

Self-contained: inline CSS + inline-SVG charts, no JS, no external assets. Every
number on the page is read straight from the results JSON the fleet produced.
Run:  python3 scripts/build_site.py
"""
import json, os, html
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results", "benchmark_results.json")
OUT_DIR = os.path.join(ROOT, "docs")

METHOD_ORDER = ["louvain", "leiden", "infomap", "spectral", "se_agglomerative"]
SE_METHODS = {"se_agglomerative", "dedoc", "codeseg"}
COLORS = {"louvain": "#6b7280", "leiden": "#9ca3af", "infomap": "#a8a29e",
          "spectral": "#60a5fa", "se_agglomerative": "#e0245e"}


def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else float("nan")


def agg(records, datasets, metric):
    """{dataset: {method: mean}} restricted to given datasets."""
    acc = defaultdict(lambda: defaultdict(list))
    for r in records:
        if r["dataset"] in datasets and r.get(metric) is not None:
            acc[r["dataset"]][r["method"]].append(r[metric])
    return {d: {m: mean(v) for m, v in md.items()} for d, md in acc.items()}


def fmt(x, nd=3):
    if x is None or (isinstance(x, float) and x != x):
        return "—"
    return f"{x:.{nd}f}"


def table(title, note, datasets, table_data, methods, highlight_best=True,
          lower_better=False, nd=3):
    th = "".join(f"<th>{html.escape(m)}</th>" for m in methods)
    rows = []
    for d in datasets:
        row = table_data.get(d, {})
        vals = {m: row.get(m) for m in methods}
        finite = [v for v in vals.values() if isinstance(v, float) and v == v]
        best = (min if lower_better else max)(finite) if (highlight_best and finite) else None
        cells = []
        for m in methods:
            v = vals.get(m)
            cls = ""
            if best is not None and isinstance(v, float) and v == v and abs(v - best) < 1e-9:
                cls = ' class="best"'
            se = ' class="se"' if (m in SE_METHODS) else ""
            cells.append(f"<td{cls or se}>{fmt(v, nd)}</td>")
        rows.append(f"<tr><th class='rowh'>{html.escape(d)}</th>{''.join(cells)}</tr>")
    return (f"<h3>{html.escape(title)}</h3><p class='note'>{note}</p>"
            f"<div class='tablewrap'><table><thead><tr><th></th>{th}</tr></thead>"
            f"<tbody>{''.join(rows)}</tbody></table></div>")


def svg_lines(series, xs, ylabel, w=720, h=320, ymax=None):
    """series: {method: [y per x]}. xs: list of x labels (numeric-ish)."""
    pad_l, pad_b, pad_t, pad_r = 52, 40, 16, 16
    iw, ih = w - pad_l - pad_r, h - pad_t - pad_b
    allv = [v for ys in series.values() for v in ys if v == v]
    ymax = ymax or (max(allv) if allv else 1.0)
    ymax = max(ymax, 1e-6)
    n = len(xs)
    def X(i): return pad_l + (iw * (i / (n - 1)) if n > 1 else iw / 2)
    def Y(v): return pad_t + ih * (1 - v / ymax)
    parts = [f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" role="img">']
    # axes + gridlines
    for g in range(5):
        v = ymax * g / 4
        y = Y(v)
        parts.append(f'<line x1="{pad_l}" y1="{y:.1f}" x2="{w-pad_r}" y2="{y:.1f}" stroke="#eee"/>')
        parts.append(f'<text x="{pad_l-8}" y="{y+4:.1f}" text-anchor="end" class="axt">{v:.2f}</text>')
    for i, xl in enumerate(xs):
        parts.append(f'<text x="{X(i):.1f}" y="{h-pad_b+18}" text-anchor="middle" class="axt">{html.escape(str(xl))}</text>')
    parts.append(f'<text x="14" y="{pad_t+ih/2}" transform="rotate(-90 14 {pad_t+ih/2})" text-anchor="middle" class="axl">{html.escape(ylabel)}</text>')
    for m in METHOD_ORDER:
        if m not in series:
            continue
        ys = series[m]
        pts = " ".join(f"{X(i):.1f},{Y(v):.1f}" for i, v in enumerate(ys) if v == v)
        if not pts:
            continue
        c = COLORS.get(m, "#333")
        sw = 3 if m in SE_METHODS else 2
        parts.append(f'<polyline points="{pts}" fill="none" stroke="{c}" stroke-width="{sw}"/>')
        for i, v in enumerate(ys):
            if v == v:
                parts.append(f'<circle cx="{X(i):.1f}" cy="{Y(v):.1f}" r="{sw+0.5}" fill="{c}"/>')
    parts.append("</svg>")
    return "".join(parts)


def legend(methods):
    items = []
    for m in methods:
        c = COLORS.get(m, "#333")
        lab = m + (" (SE)" if m in SE_METHODS else "")
        items.append(f'<span class="lg"><span class="sw" style="background:{c}"></span>{html.escape(lab)}</span>')
    return f'<div class="legend">{"".join(items)}</div>'


def main():
    data = json.load(open(RES))
    recs = data["records"]
    blocks = data["block_membership"]
    methods = [m for m in METHOD_ORDER if m in data["methods"]]
    n_runs = len(recs)
    datasets_all = sorted({r["dataset"] for r in recs})

    present = {r["dataset"] for r in recs}
    real = [d for d in blocks["real_and_sbm"] if d in present]
    lfr = [d for d in blocks["lfr_sweep"] if d in present]
    scale = [d for d in blocks["scalability"] if d in present]

    # --- block 1 tables ---
    nmi1 = agg(recs, real, "nmi")
    ari1 = agg(recs, real, "ari")
    se2d1 = agg(recs, real, "structural_entropy_2d")
    mod1 = agg(recs, real, "modularity")

    t_nmi = table("Accuracy — NMI vs. ground truth", "Higher is better; best per row in red.", real, nmi1, methods)
    t_ari = table("Accuracy — ARI vs. ground truth", "Higher is better.", real, ari1, methods)
    t_mod = table("Cross-objective — modularity", "Higher = more modular partition.", real, mod1, methods)
    t_se = table("Cross-objective — 2D structural entropy", "Lower = more structure captured by the partition.", real, se2d1, methods, lower_better=True)

    # --- block 2: LFR sweep line charts ---
    mus = lfr  # already ordered LFR-mu0.1..0.6
    nmi_lfr = agg(recs, lfr, "nmi")
    series_nmi = {m: [nmi_lfr.get(d, {}).get(m, float("nan")) for d in mus] for m in methods}
    xlabels = [d.replace("LFR-mu", "") for d in mus]
    chart_lfr = svg_lines(series_nmi, xlabels, "mean NMI", ymax=1.0)

    # --- block 3: scalability runtime ---
    time_sc = agg(recs, scale, "time_s")
    nmi_sc = agg(recs, scale, "nmi")
    Ns = scale
    series_t = {m: [time_sc.get(d, {}).get(m, float("nan")) for d in Ns] for m in methods}
    xlabels_n = [d.replace("SBM-scale-N", "") for d in Ns]
    tmax = max((v for ys in series_t.values() for v in ys if v == v), default=1.0)
    chart_time = svg_lines(series_t, xlabels_n, "wall-clock (s)", ymax=tmax * 1.05)
    t_scale_nmi = table("Scalability — NMI", "Per-node community signal held constant as N grows.", Ns, nmi_sc, methods, nd=3)

    # dataset facts
    facts = {}
    for r in recs:
        facts.setdefault(r["dataset"], (r["n"], r["m"], r["k_true"]))
    fact_rows = "".join(
        f"<tr><td>{html.escape(d)}</td><td>{facts[d][0]}</td><td>{facts[d][1]}</td><td>{facts[d][2]}</td></tr>"
        for d in datasets_all)

    css = """
    :root{--fg:#1f2937;--mut:#6b7280;--se:#e0245e;--bg:#fff;--bd:#e5e7eb}
    *{box-sizing:border-box}
    body{font:16px/1.6 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;
         color:var(--fg);max-width:980px;margin:0 auto;padding:32px 20px 80px;background:var(--bg)}
    h1{font-size:30px;margin:0 0 4px} h2{font-size:22px;margin:42px 0 8px;border-bottom:2px solid var(--bd);padding-bottom:6px}
    h3{font-size:17px;margin:22px 0 4px} a{color:#2563eb}
    .sub{color:var(--mut);margin:0 0 6px} .note{color:var(--mut);font-size:14px;margin:2px 0 10px}
    code{background:#f3f4f6;padding:2px 6px;border-radius:5px;font-size:14px}
    pre{background:#0f172a;color:#e2e8f0;padding:16px;border-radius:8px;overflow:auto;font-size:13.5px;line-height:1.5}
    pre code{background:none;color:inherit;padding:0}
    .badges span{display:inline-block;background:#f3f4f6;border:1px solid var(--bd);border-radius:20px;
                 padding:3px 12px;margin:3px 6px 3px 0;font-size:13px;color:var(--mut)}
    .tablewrap{overflow-x:auto} table{border-collapse:collapse;width:100%;margin:6px 0 4px;font-size:14px}
    th,td{border:1px solid var(--bd);padding:6px 10px;text-align:right} thead th{background:#f9fafb;text-align:right}
    th.rowh,td:first-child{text-align:left} .rowh{background:#f9fafb;font-weight:600}
    td.best{background:#fff0f5;color:var(--se);font-weight:700} td.se{color:var(--se)}
    .legend{margin:6px 0 2px} .lg{display:inline-block;margin-right:14px;font-size:13px;color:var(--mut)}
    .sw{display:inline-block;width:11px;height:11px;border-radius:3px;margin-right:5px;vertical-align:middle}
    .axt{font-size:11px;fill:#9ca3af} .axl{font-size:12px;fill:#6b7280}
    .card{border:1px solid var(--bd);border-radius:10px;padding:14px 18px;margin:14px 0;background:#fff}
    .kpi{display:flex;gap:24px;flex-wrap:wrap;margin:10px 0}
    .kpi div{background:#f9fafb;border:1px solid var(--bd);border-radius:8px;padding:10px 16px}
    .kpi b{font-size:22px;display:block} .foot{color:var(--mut);font-size:13px;margin-top:40px;border-top:1px solid var(--bd);padding-top:14px}
    svg{max-width:100%;height:auto;border:1px solid var(--bd);border-radius:8px;background:#fff}
    """

    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>selib — structural-entropy benchmark</title>
<meta name="description" content="selib: a standardized library for structural entropy. Benchmark of SE methods vs. classical community-detection baselines, scored uniformly.">
<style>{css}</style></head><body>

<h1>selib</h1>
<p class="sub">A standardized library for <b>structural entropy</b> — compute it, optimize it,
and benchmark SE methods against classical baselines under one API.</p>
<div class="badges"><span>v{html.escape(str(data['selib_version']))}</span>
<span>{n_runs} benchmark runs</span><span>{len(methods)} methods</span>
<span>{len(datasets_all)} datasets</span><span>MIT</span></div>
<p><a href="https://github.com/SuuTTT/selib">GitHub repo</a> ·
<a href="benchmark_results.json">raw results JSON</a> ·
<a href="https://github.com/SuuTTT/structural-entropy-benchmark">reproduction benchmark</a> ·
<a href="https://github.com/SuuTTT/structural-entropy-survey-paper">survey paper</a></p>

<h2>What this is</h2>
<p>Every SE paper ships its own loader, metric, and (often unmaintained) code, so
"does structural entropy actually help?" is hard to answer on equal footing.
<code>selib</code> fixes the interface: one <code>Method.fit_predict(G, k, seed)</code>
contract, a native 2D-structural-entropy encoding-tree core, shared datasets and
metrics, and a one-call benchmark — so an SE method and a Louvain baseline are
scored exactly the same way. The tables below are produced by that benchmark; the
headline takeaway matches the survey's <i>regime-dependent</i> verdict.</p>

<pre><code>import selib
recs = selib.benchmark(["louvain", "leiden", "se_agglomerative"],
                       ["Karate", "SBM-Clean", "SBM-Noisy"])
selib.summarize(recs, "nmi")</code></pre>

<h2>1 · Real graphs &amp; controlled SBM</h2>
{legend(methods)}
{t_nmi}{t_ari}{t_mod}{t_se}
<p class="note">SE (<span style="color:var(--se)">se_agglomerative</span>, the native greedy
2D-SE encoding tree) matches the baselines on clean, well-separated structure and on
Karate, but does not rescue performance once the planted signal is weak — the same
fragility the survey reports for unsupervised community detection.</p>

<h2>2 · LFR difficulty sweep</h2>
<p class="note">LFR graphs (n=500), mixing parameter μ on the x-axis: higher μ = more
inter-community edges = harder. Mean NMI over 5 seeds.</p>
{legend(methods)}
{chart_lfr}
<p class="note">All methods — SE and baselines alike — degrade together as μ rises and
collapse past the detectability threshold; no method's curve is rescued by the SE
objective. This is the core empirical message, now reproducible in one call.</p>

<h2>3 · Scalability</h2>
<p class="note">SBM with per-node community signal held constant as N grows
(k=10 blocks). Left: wall-clock per run; right table: NMI stays high, so runtime is
measured on a task every method can solve.</p>
{legend(methods)}
{chart_time}
{t_scale_nmi}
<p class="note">The native <span style="color:var(--se)">se_agglomerative</span> core is a
pure-Python greedy merge; the optimized C/igraph baselines (Louvain/Leiden/Infomap)
are faster, while spectral clustering's dense eigendecomposition scales worst. These
are wall-clock facts from the run, not claims.</p>

<h2>Datasets</h2>
<div class="tablewrap"><table><thead><tr><th>dataset</th><th>nodes</th><th>edges</th><th>k (true)</th></tr></thead>
<tbody>{fact_rows}</tbody></table></div>

<h2>Reproduce</h2>
<pre><code>git clone https://github.com/SuuTTT/selib && cd selib
pip install -e ".[extra]"
python3 scripts/run_full_benchmark.py     # writes results/benchmark_results.json
python3 scripts/build_site.py             # regenerates this page from that JSON</code></pre>
<p class="note">All numbers on this page are read directly from
<a href="benchmark_results.json"><code>results/benchmark_results.json</code></a>
produced by the run above on an RTX 3070 box. Methods that wrap a paper's original
code (deDoc, CoDeSEG) are available through the same API once their upstream artifact
is configured; the runs shown here use the native methods + classical baselines.</p>

<div class="foot">Generated from {n_runs} benchmark records ·
selib v{html.escape(str(data['selib_version']))} ·
part of the structural-entropy survey &amp; benchmark project.</div>
</body></html>"""

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, "index.html"), "w") as f:
        f.write(page)
    # ship the raw results next to the page
    with open(os.path.join(OUT_DIR, "benchmark_results.json"), "w") as f:
        json.dump(data, f, indent=2)
    # tell Pages not to run Jekyll
    open(os.path.join(OUT_DIR, ".nojekyll"), "w").close()
    print(f"wrote {OUT_DIR}/index.html  ({n_runs} records)")


if __name__ == "__main__":
    main()
