"""selib — a standardized library for structural entropy: compute it, optimize it,
and benchmark SE methods against baselines under one API.

v0.1 focus: a uniform `Method` interface over community-detection algorithms (SE
methods + classical baselines), a native SE core (encoding tree, 2D-SE, Dasgupta
cost), shared datasets/metrics, and a one-call benchmark. Deep-learning SE methods
are wrapped over their original code; the native SE core is the seed of a fuller
encoding-tree + differentiable-SE engine to come.

Quick start:
    import selib
    selib.list_methods()                  # available algorithms
    recs = selib.benchmark(["louvain", "se_agglomerative"], ["Karate", "SBM-Clean"])
    selib.summarize(recs, "nmi")
"""
from . import metrics, datasets, se                                   # noqa: F401
from .base import (Method, get, info, register, method,               # noqa: F401
                   methods as list_methods, ExternalNotConfigured)
from .benchmark import benchmark, summarize                           # noqa: F401
from . import methods                                                 # noqa: F401  (self-registers algorithms)

__version__ = "0.2.0"
