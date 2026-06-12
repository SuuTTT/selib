# selib/learn — minimal single-file SE learning methods

clean-rl-style implementations: **one file = one method**, no framework, every
file imports `selib` for the structural-entropy core (validated to machine
precision against independent implementations). Read top-to-bottom in one
sitting; run with one command; numbers print to stdout.

| file | idea | paper it distills | status |
|---|---|---|---|
| `min_se_uq.py` | LLM uncertainty = min 2D SE of the semantic graph over sampled answers | SeSE (UAI 2026) | ✅ tested — beats semantic entropy on TriviaQA (.694 vs .669) and SVAMP (.774 vs .657) |
| `min_sep_pooling.py` | graph classification with one SE pooling stage (SE-optimal partition) | SEP (ICML 2022) | ✅ tested — MUTAG 10-fold **0.825 ± 0.067** (full SEP ≈ .85) |
| `min_se_exploration.py` | tabular RL: cluster-level novelty bonus on the SE-clustered transition graph | SI2E (NeurIPS 2024) | ⚠️ runs; **null** — cluster bonus solves four-rooms (ep 264) but trails plain count novelty (ep 204) |
| `min_se_gsl.py` | rewire: +intra-SE-community kNN edges, −low-sim cross edges, retrain GCN | SE-GSL (WWW 2023) | ⚠️ runs; **null** on Cora — rewired .799–.805 vs original .808 across 3 configs |
| `min_se_contrastive.py` | contrastive views: SE-guided edge-drop probabilities (both orientations tried) | SEGA (ICML 2023) | ⚠️ runs; **null** on Cora — SE-guided ≈ uniform (−0.5 ± 0.6 pt) |

**Findings note (2026-06-12, A4000 test campaign).** The three nulls are consistent
with each other and with our survey's SEP tree ablation: at *matched* corruption /
granularity rates, the SE-chosen structure (which edges, which clusters) adds little
over structure-agnostic controls in these minimal settings — the value concentrates
in the *granularity and hierarchy geometry* that SE determines, not the specific
membership. Caveat: these are deliberate minimal distills; the published methods add
machinery (iterative refinement, value conditioning, anchor hierarchies) that the
nulls do not speak to. `min_se_uq.py` and `min_sep_pooling.py` show the positive
cases: where the SE *quantity itself* is the signal (UQ) or the hierarchy feeds a
supervised learner (pooling), the minimal version already works.

Conventions:
- ≤ ~150 lines per file, stdlib + numpy/networkx/torch + selib only.
- No config files; argparse with defaults that reproduce a headline number.
- Each file's docstring states the one-sentence idea and the source paper.
