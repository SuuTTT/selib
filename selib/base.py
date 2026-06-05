"""selib.base — unified Method interface + registry.

Every clustering/community-detection algorithm (SE-based or baseline) is exposed
as a Method with a single `fit_predict(G) -> labels` call and metadata, so they
can be listed, compared, and benchmarked uniformly. External methods that wrap a
paper's original code declare their requirement and raise a clear error if the
upstream repo/binary is not configured.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, Optional
import networkx as nx

_REGISTRY: dict[str, "Method"] = {}


@dataclass
class Method:
    name: str
    fn: Callable                       # fn(G, k=None, seed=0) -> list[int] labels
    family: str = "community_detection"
    is_se: bool = False                # True for structural-entropy methods
    native: bool = True                # True = runs from pip deps; False = wraps external original code
    paper: str = ""
    repo: str = ""
    note: str = ""

    def fit_predict(self, G: nx.Graph, k: Optional[int] = None, seed: int = 0) -> list[int]:
        return self.fn(G, k=k, seed=seed)


def register(method: Method) -> Method:
    _REGISTRY[method.name] = method
    return method


def method(name, **meta):
    """Decorator: register a function `fn(G, k=None, seed=0)->labels` as a Method."""
    def deco(fn):
        register(Method(name=name, fn=fn, **meta))
        return fn
    return deco


def get(name: str) -> Method:
    if name not in _REGISTRY:
        raise KeyError(f"unknown method '{name}'. Available: {sorted(_REGISTRY)}")
    return _REGISTRY[name]


def methods(family: Optional[str] = None, se_only: bool = False,
            native_only: bool = False) -> list[str]:
    out = []
    for n, m in sorted(_REGISTRY.items()):
        if family and m.family != family:
            continue
        if se_only and not m.is_se:
            continue
        if native_only and not m.native:
            continue
        out.append(n)
    return out


def info(name: str) -> dict:
    m = get(name)
    return {"name": m.name, "family": m.family, "is_se": m.is_se,
            "native": m.native, "paper": m.paper, "repo": m.repo, "note": m.note}


class ExternalNotConfigured(RuntimeError):
    """Raised when a wrapper needs an upstream repo/binary that isn't set up."""
