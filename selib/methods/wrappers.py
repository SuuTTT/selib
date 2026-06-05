"""Drop-in wrappers over published SE methods' ORIGINAL code.

These run each paper's actual implementation (jar / C++ binary / python repo).
selib does not bundle the upstream code; configure the path via environment
variables (or selib.config). If unset, the wrapper raises ExternalNotConfigured
with the repo URL, so the API is uniform whether or not the upstream is present.
Per-method modernization patches are documented in the survey's repro cards.
"""
from __future__ import annotations
import os, subprocess, tempfile
import networkx as nx
from ..base import method, ExternalNotConfigured
from .. import datasets as D


def _need(env, repo):
    p = os.environ.get(env)
    if not p or not os.path.exists(p):
        raise ExternalNotConfigured(
            f"set ${env} to the upstream artifact. Repo: {repo}")
    return p


@method("dedoc", family="community_detection", is_se=True, native=False,
        paper="Li et al. 2018", repo="https://github.com/yinxc/structural-information-minimisation",
        note="founding SE minimization (Java jar); set $SELIB_DEDOC_JAR")
def dedoc(G, k=None, seed=0, variant="E"):
    jar = _need("SELIB_DEDOC_JAR", "github.com/yinxc/structural-information-minimisation")
    n = G.number_of_nodes()
    with tempfile.TemporaryDirectory() as td:
        gp = os.path.join(td, "g")
        D.to_dedoc(G, gp)
        subprocess.run(["java", "-jar", jar, gp], cwd=td, check=True,
                       capture_output=True, timeout=900)
        res = next((os.path.join(td, f) for f in os.listdir(td) if "deDoc" in f), None)
        labels = [-1] * n
        for cid, line in enumerate(l for l in open(res) if l.strip()):
            for tok in line.split():
                v = int(float(tok)) - 1
                if 0 <= v < n:
                    labels[v] = cid
        nxt = max(labels) + 1
        for i in range(n):
            if labels[i] == -1:
                labels[i] = nxt; nxt += 1
        return labels


@method("codeseg", family="community_detection", is_se=True, native=False,
        paper="Xian et al. WWW 2025", repo="https://github.com/SELGroup/CoDeSEG",
        note="SE-game community detection (C++ binary); set $SELIB_CODESEG_BIN")
def codeseg(G, k=None, seed=0, tau="0.3"):
    binp = _need("SELIB_CODESEG_BIN", "github.com/SELGroup/CoDeSEG")
    n = G.number_of_nodes()
    with tempfile.TemporaryDirectory() as td:
        ein, gt, out = (os.path.join(td, x) for x in ("e", "gt", "o"))
        D.to_edgelist(G, ein, one_based=True, sep="\t")
        D.to_communities_file([0] * n, gt, one_based=True)
        subprocess.run([binp, "-i", ein, "-o", out, "-n", "10", "-t", gt,
                        "-e", tau, "-p", "1"], check=True, capture_output=True, timeout=600)
        return D.communities_file_to_labels(out, n, one_based=True)


# NOTE: deep-learning SE methods (LSENet, DeSE, SEP, SE-GSL, SEGA, SI2E) wrap a
# python repo + its own (modernized) environment; they are exposed the same way
# via $SELIB_<NAME>_DIR once their env is set up. See the survey repro cards for
# the exact commits and patches. These are stubs to be filled as envs are pinned.
