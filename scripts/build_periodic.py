"""docs/periodic.html — a DATA-DRIVEN periodic table of structural-entropy methods,
generated from the survey's facet tags (results/facet_tags.jsonl, 81 core papers).
Two projections, toggleable: graph type x direction, and role-of-SE x direction
(mirroring the journal paper's Table role-task). Cells are heat-shaded by paper
count; clicking a cell pins its paper list. Blank = open direction.
Curated open-directions + node-distribution note come from results/se_periodic.json.
"""
import json, os, html
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
OUT = os.path.join(ROOT, "docs")

GRAPH_ORDER = ["simple", "weighted", "directed", "bipartite", "signed", "attributed",
               "heterogeneous", "hypergraph", "dynamic"]
ROLE_ORDER = ["objective", "prior", "metric", "regularizer", "feature", "robustness"]
ROLE_HINT = {"objective": "SE is minimized", "prior": "SE structure feeds a learner",
             "metric": "SE scores/evaluates", "regularizer": "SE term in a loss",
             "feature": "SE values as inputs", "robustness": "privacy/adversarial use"}
TASK_ORDER = ["theory", "community_detection", "hierarchical_clustering", "graph_pooling",
              "structure_learning", "contrastive_ssl", "rl_abstraction", "application"]
TASK_LABEL = {"theory": "theory/def", "community_detection": "community det.",
              "hierarchical_clustering": "hierarchy", "graph_pooling": "pooling",
              "structure_learning": "structure learn.", "contrastive_ssl": "contrastive",
              "rl_abstraction": "RL abstraction", "application": "applications"}


def load():
    gt = defaultdict(set); tk = defaultdict(set); rl = defaultdict(set); yr = {}
    for l in open(os.path.join(RES, "facet_tags.jsonl")):
        r = json.loads(l)
        if r["facet"] == "graph_type": gt[r["value"]].add(r["key"])
        elif r["facet"] == "task": tk[r["value"]].add(r["key"])
        elif r["facet"] == "se_role": rl[r["value"]].add(r["key"])
        elif r["facet"] == "year": yr[r["key"]] = r["value"]
    return gt, tk, rl, yr


def matrix(rows_map, row_order, tk, yr):
    out = []
    for g in row_order:
        row = []
        for t in TASK_ORDER:
            keys = sorted(rows_map.get(g, set()) & tk.get(t, set()),
                          key=lambda k: yr.get(k, "9999"))
            row.append(keys)
        out.append(row)
    return out


def main():
    gt, tk, rl, yr = load()
    se = json.load(open(os.path.join(RES, "se_periodic.json")))
    allkeys = set().union(*gt.values()) if gt else set()
    n_total = len(allkeys)

    data = {
        "views": {
            "graph": {"rows": GRAPH_ORDER, "hints": {},
                      "cells": matrix(gt, GRAPH_ORDER, tk, yr),
                      "label": "graph type × direction"},
            "role": {"rows": ROLE_ORDER, "hints": ROLE_HINT,
                     "cells": matrix(rl, ROLE_ORDER, tk, yr),
                     "label": "role of SE × direction"},
        },
        "cols": [TASK_LABEL[t] for t in TASK_ORDER],
        "years": yr,
    }

    opens = "".join(f"<li>{html.escape(o)}</li>" for o in se["open_directions"])
    pi = se["pi_note"]

    css = """
:root{--fg:#16202b;--mut:#65728a;--bd:#dfe5ec;--bg:#ffffff;--card:#f6f8fa;
 --accent:#e0245e;--link:#2563eb;--tile0:#f3f6f9;--pin:#fff7e6;--pinbd:#f5c66b}
@media (prefers-color-scheme: dark){
 :root{--fg:#e7ecf3;--mut:#94a3b8;--bd:#2c3a4d;--bg:#0e1520;--card:#16202d;
  --tile0:#141d29;--pin:#2a2110;--pinbd:#8a6a23}}
*{box-sizing:border-box}
body{font:15.5px/1.55 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;
 color:var(--fg);background:var(--bg);max-width:1180px;margin:0 auto;padding:32px 20px 80px}
h1{font-size:30px;margin:0 0 4px;letter-spacing:-.5px}
h2{font-size:20px;margin:36px 0 8px;border-bottom:2px solid var(--bd);padding-bottom:6px}
a{color:var(--link);text-decoration:none} a:hover{text-decoration:underline}
.sub{color:var(--mut);margin:0 0 10px}
.toggle{display:inline-flex;border:1px solid var(--bd);border-radius:10px;overflow:hidden;margin:12px 0}
.toggle button{font:600 13.5px/1 inherit;padding:9px 16px;border:0;background:transparent;color:var(--mut);cursor:pointer}
.toggle button.on{background:var(--accent);color:#fff}
.grid{display:grid;gap:5px;margin-top:8px}
.hcell,.rcell{font-size:11px;font-weight:700;color:var(--mut);display:flex;align-items:center}
.hcell{justify-content:center;text-align:center;padding:2px}
.rcell{justify-content:flex-end;text-align:right;padding-right:8px}
.tile{position:relative;border:1px solid var(--bd);border-radius:9px;background:var(--tile0);
 min-height:54px;padding:6px 8px;cursor:pointer;transition:transform .08s ease}
.tile:hover{transform:translate(0,-2px);box-shadow:0 3px 14px rgba(0,0,0,.12)}
.tile .n{font-size:17px;font-weight:800}
.tile .yr{font-size:9.5px;color:var(--mut)}
.tile.gap{cursor:default;background:transparent;border-style:dashed}
.tile.gap::after{content:"open";position:absolute;inset:0;display:flex;align-items:center;
 justify-content:center;font-size:10px;color:var(--mut);opacity:.65;letter-spacing:.06em}
.tile.pinned{outline:2px solid var(--pinbd);background:var(--pin)}
#detail{border:1px solid var(--bd);border-radius:12px;background:var(--card);padding:14px 18px;
 margin-top:14px;min-height:54px}
#detail .keys{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}
#detail .key{font:12px/1.6 ui-monospace,SFMono-Regular,Menlo,monospace;background:var(--bg);
 border:1px solid var(--bd);border-radius:6px;padding:1px 8px}
.note{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:14px 18px;margin:14px 0}
.foot{color:var(--mut);font-size:13px;margin-top:36px;border-top:1px solid var(--bd);padding-top:14px}
.legend{font-size:12.5px;color:var(--mut);margin-top:6px}
"""

    js = """
const DATA = __DATA__;
let view = 'graph', pinned = null;
const heat = n => n===0 ? '' :
  `rgba(224,36,94,${Math.min(0.08 + 0.105*Math.log2(1+n), 0.62)})`;
function render(){
  const v = DATA.views[view];
  const grid = document.getElementById('grid');
  grid.style.gridTemplateColumns = `120px repeat(${DATA.cols.length},1fr)`;
  let cells = ['<div></div>'];
  DATA.cols.forEach(c => cells.push(`<div class="hcell">${c}</div>`));
  v.rows.forEach((r,i) => {
    const hint = v.hints[r] ? ` title="${v.hints[r]}"` : '';
    cells.push(`<div class="rcell"${hint}>${r}</div>`);
    v.cells[i].forEach((keys,j) => {
      const n = keys.length;
      if(!n){ cells.push('<div class="tile gap"></div>'); return; }
      const yrs = keys.map(k => DATA.years[k]).filter(Boolean);
      const span = yrs.length ? `${Math.min(...yrs)}–${Math.max(...yrs)}` : '';
      const pin = pinned && pinned[0]===i && pinned[1]===j ? ' pinned' : '';
      cells.push(`<div class="tile${pin}" style="background:${heat(n)}"
        onclick="pin(${i},${j})"><div class="n">${n}</div><div class="yr">${span}</div></div>`);
    });
  });
  grid.innerHTML = cells.join('');
  const d = document.getElementById('detail');
  if(pinned){
    const [i,j] = pinned, keys = v.cells[i][j];
    d.innerHTML = `<b>${v.rows[i]}</b> × <b>${DATA.cols[j]}</b> — ${keys.length} paper(s)
      <div class="keys">${keys.map(k=>`<span class="key">${k} <span style="color:var(--mut)">${DATA.years[k]||''}</span></span>`).join('')}</div>`;
  } else {
    d.innerHTML = '<span style="color:var(--mut)">Click a tile to pin its paper list here.</span>';
  }
}
function pin(i,j){ pinned = (pinned && pinned[0]===i && pinned[1]===j) ? null : [i,j]; render(); }
function setView(v){ view = v; pinned = null;
  document.getElementById('bg').classList.toggle('on', v==='graph');
  document.getElementById('br').classList.toggle('on', v==='role'); render(); }
window.onload = render;
"""
    js = js.replace("__DATA__", json.dumps(data))

    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>selib — periodic table of structural-entropy methods</title>
<style>{css}</style></head><body>
<h1>A periodic table of structural-entropy methods</h1>
<p class="sub">Generated from the survey's <b>{n_total} tagged papers</b> (1,297 verified
facet tags). Heat = paper count; a dashed tile is an <b>open direction</b>. Click any tile
for its papers.
<a href="index.html">← benchmark</a> · <a href="gallery.html">gallery</a> ·
<a href="tutorial.html">tutorial</a> · <a href="maps.html">more maps</a> ·
<a href="https://github.com/SuuTTT/structural-entropy-survey-paper">survey</a></p>

<div class="toggle">
  <button id="bg" class="on" onclick="setView('graph')">graph type × direction</button>
  <button id="br" onclick="setView('role')">role of SE × direction</button>
</div>
<div class="legend">The role view mirrors the journal paper's role taxonomy: hover a row
label for what the role means. Year range inside each tile = first–latest paper.</div>

<div id="grid" class="grid"></div>
<div id="detail"></div>

<h2>{html.escape(pi['title'])}</h2>
<div class="note">{html.escape(pi['body'])}</div>

<h2>Open directions surfaced by the table</h2>
<ul>{opens}</ul>

<div class="foot">Data-driven from the survey's facet tags (results/facet_tags.jsonl); a blank
tile means no paper in the corpus was tagged there (not proof of non-existence). Empty
columns for <b>signed</b> and <b>bipartite</b> graphs, and sparse hypergraph / directed rows,
map the frontier.</div>
<script>{js}</script>
</body></html>"""
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "periodic.html"), "w") as f:
        f.write(page)
    for extra in ("se_periodic.json", "facet_tags.jsonl"):
        src = os.path.join(RES, extra)
        if os.path.exists(src):
            open(os.path.join(OUT, extra), "w").write(open(src).read())
    print(f"wrote {OUT}/periodic.html (2 views, {n_total} papers)")


if __name__ == "__main__":
    main()
