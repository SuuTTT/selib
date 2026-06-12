# selib/learn — minimal single-file SE learning methods

clean-rl-style implementations: **one file = one method**, no framework, every
file imports `selib` for the structural-entropy core (validated to machine
precision against independent implementations). Read top-to-bottom in one
sitting; run with one command; numbers print to stdout.

| file | idea | paper it distills | status |
|---|---|---|---|
| `min_se_uq.py` | LLM uncertainty = min 2D SE of the semantic graph over sampled answers | SeSE (UAI 2026) | ✅ runs |
| `min_sep_pooling.py` | graph classification with SE coding-tree pooling | SEP (ICML 2022) | planned |
| `min_se_exploration.py` | RL exploration bonus from SE of the state-transition graph | SI2E (2024) | planned |
| `min_se_gsl.py` | graph structure learning: rewire by SE-minimal skeleton | SE-GSL (WWW 2023) | planned |

Conventions:
- ≤ ~150 lines per file, stdlib + numpy/networkx/torch + selib only.
- No config files; argparse with defaults that reproduce a headline number.
- Each file's docstring states the one-sentence idea and the source paper.
