"""Smoke test: import selib, list methods, run a small benchmark, sanity-check it."""
import json
import selib


def test_smoke():
    print("selib", selib.__version__)
    names = selib.list_methods()
    print("methods:", names)
    for n in ("louvain", "leiden", "infomap", "spectral", "se_agglomerative"):
        assert n in names, f"missing {n}"

    recs = selib.benchmark(
        ["louvain", "leiden", "infomap", "spectral", "se_agglomerative"],
        ["Karate", "SBM-Clean", "SBM-Noisy"],
    )
    print("n_records", len(recs))
    assert recs, "no records produced"
    for r in recs:
        assert -0.5 <= r["nmi"] <= 1.0001
        assert "structural_entropy_2d" in r and "modularity" in r

    print("NMI\n", json.dumps(selib.summarize(recs, "nmi"), indent=2))
    print("SE-2D\n", json.dumps(selib.summarize(recs, "structural_entropy_2d"), indent=2))

    # info on an external (unconfigured) method must be listable without error
    print("dedoc info:", selib.info("dedoc"))
    print("DONE_OK")


if __name__ == "__main__":
    test_smoke()
