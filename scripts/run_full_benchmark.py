"""Full selib benchmark — the run that backs the project page.

Three blocks, all scored uniformly via selib:
  1. Real graphs + controlled SBM  (Karate, Football, SBM-Clean, SBM-Noisy)
  2. LFR mixing-parameter sweep     (the canonical community-detection difficulty axis)
  3. SBM scalability sweep          (constant per-node signal as N grows; records wall-clock)

Every record carries external accuracy (ARI/NMI), cross-objective values
(modularity / map-equation / 2D structural entropy / #communities) and runtime,
so SE methods and baselines are on the same footing. Output: results JSON only —
no number is typed by hand.
"""
import json, os, time
import selib
from selib import datasets as D, metrics as M, get

METHODS = ["louvain", "leiden", "infomap", "spectral", "se_agglomerative", "se_louvain"]


def datasets_block():
    block = {}
    block["real_and_sbm"] = [
        ("Karate", D.karate),
        ("Football", D.football),
        ("SBM-Clean", lambda: D.sbm(150, 3, 0.30, 0.05)),
        ("SBM-Noisy", lambda: D.sbm(150, 3, 0.15, 0.08)),
    ]
    block["lfr_sweep"] = [
        (f"LFR-mu{mu:.1f}", (lambda mu=mu: D.lfr(n=500, mu=mu, seed=0)))
        for mu in (0.1, 0.2, 0.3, 0.4, 0.5, 0.6)
    ]
    block["scalability"] = [
        (f"SBM-scale-N{N}", (lambda N=N: D.sbm_scalable(n=N, k=10)))
        for N in (200, 500, 1000, 2000)
    ]
    return block


def run(items, seeds):
    recs = []
    for name, loader in items:
        try:
            G, gt = loader()
        except Exception as e:
            print(f"[skip dataset {name}] {e}", flush=True); continue
        k = len(set(gt))
        meta = {"n": G.number_of_nodes(), "m": G.number_of_edges(), "k_true": k}
        for mn in METHODS:
            m = get(mn)
            for s in seeds:
                t0 = time.perf_counter()
                try:
                    pred = m.fit_predict(G, k=k, seed=s)
                except Exception as e:
                    print(f"[err {mn}/{name}] {e}", flush=True); break
                dt = time.perf_counter() - t0
                rec = {"method": mn, "is_se": m.is_se, "dataset": name, "seed": s,
                       "time_s": round(dt, 4), "ari": M.ari(gt, pred), "nmi": M.nmi(gt, pred)}
                rec.update({kk: (round(vv, 6) if isinstance(vv, float) else vv)
                            for kk, vv in M.cross_objective(G, pred).items()})
                rec.update(meta)
                recs.append(rec)
                if not m.native or mn == "se_agglomerative":  # deterministic: one seed
                    break
        print(f"[done {name}] n={meta['n']} m={meta['m']}", flush=True)
    return recs


def main():
    os.makedirs("results", exist_ok=True)
    blocks = datasets_block()
    records = []
    records += run(blocks["real_and_sbm"], seeds=(0, 1, 2, 3, 4))
    records += run(blocks["lfr_sweep"], seeds=(0, 1, 2, 3, 4))
    records += run(blocks["scalability"], seeds=(0, 1, 2))
    out = {
        "selib_version": selib.__version__,
        "methods": METHODS,
        "block_membership": {b: [n for n, _ in items] for b, items in blocks.items()},
        "records": records,
    }
    with open("results/benchmark_results.json", "w") as f:
        json.dump(out, f, indent=2)
    print(f"WROTE results/benchmark_results.json with {len(records)} records", flush=True)


if __name__ == "__main__":
    main()
