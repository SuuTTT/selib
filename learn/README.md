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

## Resolution behavior — SE vs modularity (the duality)

`min_se_resolution.py` on ring-of-cliques (Fortunato-Barthelemy 2007), clique size 5,
truth = one community per clique:

| r (cliques) | louvain | leiden | free-k SE | se_fixed_k |
|---|---|---|---|---|
| 8  | 1.00 | 1.00 | 1.00 | 1.00 |
| 24 | 0.62 (13 found) | 0.62 | **1.00 (24)** | 0.94 |
| 32 | 0.63 (18) | 0.63 | **1.00 (32)** | 0.91 |
| 48 | 0.53 (21) | 0.55 | **1.00 (48)** | 0.87 |

**Modularity has a resolution limit — it merges adjacent cliques as r grows
(13/18/21 found instead of 24/32/48). Free-k SE does NOT: it recovers every
clique (ARI 1.0).** So SE's resolution behavior is the *opposite* of
modularity's. The over-resolution failure of SE (seen on noisy attributed
graphs like Cora: 338 communities) is therefore regime-specific, not a
universal flaw — on clean planted structure SE is the one that gets resolution
right where modularity fails. (Here se_fixed_k is slightly noisier than free-k
because free-k is already exactly correct; fixed-k helps in the *opposite*
regime, where free-k over-segments.)

**K-constrained SE** (`se_optimize_fixed_k`, ported from
[se-label-alignment](https://github.com/SuuTTT/se-label-alignment) SE-HybridK)
is now a first-class selib optimizer. Validated against the sealgo reference on
LFR-mu0.3 (K=10): selib H2=6.122 / ARI .832 vs reference H2=6.131 / ARI .808 —
agreement within multistart noise (selib reached marginally lower SE).
It does NOT rescue the GSL downstream null (Cora se_k102 .797 vs original .808),
which strengthens P2: the GSL null is not just over-segmentation.

## Backend ablation (2026-06-12): se vs louvain/leiden/infomap vs random

Every host method can swap its structure-finder (`--cluster`, see `backends.py`).
Results so far (Cora/LFR/four-rooms, A4000):

| host method | se | se_k (matched k) | louvain | leiden | infomap | random_matched |
|---|---|---|---|---|---|---|
| flat CD, LFR-mu0.1 (ARI) | .894 | — | .992 | .996 | **.997** | -.003 |
| flat CD, LFR-mu0.4 (ARI / NMI) | .182 / **.463** | — | .255 / .385 | **.294** / .435 | .200 / .409 | ~0 |
| hierarchy (Dasgupta, 3 families) | **wins all** | — | — | — | — | — |
| GSL rewiring (Cora Δacc) | −0.3 | −0.6 | **+0.7 (8-seed, real)** | 0.0 | — | **−7.0** |
| contrastive views (Cora Δacc) | −0.6 | — | −0.4 | — | — | −0.1 |
| exploration (four-rooms) | null | — | null | — | — | — |
| SI2E DoorKey (success) | .96 | — | — | — | — | .96 |

Cross-reference: [fastsi2e](https://github.com/SuuTTT/fastsi2e) ran the same swap
inside full SI2E on the HARD env: **infomap 95.3±4.6 / leiden 95.1±9.8 beat the SE
PartitionTree 67.5±27.9 on KeyCorridorS3R2, at 3-4× speed** (k-means matches on
DoorKey at 4× — our independent GPU k-means backend measures 4.3×).

Reading: (i) SE always attains the lowest 2D-SE — selib optimizes its objective
best; label misalignment, not optimization, explains flat-CD losses. (ii) SE wins
where the *hierarchy* is the product. (iii) In host methods, the difference among
reasonable partitioners is small (and SE's free-k over-segmentation hurts —
constraining k removes the deficit but doesn't create a gain); only *incoherent*
structure (random) is catastrophic where the partition edits data (GSL). (iv) On
hard RL exploration, flow-based clustering (infomap) currently beats the SE tree.

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
