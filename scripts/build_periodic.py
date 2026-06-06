"""docs/periodic.html — a 'periodic table' of structural-entropy methods:
graph type x research direction, from results/se_periodic.json. Filled cells list
representative methods; blank cells are open directions."""
import json, os, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results", "se_periodic.json")
OUT = os.path.join(ROOT, "docs")


def main():
    d = json.load(open(RES))
    dirs = d["directions"]
    th = "".join(f"<th>{html.escape(x)}</th>" for x in dirs)
    rows, n_fill, n_cells = [], 0, 0
    for gt in d["graph_types"]:
        cells = []
        for col in dirs:
            n_cells += 1
            ms = gt["cells"].get(col, [])
            if ms:
                n_fill += 1
                inner = "<br>".join(html.escape(m) for m in ms)
                cells.append(f'<td class="hit">{inner}</td>')
            else:
                cells.append('<td class="gap">·</td>')
        rows.append(
            f'<tr><th class="rowh">{html.escape(gt["name"])}'
            f'<div class="pi">π = {html.escape(gt["pi"])}</div></th>{"".join(cells)}</tr>')
    opens = "".join(f"<li>{html.escape(o)}</li>" for o in d["open_directions"])
    pi = d["pi_note"]
    css = """
    :root{--fg:#1f2937;--mut:#6b7280;--bd:#e5e7eb;--se:#e0245e;--hit:#ecfdf5;--hitbd:#86efac;--gap:#fef2f2}
    *{box-sizing:border-box}
    body{font:16px/1.55 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:var(--fg);max-width:1180px;margin:0 auto;padding:32px 20px 80px}
    h1{font-size:30px;margin:0 0 4px} h2{font-size:21px;margin:34px 0 8px;border-bottom:2px solid var(--bd);padding-bottom:6px} a{color:#2563eb}
    .sub{color:var(--mut);margin:0 0 8px}
    .tablewrap{overflow-x:auto}
    table{border-collapse:collapse;width:100%;font-size:12.5px;margin-top:10px}
    th,td{border:1px solid var(--bd);padding:6px 8px;vertical-align:top}
    thead th{background:#f9fafb;text-align:left;position:sticky;top:0}
    th.rowh{background:#f9fafb;text-align:left;min-width:150px} .pi{color:var(--mut);font-weight:400;font-size:11px;margin-top:2px}
    td.hit{background:var(--hit);border-color:var(--hitbd)} td.gap{background:var(--gap);color:#fca5a5;text-align:center;font-size:16px}
    .legend{margin:10px 0;font-size:13px;color:var(--mut)} .sw{display:inline-block;width:12px;height:12px;border-radius:3px;vertical-align:middle;margin:0 4px 0 12px}
    .note{background:#f9fafb;border:1px solid var(--bd);border-radius:10px;padding:14px 18px;margin:14px 0}
    code{background:#f3f4f6;padding:2px 6px;border-radius:5px;font-size:13.5px}
    .foot{color:var(--mut);font-size:13px;margin-top:34px;border-top:1px solid var(--bd);padding-top:14px}
    """
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>selib — a periodic table of structural-entropy methods</title>
<style>{css}</style></head><body>
<h1>A periodic table of structural-entropy methods</h1>
<p class="sub">Graph type &times; research direction. Each filled cell lists representative
methods; a blank cell is an <b>open direction</b>.
<a href="index.html">← benchmark</a> · <a href="gallery.html">gallery</a> ·
<a href="tutorial.html">tutorial</a> · <a href="recursive.html">recursive</a> ·
<a href="https://github.com/SuuTTT/structural-entropy-survey-paper">survey</a></p>
<div class="legend"><span class="sw" style="background:var(--hit);border:1px solid var(--hitbd)"></span>has work
<span class="sw" style="background:var(--gap)"></span>open ({n_cells - n_fill} of {n_cells} cells)</div>

<div class="tablewrap"><table><thead><tr><th>graph type</th>{th}</tr></thead>
<tbody>{''.join(rows)}</tbody></table></div>

<h2>{html.escape(pi['title'])}</h2>
<div class="note">{html.escape(pi['body'])}</div>

<h2>Open directions surfaced by the table</h2>
<ul>{opens}</ul>

<div class="foot">Curated from the structural-entropy survey's bibliography (104 papers).
A blank cell means no work was found there in the survey, not a proof of non-existence —
but the pattern (whole empty columns for signed and bipartite graphs; sparse rows for
hypergraph / directed deep learning) maps the frontier. The node distribution π shown per
row is the convention each family uses; see the note above on generalizing it.</div>
</body></html>"""
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "periodic.html"), "w") as f:
        f.write(page)
    with open(os.path.join(OUT, "se_periodic.json"), "w") as f:
        json.dump(d, f, indent=2)
    print(f"wrote {OUT}/periodic.html — {n_fill}/{n_cells} cells filled, {n_cells-n_fill} open")


if __name__ == "__main__":
    main()
