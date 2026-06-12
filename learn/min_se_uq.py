"""Minimal SeSE-style LLM uncertainty quantification with selib (~120 lines).

clean-rl philosophy: one file, one idea, no framework. Given N sampled answers
to a question, build a semantic graph (pairwise NLI entailment), minimize 2D
structural entropy over it with selib, and use the attained entropy as the
uncertainty score: a confident model concentrates its samples in one tight
semantic cluster (low SE); a hallucinating model scatters them (high SE).

Idea: SeSE (Zhao et al., UAI 2026). This is an independent minimal
re-implementation on selib's validated SE core — useful both as a tutorial
and as a cross-check of the official release.

Usage (offline re-scoring of a SeSE run_record):
  python min_se_uq.py --generations validation_generations.pkl \
                      --labels uncertainty_measures.json --out rescored.json
Inputs: the pickle maps id -> {question, responses: [(text, ...), ...]};
labels JSON provides validation_is_false (1 = greedy answer judged wrong).
"""
import argparse
import json
import pickle

import numpy as np
import networkx as nx
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from selib.seopt import se_optimize
from selib.metrics import structural_entropy_2d

NLI_MODEL = "microsoft/deberta-v2-xlarge-mnli"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


def entailment_matrix(texts, tok, nli, batch_size=64):
    """Symmetric semantic-similarity matrix: mean of both-direction entailment."""
    n = len(texts)
    pairs = [(i, j) for i in range(n) for j in range(n) if i != j]
    probs = np.zeros((n, n))
    for s in range(0, len(pairs), batch_size):
        chunk = pairs[s : s + batch_size]
        enc = tok([(texts[i], texts[j]) for i, j in chunk],
                  padding=True, truncation=True, return_tensors="pt").to(DEVICE)
        with torch.no_grad():
            logits = nli(**enc).logits
        p = torch.softmax(logits, dim=1)[:, 2].cpu().numpy()  # mnli: 2 = entailment
        for (i, j), v in zip(chunk, p):
            probs[i, j] = v
    return (probs + probs.T) / 2.0


def semantic_se(texts, question, tok, nli, eps=0.05):
    """Min 2D structural entropy (bits, >= 0) of the question-conditioned
    semantic graph. Higher = more scattered semantic space = more uncertain."""
    texts = [f"{question} {t}" for t in texts]
    W = entailment_matrix(texts, tok, nli)
    W[W < eps] = 0.0  # drop noise edges; keeps the measure scale-free
    G = nx.Graph()
    G.add_nodes_from(range(len(texts)))
    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            if W[i, j] > 0:
                G.add_edge(i, j, weight=float(W[i, j]))
    if G.number_of_edges() == 0:  # all answers mutually unrelated: max scatter
        return float(np.log2(max(len(texts), 2))), len(texts)
    labels = se_optimize(G, seed=0)
    return structural_entropy_2d(G, labels), len(set(labels))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--generations", required=True)
    ap.add_argument("--labels", required=True)
    ap.add_argument("--out", default="rescored.json")
    args = ap.parse_args()

    tok = AutoTokenizer.from_pretrained(NLI_MODEL)
    nli = AutoModelForSequenceClassification.from_pretrained(NLI_MODEL).to(DEVICE).eval()

    gens = pickle.load(open(args.generations, "rb"))
    labels = json.load(open(args.labels))
    y_false = labels["validation_is_false"]

    scores, nclusters = [], []
    for tid, ex in gens.items():
        responses = [r[0] for r in ex["responses"]]
        h, k = semantic_se(responses, ex["question"], tok, nli)
        scores.append(h)
        nclusters.append(k)
        if len(scores) % 50 == 0:
            print(f"{len(scores)} scored", flush=True)

    from sklearn import metrics
    fpr, tpr, _ = metrics.roc_curve(y_false[: len(scores)], scores, pos_label=1)
    auroc = metrics.auc(fpr, tpr)
    print(f"selib min-2D-SE AUROC: {auroc:.4f}  (n={len(scores)})")
    json.dump({"auroc": auroc, "scores": scores, "n_clusters": nclusters},
              open(args.out, "w"))


if __name__ == "__main__":
    main()
