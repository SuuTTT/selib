"""docs/periodic.html — a DATA-DRIVEN periodic table of structural-entropy methods,
generated from the survey's facet tags (results/facet_tags.jsonl, 81 core papers),
so every cell reflects the actual literature. graph type (rows) x research direction
(cols); each cell shows the count + the paper keys; blank = open direction. The
curated open-directions + node-distribution note come from results/se_periodic.json.
"""
import json, os, html
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
OUT = os.path.join(ROOT, "docs")

GRAPH_ORDER = ["simple", "weighted", "directed", "bipartite", "signed", "attributed",
               "heterogeneous", "hypergraph", "dynamic"]
TASK_ORDER = ["theory", "community_detection", "hierarchical_clustering", "graph_pooling",
              "structure_learning", "contrastive_ssl", "rl_abstraction", "application"]
TASK_LABEL = {"theory": "theory/def", "community_detection": "community det.",
              "hierarchical_clustering": "hierarchy", "graph_pooling": "pooling",
              "structure_learning": "structure learn.", "contrastive_ssl": "contrastive",
              "rl_abstraction": "RL abstraction", "application": "applications"}


def load():
    gt = defaultdict(set); tk = defaultdict(set)
    for l in open(os.path.join(RES, "facet_tags.jsonl")):
        r = json.loads(l)
        if r["facet"] == "graph_type":
            gt[r["value"]].add(r["key"])
        elif r["facet"] == "task":
            tk[r["value"]].add(r["key"])
    return gt, tk


def main():
    gt, tk = load()
    se = json.load(open(os.path.join(RES, "se_periodic.json")))
    allkeys = set().union(*gt.values()) if gt else set()
    n_total = len(allkeys)

    th = "".join(f"<th>{html.escape(TASK_LABEL.get(t,t))}</th>" for t in TASK_ORDER)
    rows = ""; n_fill = 0; n_cells = 0
    for g in GRAPH_ORDER:
        tds = ""
        for t in TASK_ORDER:
            n_cells += 1
            keys = sorted(gt.get(g, set()) & tk.get(t, set()))
            if keys:
                n_fill += 1
                lab = "<br>".join(html.escape(k) for k in keys[:6]) + (f"<br>+{len(keys)-6} more" if len(keys) > 6 else "")
                tds += f'<td class="hit" title="{len(keys)} papers"><b>{len(keys)}</b><div class="ks">{lab}</div></td>'
            else:
                tds += '<td class="gap">·</td>'
        rows += f'<tr><th class="rowh">{html.escape(g)}</th>{tds}</tr>'

    opens = "".join(f"<li>{html.escape(o)}</li>" for o in se["open_directions"])
    pi = se["pi_note"]
    css = """
    :root{--fg:#1f2937;--mut:#6b7280;--bd:#e5e7eb;--se:#e0245e;--hit:#ecfdf5;--hitbd:#86efac;--gap:#fef2f2}
    *{box-sizing:border-box}
    body{font:16px/1.5 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:var(--fg);max-width:1180px;margin:0 auto;padding:32px 20px 80px}
    h1{font-size:30px;margin:0 0 4px} h2{font-size:21px;margin:34px 0 8px;border-bottom:2px solid var(--bd);padding-bottom:6px} a{color:#2563eb}
    .sub{color:var(--mut);margin:0 0 8px}
    .tablewrap{overflow-x:auto}
    table{border-collapse:collapse;width:100%;font-size:11.5px;margin-top:10px}
    th,td{border:1px solid var(--bd);padding:5px 7px;vertical-align:top;text-align:left}
    thead th{background:#f9fafb} th.rowh{background:#f9fafb;min-width:108px}
    td.hit{background:var(--hit);border-color:var(--hitbd)} td.hit b{font-size:14px}
    td.gap{background:var(--gap);color:#fca5a5;text-align:center;font-size:16px;vertical-align:middle}
    .ks{color:#475569;font-size:10px;margin-top:3px;line-height:1.25}
    .legend{margin:10px 0;font-size:13px;color:var(--mut)} .sw{display:inline-block;width:12px;height:12px;border-radius:3px;vertical-align:middle;margin:0 4px 0 12px}
    .note{background:#f9fafb;border:1px solid var(--bd);border-radius:10px;padding:14px 18px;margin:14px 0}
    code{background:#f3f4f6;padding:2px 6px;border-radius:5px;font-size:13.5px}
    .foot{color:var(--mut);font-size:13px;margin-top:34px;border-top:1px solid var(--bd);padding-top:14px}
    """
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>selib — periodic table of structural-entropy methods</title>
<style>{css}</style></head><body>
<h1>A periodic table of structural-entropy methods</h1>
<p class="sub">Graph type &times; research direction, generated from the survey's
<b>{n_total} tagged papers</b>. Each cell shows the count and the paper keys; a blank cell
is an <b>open direction</b>.
<a href="index.html">← benchmark</a> · <a href="gallery.html">gallery</a> ·
<a href="tutorial.html">tutorial</a> · <a href="recursive.html">recursive</a> ·
<a href="maps.html"><b>more maps</b></a> ·
<a href="https://github.com/SuuTTT/structural-entropy-survey-paper">survey</a></p>
<div class="legend"><span class="sw" style="background:var(--hit);border:1px solid var(--hitbd)"></span>has work
<span class="sw" style="background:var(--gap)"></span>open ({n_cells - n_fill} of {n_cells} cells)</div>

<div class="tablewrap"><table><thead><tr><th>graph type</th>{th}</tr></thead>
<tbody>{rows}</tbody></table></div>
<p class="sub">This is one projection; the <a href="maps.html">maps page</a> has the top-10
row×col cuts, a method genealogy, and a phase diagram of when each direction emerged.</p>

<h2>{html.escape(pi['title'])}</h2>
<div class="note">{html.escape(pi['body'])}</div>

<h2>Open directions surfaced by the table</h2>
<ul>{opens}</ul>

<div class="foot">Data-driven from the survey's facet tags (results/facet_tags.jsonl); a blank
cell means no paper in the corpus was tagged there (not proof of non-existence). Whole empty
columns for <b>signed</b> and <b>bipartite</b> graphs, and sparse hypergraph / directed rows,
map the frontier.</div>
</body></html>"""
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "periodic.html"), "w") as f:
        f.write(page)
    for extra in ("se_periodic.json", "facet_tags.jsonl"):
        src = os.path.join(RES, extra)
        if os.path.exists(src):
            open(os.path.join(OUT, extra), "w").write(open(src).read())
    print(f"wrote {OUT}/periodic.html (data-driven; {n_fill}/{n_cells} cells, {n_total} papers)")


if __name__ == "__main__":
    main()
