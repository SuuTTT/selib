# selib/learn — minimal single-file SE learning methods

clean-rl-style implementations: **one file = one method**, no framework, every
file imports `selib` for the structural-entropy core (validated to machine
precision against independent implementations). Read top-to-bottom in one
sitting; run with one command; numbers print to stdout.

| file | idea | paper it distills | status |
|---|---|---|---|
| `min_se_uq.py` | LLM uncertainty = min 2D SE of the semantic graph over sampled answers | SeSE (UAI 2026) | ✅ tested — beats semantic entropy on TriviaQA (.694 vs .669) and SVAMP (.774 vs .657) |
| `min_sep_pooling.py` | graph classification with one SE pooling stage (SE-optimal partition) | SEP (ICML 2022) | 🧪 testing (MUTAG 10-fold) |
| `min_se_exploration.py` | tabular RL: cluster-level novelty bonus on the SE-clustered transition graph | SI2E (NeurIPS 2024) | 🧪 testing (four-rooms, 3 bonus arms) |
| `min_se_gsl.py` | rewire: +intra-SE-community kNN edges, −low-sim cross edges, retrain GCN | SE-GSL (WWW 2023) | 🧪 testing (Cora) |
| `min_se_contrastive.py` | contrastive views: drop intra-community edges more, cross edges less | SEGA (ICML 2023) | 🧪 testing (Cora, vs uniform) |

Conventions:
- ≤ ~150 lines per file, stdlib + numpy/networkx/torch + selib only.
- No config files; argparse with defaults that reproduce a headline number.
- Each file's docstring states the one-sentence idea and the source paper.
