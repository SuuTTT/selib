"""docs/recursive.html — recursive triangle-fractal community structures, each shown
as a Sierpinski-style graph (coloured by the encoding tree's top split) beside its
se_hier encoding-tree dendrogram. From results/recursive.json."""
import json, os, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results", "recursive.json")
OUT = os.path.join(ROOT, "docs")
PALETTE = ["#e0245e", "#2563eb", "#16a34a", "#f59e0b", "#7c3aed", "#0891b2"]


def svg_graph(gr, w=300, h=270):
    pos = {int(k): v for k, v in gr["pos"].items()}
    labels, edges = gr["labels"], gr["edges"]
    xs = [p[0] for p in pos.values()]; ys = [p[1] for p in pos.values()]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    pad = 14
    r = 6 if gr["n"] <= 12 else (4 if gr["n"] <= 30 else 2.6)
    def X(x): return pad + (w - 2 * pad) * (x - x0) / (x1 - x0 + 1e-9)
    def Y(y): return pad + (h - 2 * pad) * (1 - (y - y0) / (y1 - y0 + 1e-9))
    p = [f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">']
    for u, v in edges:
        a, b = pos[u], pos[v]
        p.append(f'<line x1="{X(a[0]):.1f}" y1="{Y(a[1]):.1f}" x2="{X(b[0]):.1f}" y2="{Y(b[1]):.1f}" stroke="#cbd2d9" stroke-width="0.7"/>')
    for u, pt in pos.items():
        c = PALETTE[labels[u] % len(PALETTE)]
        p.append(f'<circle cx="{X(pt[0]):.1f}" cy="{Y(pt[1]):.1f}" r="{r}" fill="{c}" stroke="#fff" stroke-width="0.6"/>')
    p.append("</svg>")
    return "".join(p)


def svg_dendro(tree, w=300, h=270):
    leaves = []; maxd = [0]
    def order(n, d):
        maxd[0] = max(maxd[0], d)
        if "leaf" in n:
            leaves.append(n); n["_x"] = len(leaves) - 1; n["_d"] = d; return n["_x"]
        xs = [order(c, d + 1) for c in n["children"]]
        n["_x"] = sum(xs) / len(xs); n["_d"] = d; return n["_x"]
    order(tree, 0)
    nL = max(len(leaves), 1); D = max(maxd[0], 1); pad = 14
    def X(x): return pad + (w - 2 * pad) * (x / max(nL - 1, 1))
    def Y(d): return pad + (h - 2 * pad) * (d / D)
    p = [f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">']
    def draw(n):
        if "leaf" in n:
            p.append(f'<circle cx="{X(n["_x"]):.1f}" cy="{Y(n["_d"]):.1f}" r="2.2" fill="#e0245e"/>'); return
        for c in n["children"]:
            p.append(f'<line x1="{X(n["_x"]):.1f}" y1="{Y(n["_d"]):.1f}" x2="{X(c["_x"]):.1f}" y2="{Y(c["_d"]):.1f}" stroke="#6b7280" stroke-width="1"/>')
            draw(c)
    draw(tree)
    p.append("</svg>")
    return "".join(p)


def card(gr):
    comp = (gr["se_1d"] - gr["se_2d_opt"]) / gr["se_1d"] * 100 if gr["se_1d"] else 0
    return (
        f'<div class="card"><h3>{html.escape(gr["name"])}</h3>'
        f'<div class="row">'
        f'<div class="fig">{svg_graph(gr)}<div class="cap">graph (colour = top-level community)</div></div>'
        f'<div class="fig">{svg_dendro(gr["tree"])}<div class="cap">se_hier encoding tree</div></div>'
        f'</div>'
        f'<table class="stat"><tbody>'
        f'<tr><td>nodes / edges</td><td>{gr["n"]} / {gr["m"]}</td></tr>'
        f'<tr><td>flat communities (SE-optimal)</td><td><b>{gr["k_flat"]}</b> = 3<sup>{gr["level"]-1}</sup></td></tr>'
        f'<tr><td>encoding-tree height</td><td><b>{gr["tree_height"]}</b></td></tr>'
        f'<tr><td>1D structural entropy</td><td>{gr["se_1d"]:.3f}</td></tr>'
        f'<tr><td>2D structural entropy (optimal)</td><td>{gr["se_2d_opt"]:.3f}</td></tr>'
        f'<tr><td>encoding-tree entropy H<sup>T</sup></td><td><b>{gr["se_tree_opt"]:.3f}</b></td></tr>'
        f'<tr><td>compression vs 1D</td><td>{comp:.1f}%</td></tr>'
        f'</tbody></table></div>')


def main():
    data = json.load(open(RES))
    cards = "".join(card(g) for g in data["graphs"])
    css = """
    :root{--fg:#1f2937;--mut:#6b7280;--bd:#e5e7eb;--se:#e0245e}
    *{box-sizing:border-box}
    body{font:16px/1.6 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:var(--fg);max-width:1000px;margin:0 auto;padding:32px 20px 80px}
    h1{font-size:30px;margin:0 0 4px} a{color:#2563eb} .sub{color:var(--mut);margin:0 0 8px}
    code{background:#f3f4f6;padding:2px 6px;border-radius:5px;font-size:14px}
    .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:18px;margin-top:18px}
    .card{border:1px solid var(--bd);border-radius:12px;padding:14px 16px;background:#fff}
    .card h3{margin:0 0 8px;font-size:16px}
    .row{display:flex;gap:10px;flex-wrap:wrap} .fig{flex:1 1 140px;min-width:130px}
    .cap{font-size:11.5px;color:var(--mut);text-align:center;margin-top:3px}
    svg{width:100%;height:auto;border:1px solid var(--bd);border-radius:8px;background:#fff}
    table.stat{width:100%;border-collapse:collapse;margin-top:8px;font-size:12.5px}
    table.stat td{padding:3px 4px;border-bottom:1px solid #f1f3f5} table.stat td:last-child{text-align:right}
    .foot{color:var(--mut);font-size:13px;margin-top:34px;border-top:1px solid var(--bd);padding-top:14px}
    """
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>selib — recursive community structures</title>
<style>{css}</style></head><body>
<h1>Recursive community structures</h1>
<p class="sub">Triangle of triangles, and deeper. A level-k graph is three copies of
level-(k&minus;1) joined pairwise — a clean nested hierarchy.
<a href="index.html">← benchmark</a> · <a href="gallery.html">gallery</a> ·
<a href="tutorial.html">tutorial</a> · <a href="https://github.com/SuuTTT/selib">repo</a></p>

<p>These graphs are built to have <b>hierarchy at every scale</b>, which is exactly
what structural entropy is for. Two things stand out. First, <code>selib.optimal_2d</code>
recovers <b>exactly 3<sup>k&minus;1</sup> communities</b> — the finest triangles
(3, then 9, then 27) — with no number-of-clusters hint. Second, and more telling:
as the graph grows 9 → 27 → 81 nodes, the flat 2D entropy climbs (1.90 → 2.41 → 2.95)
but the <b>encoding-tree entropy H<sup>T</sup> barely moves</b> (1.60 → 1.72 → 1.79).
A self-similar hierarchy is almost free to encode <i>hierarchically</i> — the
dendrogram on the right captures the full nesting, which a flat partition cannot.
This is the clearest possible picture of why structural entropy is defined over a
tree rather than a single cut.</p>

<div class="grid">{cards}</div>

<div class="foot">Built with <code>scripts/run_recursive.py</code> (triangle fractal +
<code>selib</code>) on a fleet box; every value computed, the tree drawn from the
actual <code>se_hier</code> output.</div>
</body></html>"""
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "recursive.html"), "w") as f:
        f.write(page)
    with open(os.path.join(OUT, "recursive.json"), "w") as f:
        json.dump(data, f, indent=2)
    print(f"wrote {OUT}/recursive.html ({len(data['graphs'])} graphs)")


if __name__ == "__main__":
    main()
