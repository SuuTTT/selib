"""selib.benchmark — run a set of methods over a set of datasets, uniformly.

Returns tidy per-(method, dataset, seed) records with external accuracy (ARI/NMI)
and cross-objective values (modularity / map-equation / 2D-SE), so SE methods and
baselines are scored on the same footing.
"""
from __future__ import annotations
from typing import Iterable, Optional
from . import datasets as D, metrics as M
from .base import get, methods as list_methods, ExternalNotConfigured


def _load(spec):
    """spec: dataset name (in datasets.REGISTRY), an (G, labels) tuple, or a callable."""
    if isinstance(spec, tuple):
        return spec
    if callable(spec):
        return spec()
    return D.REGISTRY[spec]()


def benchmark(method_names: Optional[Iterable[str]] = None,
              datasets: Optional[Iterable] = None,
              seeds: Iterable[int] = (0, 1, 2, 3, 4),
              cross_objective: bool = True) -> list[dict]:
    method_names = list(method_names or list_methods(family="community_detection"))
    datasets = list(datasets or ["Karate", "SBM-Clean", "SBM-Noisy"])
    records = []
    for dspec in datasets:
        name = dspec if isinstance(dspec, str) else getattr(dspec, "__name__", "data")
        try:
            G, gt = _load(dspec)
        except Exception as e:
            print(f"[skip dataset {name}] {e}"); continue
        k = len(set(gt))
        for mn in method_names:
            m = get(mn)
            for s in seeds:
                try:
                    pred = m.fit_predict(G, k=k, seed=s)
                except ExternalNotConfigured as e:
                    print(f"[skip {mn} — external not configured] {e}"); break
                except Exception as e:
                    print(f"[err {mn}/{name}/seed{s}] {e}"); continue
                rec = {"method": mn, "is_se": m.is_se, "dataset": name, "seed": s,
                       "ari": M.ari(gt, pred), "nmi": M.nmi(gt, pred)}
                if cross_objective:
                    rec.update(M.cross_objective(G, pred))
                records.append(rec)
                # deterministic methods: one seed suffices
                if not m.native or mn in ("se_agglomerative", "dedoc", "codeseg"):
                    break
    return records


def summarize(records: list[dict], metric: str = "ari") -> dict:
    """{(dataset): {method: mean}} for a quick table."""
    from collections import defaultdict
    agg = defaultdict(lambda: defaultdict(list))
    for r in records:
        if r.get(metric) is not None:
            agg[r["dataset"]][r["method"]].append(r[metric])
    return {d: {m: sum(v) / len(v) for m, v in md.items()} for d, md in agg.items()}
