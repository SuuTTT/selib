"""Cross-check selib's 2D structural entropy against independent implementations:
  (1) glass-jax's discrete StructuralEntropyScorer (separate code path),
  (2) the original deDoc (Java) printed 2D structural entropy for its own partition,
  (3) the published CoDeSEG (C++) printed entropy for its own partition.
Covers connected, DISCONNECTED, and weighted graphs. Writes results/se_crosscheck.json.

Env: GLASSJAX_ENTROPY=/path/to/entropy.py, SELIB_DEDOC_JAR, SELIB_CODESEG_BIN.
"""
import json, os, math, random, subprocess, tempfile, importlib.util
import numpy as np
import networkx as nx
from selib import metrics as M, datasets as D


def load_glassjax():
    p = os.environ.get("GLASSJAX_ENTROPY", "/root/glassjax_entropy.py")
    if not os.path.exists(p):
        return None
    import sys
    spec = importlib.util.spec_from_file_location("gj_entropy", p)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["gj_entropy"] = mod          # dataclasses need the module registered
    spec.loader.exec_module(mod)
    return mod


def random_graphs():
    cases = []
    for s in range(40):
        n = random.randint(8, 60)
        G = nx.convert_node_labels_to_integers(nx.gnp_random_graph(n, random.uniform(0.08, 0.4), seed=s))
        k = random.randint(1, 6)
        labels = [random.randrange(k) for _ in range(n)]
        cases.append(("gnp", G, labels))
    # explicitly DISCONNECTED graphs
    for s in range(10):
        G = nx.disjoint_union_all([nx.gnp_random_graph(random.randint(4, 12), 0.4, seed=s * 7 + i)
                                   for i in range(random.randint(2, 4))])
        G = nx.convert_node_labels_to_integers(G)
        labels = [random.randrange(3) for _ in range(G.number_of_nodes())]
        cases.append(("disconnected", G, labels))
    # WEIGHTED graph
    for s in range(8):
        G = nx.convert_node_labels_to_integers(nx.gnp_random_graph(random.randint(10, 30), 0.3, seed=100 + s))
        for u, v in G.edges():
            G[u][v]["weight"] = random.uniform(0.5, 4.0)
        labels = [random.randrange(4) for _ in range(G.number_of_nodes())]
        cases.append(("weighted", G, labels))
    return cases


def check_glassjax(out, gj):
    if gj is None:
        out["glassjax"] = {"available": False}
        return
    maxdiff = 0.0; worst = None
    for kind, G, labels in random_graphs():
        A = nx.to_numpy_array(G, weight="weight")
        gj_val = gj.StructuralEntropyScorer.from_adjacency(A).score(labels)
        se_val = M.structural_entropy_2d(G, labels)
        d = abs(gj_val - se_val)
        if d > maxdiff:
            maxdiff = d; worst = {"kind": kind, "n": G.number_of_nodes(),
                                  "selib": round(se_val, 9), "glassjax": round(gj_val, 9)}
    out["glassjax"] = {"available": True, "trials": 58, "max_abs_diff": maxdiff, "worst": worst}
    print(f"[glass-jax] 58 trials (incl. disconnected+weighted): max abs diff = {maxdiff:.3e}", flush=True)


def run_dedoc_and_compare(out):
    jar = os.environ.get("SELIB_DEDOC_JAR")
    if not jar or not os.path.exists(jar):
        out["dedoc"] = {"available": False}; return
    recs = []
    for name, G in (("Karate", D.karate()[0]), ("SBM-Clean", D.sbm(120, 3, 0.3, 0.05)[0])):
        G = nx.convert_node_labels_to_integers(G)
        with tempfile.TemporaryDirectory() as td:
            gp = os.path.join(td, "g")
            D.to_dedoc(G, gp)
            r = subprocess.run(["java", "-jar", jar, gp], cwd=td, capture_output=True, text=True, timeout=300)
            printed = None
            for tok in (r.stdout + " " + r.stderr).replace("=", " ").split():
                try:
                    printed = float(tok)
                except ValueError:
                    pass  # keep last parseable float (deDoc prints the 2D-nSE)
            res = next((os.path.join(td, f) for f in os.listdir(td) if "deDoc" in f), None)
            labels = D.communities_file_to_labels(res, G.number_of_nodes(), one_based=True) if res else None
        if labels is None:
            continue
        se_selib = M.structural_entropy_2d(G, labels)
        h1 = -sum((d / sum(dict(G.degree(weight='weight')).values())) *
                  math.log2(d / sum(dict(G.degree(weight='weight')).values()))
                  for d in dict(G.degree(weight='weight')).values() if d > 0)
        recs.append({"dataset": name, "dedoc_printed": printed,
                     "selib_H2_of_dedoc_partition": round(se_selib, 6),
                     "selib_H1": round(h1, 6),
                     "ratio_printed_over_H2": round(printed / se_selib, 4) if (printed and se_selib) else None})
        print(f"[deDoc] {name}: printed={printed} selib H2(partition)={se_selib:.6f} H1={h1:.6f}", flush=True)
    out["dedoc"] = {"available": True, "records": recs,
                    "note": "deDoc prints a 2D structural-entropy value for ITS partition; "
                            "we recompute selib's H2 of the same partition to confirm the definition matches "
                            "(up to deDoc's normalization)."}


def run_codeseg_and_compare(out):
    binp = os.environ.get("SELIB_CODESEG_BIN")
    if not binp or not os.path.exists(binp):
        out["codeseg"] = {"available": False}; return
    recs = []
    for name, G in (("Karate", D.karate()[0]), ("SBM-Clean", D.sbm(120, 3, 0.3, 0.05)[0])):
        G = nx.convert_node_labels_to_integers(G)
        n = G.number_of_nodes()
        with tempfile.TemporaryDirectory() as td:
            ein, gt, o = (os.path.join(td, x) for x in ("e", "gt", "o"))
            D.to_edgelist(G, ein, one_based=True, sep="\t")
            D.to_communities_file([0] * n, gt, one_based=True)
            r = subprocess.run([binp, "-i", ein, "-o", o, "-n", "10", "-t", gt, "-e", "0.3", "-p", "1", "-v"],
                               capture_output=True, text=True, timeout=300)
            printed = None
            for line in (r.stdout + r.stderr).splitlines():
                low = line.lower()
                if "entropy" in low or "nse" in low:
                    for tok in line.replace("=", " ").replace(":", " ").split():
                        try:
                            printed = float(tok)
                        except ValueError:
                            pass
            labels = D.communities_file_to_labels(o, n, one_based=True)
        se_selib = M.structural_entropy_2d(G, labels)
        recs.append({"dataset": name, "codeseg_printed_entropy": printed,
                     "selib_H2_of_codeseg_partition": round(se_selib, 6)})
        print(f"[CoDeSEG] {name}: printed={printed} selib H2(partition)={se_selib:.6f}", flush=True)
    out["codeseg"] = {"available": True, "records": recs}


def main():
    random.seed(0)
    os.makedirs("results", exist_ok=True)
    out = {}
    check_glassjax(out, load_glassjax())
    try:
        run_dedoc_and_compare(out)
    except Exception as e:
        out["dedoc"] = {"available": False, "error": str(e)}; print("dedoc err", e, flush=True)
    try:
        run_codeseg_and_compare(out)
    except Exception as e:
        out["codeseg"] = {"available": False, "error": str(e)}; print("codeseg err", e, flush=True)
    with open("results/se_crosscheck.json", "w") as f:
        json.dump(out, f, indent=2)
    print("WROTE results/se_crosscheck.json", flush=True)


if __name__ == "__main__":
    main()
