"""Generate docs/gallery.html — a gallery of SE-optimal partitions of classical
graphs, from results/gallery.json (every layout/label/value produced by the run).
Self-contained: inline CSS + inline SVG, no JS.
"""
import json, os, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results", "gallery.json")
OUT = os.path.join(ROOT, "docs")

PALETTE = ["#e0245e", "#2563eb", "#16a34a", "#f59e0b", "#7c3aed", "#0891b2",
           "#db2777", "#65a30d", "#dc2626", "#0d9488", "#9333ea", "#ca8a04",
           "#0ea5e9", "#84cc16", "#f43f5e", "#6366f1"]


def svg_graph(gr, w=300, h=260):
    pos, labels, edges = gr["pos"], gr["labels"], gr["edges"]
    pos = {int(k): v for k, v in pos.items()}
    xs = [p[0] for p in pos.values()]; ys = [p[1] for p in pos.values()]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    pad = 14
    rad = 5 if len(pos) <= 80 else 3.2
    def X(x): return pad + (w - 2 * pad) * (x - x0) / (x1 - x0 + 1e-9)
    def Y(y): return pad + (h - 2 * pad) * (1 - (y - y0) / (y1 - y0 + 1e-9))
    parts = [f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" role="img">']
    for u, v in edges:
        pu, pv = pos[u], pos[v]
        parts.append(f'<line x1="{X(pu[0]):.1f}" y1="{Y(pu[1]):.1f}" x2="{X(pv[0]):.1f}" '
                     f'y2="{Y(pv[1]):.1f}" stroke="#d7dbe0" stroke-width="0.6"/>')
    for u, p in pos.items():
        c = PALETTE[labels[u] % len(PALETTE)]
        parts.append(f'<circle cx="{X(p[0]):.1f}" cy="{Y(p[1]):.1f}" r="{rad}" fill="{c}" '
                     f'stroke="#fff" stroke-width="0.6"/>')
    parts.append("</svg>")
    return "".join(parts)


def card(gr):
    se1, se2 = gr["se_1d"], gr["se_2d_opt"]
    return (
        f'<div class="card"><h3>{html.escape(gr["name"])}</h3>'
        f'<div class="note">{html.escape(gr["note"])}</div>'
        f'{svg_graph(gr)}'
        f'<table class="stat"><tbody>'
        f'<tr><td>nodes / edges</td><td>{gr["n"]} / {gr["m"]}</td></tr>'
        f'<tr><td>communities (SE-optimal)</td><td><b>{gr["k"]}</b></td></tr>'
        f'<tr><td>1D structural entropy</td><td>{se1:.3f}</td></tr>'
        f'<tr><td>2D structural entropy (optimal)</td><td><b>{se2:.3f}</b></td></tr>'
        f'<tr><td>compression vs 1D</td><td>{gr["compression"]*100:.1f}%</td></tr>'
        f'<tr><td>encoding-tree entropy H<sup>T</sup></td><td>{gr["se_tree_opt"]:.3f}</td></tr>'
        f'</tbody></table></div>')


def main():
    data = json.load(open(RES))
    cards = "".join(card(g) for g in data["graphs"])
    css = """
    :root{--fg:#16202b;--mut:#65728a;--bd:#dfe5ec;--bg:#ffffff;--card:#fbfcfd;--se:#e0245e}
    @media (prefers-color-scheme: dark){
      :root{--fg:#e7ecf3;--mut:#94a3b8;--bd:#2c3a4d;--bg:#0e1520;--card:#16202d}}
    *{box-sizing:border-box}
    body{font:16px/1.6 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;
         color:var(--fg);background:var(--bg);max-width:1100px;margin:0 auto;padding:32px 20px 80px}
    h1{font-size:30px;margin:0 0 4px;letter-spacing:-.5px} a{color:#2563eb;text-decoration:none} a:hover{text-decoration:underline}
    .sub{color:var(--mut);margin:0 0 8px}
    .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:18px;margin-top:18px}
    .card{border:1px solid var(--bd);border-radius:14px;padding:14px 16px;background:var(--card);
          transition:transform .1s ease, box-shadow .1s ease}
    .card:hover{transform:translateY(-3px);box-shadow:0 6px 22px rgba(0,0,0,.13)}
    .card h3{margin:0 0 2px;font-size:16px} .card .note{color:var(--mut);font-size:12.5px;margin-bottom:8px;min-height:2.4em}
    svg{width:100%;height:auto;border:1px solid var(--bd);border-radius:10px;background:#fff}
    table.stat{width:100%;border-collapse:collapse;margin-top:8px;font-size:12.5px}
    table.stat td{padding:3px 4px;border-bottom:1px solid var(--bd)} table.stat td:last-child{text-align:right}
    code{background:rgba(127,127,127,.12);padding:2px 6px;border-radius:5px;font-size:14px}
    pre{background:#0f172a;color:#e2e8f0;padding:14px;border-radius:10px;overflow:auto;font-size:13px}
    pre code{background:none;color:inherit;padding:0}
    .foot{color:var(--mut);font-size:13px;margin-top:36px;border-top:1px solid var(--bd);padding-top:14px}
    """
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>selib — SE gallery</title>
<style>{css}</style></head><body>
<h1>Gallery: optimal structural-entropy partitions</h1>
<p class="sub">The SE-optimal flat partition (minimizing 2D structural entropy at free
<i>k</i>, via <code>selib.optimal_2d</code>) on classical graphs. Node colour = community.
<a href="index.html">← benchmark</a> · <a href="tutorial.html">SE tutorial</a> · <a href="https://github.com/SuuTTT/selib">repo</a></p>

<p>Each graph is partitioned by <b>minimizing its structural entropy</b> — no target
number of clusters is given; the resolution is chosen by the objective. The
calculator behind these numbers:</p>
<pre><code>import selib, networkx as nx
G = nx.karate_club_graph()
selib.se_report(G)
# {{'n': 34, 'm': 78, 'se_1d': ..., 'se_2d_optimal': ..., 'num_communities': ..., ...}}
labels, h2 = selib.optimal_2d(G)        # SE-optimal partition + its 2D-SE
selib.structural_entropy(G, labels)     # 2D-SE of any partition
selib.structural_entropy(G, dim=1)      # 1D-SE (partition-free upper bound)</code></pre>

<div class="grid">{cards}</div>

<div class="foot">Read this gallery as: a graph with strong community structure
(Karate, SBM, caveman, LFR) compresses well — its optimal 2D entropy sits far below
the partition-free 1D value — while a structureless graph (Petersen, grid) barely
compresses, and a pure tree is best described hierarchically. Every value is computed
by <code>selib.calc</code> from the graph; nothing is hand-set.</div>
</body></html>"""
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "gallery.html"), "w") as f:
        f.write(page)
    with open(os.path.join(OUT, "gallery.json"), "w") as f:
        json.dump(data, f, indent=2)
    print(f"wrote {OUT}/gallery.html ({len(data['graphs'])} graphs)")


if __name__ == "__main__":
    main()
