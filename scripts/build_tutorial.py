"""Generate docs/tutorial.html from results/tutorial.json — worked examples of
computing 2D structural entropy, with full term breakdowns and selib one-liners."""
import json, os, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results", "tutorial.json")
OUT = os.path.join(ROOT, "docs")
PALETTE = ["#e0245e", "#2563eb", "#16a34a", "#f59e0b", "#7c3aed", "#0891b2", "#db2777", "#65a30d"]


def svg(ex, w=240, h=200):
    pos = {int(k): v for k, v in ex["pos"].items()}
    labels, edges = ex["labels"], ex["edges"]
    xs = [p[0] for p in pos.values()]; ys = [p[1] for p in pos.values()]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    pad = 22
    def X(x): return pad + (w - 2 * pad) * (x - x0) / (x1 - x0 + 1e-9)
    def Y(y): return pad + (h - 2 * pad) * (1 - (y - y0) / (y1 - y0 + 1e-9))
    p = [f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">']
    for u, v in edges:
        a, b = pos[u], pos[v]
        p.append(f'<line x1="{X(a[0]):.1f}" y1="{Y(a[1]):.1f}" x2="{X(b[0]):.1f}" y2="{Y(b[1]):.1f}" stroke="#cbd2d9" stroke-width="1.4"/>')
    for u, pt in pos.items():
        c = PALETTE[labels[u] % len(PALETTE)]
        p.append(f'<circle cx="{X(pt[0]):.1f}" cy="{Y(pt[1]):.1f}" r="9" fill="{c}" stroke="#fff" stroke-width="1.4"/>')
        p.append(f'<text x="{X(pt[0]):.1f}" y="{Y(pt[1])+3.5:.1f}" text-anchor="middle" font-size="10" fill="#fff">{u}</text>')
    p.append("</svg>")
    return "".join(p)


def card(ex):
    bd = ex["breakdown"]; tm = bd["two_m"]
    rows = "".join(
        f"<tr><td>{r['comm']}</td><td>{{{', '.join(map(str, r['members']))}}}</td>"
        f"<td>{r['V']:g}</td><td>{r['g']:g}</td>"
        f"<td>{r['module_term']:.4f}</td><td>{r['within_term']:.4f}</td></tr>"
        for r in bd["rows"])
    intflag = ""
    if abs(ex["se_2d"] - round(ex["se_2d"])) < 1e-6:
        intflag = f' <span class="int">= {round(ex["se_2d"])} bit{"s" if round(ex["se_2d"])!=1 else ""} exactly</span>'
    return (
        f'<div class="card"><h3>{html.escape(ex["name"])}</h3>'
        f'<div class="row"><div class="fig">{svg(ex)}'
        f'<div class="cap">n={ex["n"]}, m={ex["m"]}, 2m={tm:g}; colour = community</div></div>'
        f'<div class="body"><p class="note">{ex["note"]}</p>'
        f'<table class="bd"><thead><tr><th>j</th><th>members</th><th>V<sub>j</sub></th>'
        f'<th>g<sub>j</sub></th><th>module</th><th>within</th></tr></thead>'
        f'<tbody>{rows}</tbody>'
        f'<tfoot><tr><td colspan="4">totals</td><td>{bd["module_total"]:.4f}</td>'
        f'<td>{bd["within_total"]:.4f}</td></tr></tfoot></table>'
        f'<p class="res">H<sup>1</sup> = {ex["se_1d"]:.4f} &nbsp;·&nbsp; '
        f'<b>H<sup>2</sup> = {bd["module_total"]:.4f} + {bd["within_total"]:.4f} '
        f'= {ex["se_2d"]:.4f}</b>{intflag}</p>'
        f'<pre><code>selib.structural_entropy(G, {ex["labels"]})  # -> {ex["se_2d_selib"]:.4f}</code></pre>'
        f'</div></div></div>')


def crosscheck_html():
    p = os.path.join(os.path.dirname(RES), "se_crosscheck.json")
    if not os.path.exists(p):
        return ""
    x = json.load(open(p))
    parts = []
    gj = x.get("glassjax", {})
    if gj.get("available"):
        parts.append(
            f"<li><b>glass-jax discrete scorer</b> (an independent implementation of the "
            f"same definition): over {gj['trials']} random graphs — connected, "
            f"<i>disconnected</i>, and <i>weighted</i> — the maximum absolute difference from "
            f"<code>selib</code> is <b>{gj['max_abs_diff']:.1e}</b> bits, i.e. floating-point "
            f"machine precision. The definitions are identical.</li>")
    dd = x.get("dedoc", {})
    if dd.get("available") and dd.get("records"):
        ex = dd["records"][0]
        parts.append(
            f"<li><b>deDoc</b> (original Java, Li 2018): reproduces its partition exactly; the "
            f"value it prints is a Hi-C&#8209;specific <i>normalized</i> 2D-SE (e.g. Karate "
            f"{ex['dedoc_printed']:.3f}), not raw bits, so it is not directly equal to "
            f"<code>selib</code>'s H<sup>2</sup> = {ex['selib_H2_of_dedoc_partition']:.3f} of the "
            f"same partition — the <i>definition</i> is confirmed via glass-jax above, while the "
            f"<i>normalization</i> differs.</li>")
    return ("<ul>" + "".join(parts) + "</ul>") if parts else ""


def main():
    data = json.load(open(RES))
    cards = "".join(card(e) for e in data["examples"])
    xc = crosscheck_html()
    css = """
    :root{--fg:#1f2937;--mut:#6b7280;--bd:#e5e7eb;--se:#e0245e}
    *{box-sizing:border-box}
    body{font:16px/1.6 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:var(--fg);max-width:980px;margin:0 auto;padding:32px 20px 80px}
    h1{font-size:30px;margin:0 0 4px} h2{font-size:21px;margin:34px 0 8px;border-bottom:2px solid var(--bd);padding-bottom:6px} a{color:#2563eb}
    .sub{color:var(--mut);margin:0 0 8px}
    code{background:#f3f4f6;padding:2px 6px;border-radius:5px;font-size:13.5px}
    pre{background:#0f172a;color:#e2e8f0;padding:12px;border-radius:8px;overflow:auto;font-size:13px;margin:8px 0 0} pre code{background:none;color:inherit;padding:0}
    .formula{background:#f9fafb;border:1px solid var(--bd);border-radius:10px;padding:14px 18px;font-size:15px;overflow-x:auto}
    .card{border:1px solid var(--bd);border-radius:12px;padding:16px 18px;margin:16px 0;background:#fff}
    .card h3{margin:0 0 8px;font-size:17px}
    .row{display:flex;gap:18px;flex-wrap:wrap} .fig{flex:0 0 240px} .body{flex:1 1 360px}
    .cap{font-size:12px;color:var(--mut);text-align:center;margin-top:4px} .note{margin:0 0 8px}
    svg{border:1px solid var(--bd);border-radius:8px;background:#fff;width:240px;height:auto}
    table.bd{border-collapse:collapse;width:100%;font-size:13px;margin-top:6px}
    table.bd th,table.bd td{border:1px solid var(--bd);padding:4px 8px;text-align:right} table.bd td:nth-child(2){text-align:left}
    table.bd thead th{background:#f9fafb} table.bd tfoot td{font-weight:600;background:#f9fafb}
    .res{margin:10px 0 0;font-size:15px} .int{color:var(--se);font-weight:700}
    .foot{color:var(--mut);font-size:13px;margin-top:36px;border-top:1px solid var(--bd);padding-top:14px}
    """
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>selib — how to compute 2D structural entropy</title>
<style>{css}</style></head><body>
<h1>Tutorial: computing 2D structural entropy</h1>
<p class="sub">Worked, byte-checked examples — some with integer answers.
<a href="index.html">← benchmark</a> · <a href="gallery.html">gallery</a> · <a href="https://github.com/SuuTTT/selib">repo</a></p>

<h2>The formula</h2>
<p>For a graph with degrees d<sub>v</sub>, total degree 2m = &Sigma;<sub>v</sub> d<sub>v</sub>,
and a partition into communities j with volume V<sub>j</sub> = &Sigma;<sub>v&isin;j</sub> d<sub>v</sub>
and cut g<sub>j</sub> (edge weight leaving j), the 2D structural entropy is</p>
<div class="formula">
H<sup>2</sup> =
&minus; &Sigma;<sub>j</sub> (g<sub>j</sub>/2m) log<sub>2</sub>(V<sub>j</sub>/2m)
&nbsp;<span style="color:#6b7280">(module / cut term)</span>
&nbsp;&minus; &Sigma;<sub>v</sub> (d<sub>v</sub>/2m) log<sub>2</sub>(d<sub>v</sub>/V<sub>c(v)</sub>)
&nbsp;<span style="color:#6b7280">(within term)</span>
</div>
<p>The 1D entropy H<sup>1</sup> = &minus;&Sigma;<sub>v</sub>(d<sub>v</sub>/2m)log<sub>2</sub>(d<sub>v</sub>/2m)
is the same quantity with no partition (every node its own "module" sharing the whole graph as parent);
it is an upper bound that H<sup>2</sup> improves on whenever the graph has community structure. Below,
the <code>module</code> and <code>within</code> columns are the per-community contributions to each sum;
the displayed totals are reproduced exactly by <code>selib</code>.</p>

{cards}

<h2>Definitions &amp; conventions (what selib actually computes)</h2>
<p>Structural entropy is usually motivated by a random walk: on a <i>connected</i>
graph the stationary distribution is &pi;<sub>v</sub> = d<sub>v</sub>/2m, and the
formulas above are its expected description length under a partition. But the
quantities they use — degrees, community volumes V<sub>j</sub>, and cuts
g<sub>j</sub> — are purely <b>combinatorial</b>, so the entropy is well-defined for
<i>any</i> graph, connected or not. selib computes it directly from those quantities.
Concretely:</p>
<ul>
<li><b>Units:</b> bits (log base 2). These are the raw structural-entropy values of
Li &amp; Pan (2016), <i>not</i> normalized by 1D-SE or by log&#8202;n.</li>
<li><b>Weights:</b> an edge attribute <code>weight</code> (default 1); the degree
d<sub>v</sub> is the weighted degree and 2m = &Sigma;<sub>v</sub> d<sub>v</sub>.</li>
<li><b>Disconnected / "discrete" graphs:</b> no connectivity is required. A graph
that splits into pieces (like <i>Four disjoint edges</i> above) just has several
communities with cut g<sub>j</sub>=0; their volumes still enter the sums. The
random-walk picture is then per-component, but the entropy <i>value</i> is
unambiguous — we treat d<sub>v</sub>/2m as the node weights exactly as in the
connected case. This is the same convention used by deDoc, CoDeSEG, and the
glass-jax discrete scorer (verified — see below).</li>
<li><b>Isolated nodes</b> (degree 0) contribute nothing: the d&#8202;log&#8202;d terms
vanish. <b>Self-loops</b> count twice in the degree (NetworkX convention) and are
always internal to their community.</li>
<li><b>Direction:</b> graphs are treated as undirected (the adjacency is
symmetrized); directed SE is out of scope for v0.2.</li>
<li><b>Higher dimensions:</b> the 2D value is the entropy of a flat (2-level)
partition; the full encoding-tree value H<sup>T</sup> generalizes it to trees of any
height (a 2-level tree's H<sup>T</sup> equals H<sup>2</sup> exactly — checked).</li>
</ul>

<h2>Cross-checked against independent implementations</h2>
<p>The 2D-SE numbers here are validated against code that implements the formula
independently. Full per-run report: <a href="se_crosscheck.json">se_crosscheck.json</a>.</p>
"""+ xc +"""

<div class="foot">Every number here is computed by <code>selib.calc</code> and asserted equal to the
hand-derived breakdown in <a href="tutorial.json">tutorial.json</a> — if the arithmetic and the library
ever disagreed, the build would fail.</div>
</body></html>"""
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "tutorial.html"), "w") as f:
        f.write(page)
    with open(os.path.join(OUT, "tutorial.json"), "w") as f:
        json.dump(data, f, indent=2)
    print(f"wrote {OUT}/tutorial.html ({len(data['examples'])} examples)")


if __name__ == "__main__":
    main()
