"""selib.segnn — attribute-aware SE: differentiable soft 2D structural entropy + a
tiny GCN encoder. Ported from the author's glass-jax prototype (objectives/
structural_entropy.py + models/gnn_se.py), with flax/optax replaced by pure jax +
a hand-rolled Adam so the only optional dependency is `jax` (CPU build is fine).

Pipeline: node features X (from G.graph["X"]; identity if absent) and adjacency A
-> logits = (ReLU(A @ (X W1 + b1))) W2 + b2 -> S = softmax(logits) -> minimize the
soft H^2(A, S) by gradient descent -> hard labels = argmax S.

The soft objective uses the identity (sum_i S_ji = 1):
  H^2 = -sum_k (g_k/2m) log2(V_k/2m)  +  H_1(G) + sum_k (V_k/2m) log2(V_k/2m)
so at a one-hot S it equals the canonical 2D-SE *exactly* (checked in __main__).
"""
from __future__ import annotations
import numpy as np
import networkx as nx


def _require_jax():
    try:
        import jax  # noqa: F401
        return True
    except Exception as e:
        raise RuntimeError(
            "se_gnn needs jax (CPU is fine): pip install jax  — " + str(e))


def soft_se2d(A, S, eps=1e-9):
    """Differentiable 2D structural entropy of soft assignment S (N,K). jax arrays."""
    import jax.numpy as jnp
    d = jnp.sum(A, axis=-1)
    two_m = jnp.sum(d)
    V = jnp.dot(d, S)                              # (K,) module volumes
    AS = jnp.dot(A, S)
    g = jnp.sum(S * (d[:, None] - AS), axis=0)     # (K,) module cuts
    p_vol = V / (two_m + eps)
    p_cut = g / (two_m + eps)
    term1 = -jnp.sum(p_cut * jnp.log2(jnp.clip(p_vol, eps, 1.0)))
    p = jnp.clip(d / (two_m + eps), eps, 1.0)
    h1 = -jnp.sum(p * jnp.log2(p))                 # 1D SE (constant in S)
    term2 = h1 + jnp.sum(p_vol * jnp.log2(jnp.clip(p_vol, eps, 1.0)))
    return term1 + term2


def se_gnn_fit(A, X, k, seed=0, hidden=32, iters=150, lr=0.01):
    """Train the GCN to minimize soft H^2; return (labels, final_loss)."""
    _require_jax()
    import jax
    import jax.numpy as jnp
    A_ = jnp.asarray(A, dtype=jnp.float32)
    X_ = jnp.asarray(X, dtype=jnp.float32)
    D = X_.shape[1]
    key = jax.random.PRNGKey(seed)
    k1, k2 = jax.random.split(key)
    params = {
        "W1": jax.random.normal(k1, (D, hidden)) * jnp.sqrt(2.0 / D),
        "b1": jnp.zeros(hidden),
        "W2": jax.random.normal(k2, (hidden, k)) * jnp.sqrt(2.0 / hidden),
        "b2": jnp.zeros(k),
    }

    def forward(p):
        h = jnp.maximum(jnp.dot(A_, jnp.dot(X_, p["W1"]) + p["b1"]), 0.0)
        return jnp.dot(h, p["W2"]) + p["b2"]

    def loss_fn(p):
        S = jax.nn.softmax(forward(p), axis=-1)
        return soft_se2d(A_, S)

    grad_fn = jax.jit(jax.value_and_grad(loss_fn))
    # hand-rolled Adam (keeps optax out of the deps)
    m = {kk: jnp.zeros_like(v) for kk, v in params.items()}
    v = {kk: jnp.zeros_like(vv) for kk, vv in params.items()}
    b1, b2, ae = 0.9, 0.999, 1e-8
    loss = None
    for t in range(1, iters + 1):
        loss, g = grad_fn(params)
        for kk in params:
            m[kk] = b1 * m[kk] + (1 - b1) * g[kk]
            v[kk] = b2 * v[kk] + (1 - b2) * g[kk] ** 2
            mh = m[kk] / (1 - b1 ** t)
            vh = v[kk] / (1 - b2 ** t)
            params[kk] = params[kk] - lr * mh / (jnp.sqrt(vh) + ae)
    labels = np.asarray(jax.numpy.argmax(forward(params), axis=-1))
    return labels, float(loss)


def se_gnn(G, k=None, seed=0, hidden=32, iters=150, lr=0.01):
    """Attribute-aware SE community detection. Features are read from
    G.graph["X"] (numpy array aligned with list(G.nodes())); identity features are
    used if absent (featureless mode = learnable per-node embedding).
    `k` is the number of communities (required in spirit; defaults to 8)."""
    nodes = list(G.nodes())
    n = len(nodes)
    A = nx.to_numpy_array(G, nodelist=nodes, weight="weight").astype("float32")
    X = G.graph.get("X")
    if X is None:
        X = np.eye(n, dtype="float32")
    labels, _ = se_gnn_fit(A, np.asarray(X, dtype="float32"), int(k or 8),
                           seed=seed, hidden=hidden, iters=iters, lr=lr)
    return [int(x) for x in labels]


# ----------------------------- self-tests -----------------------------------
def _selftest():
    import random
    from . import metrics as M
    _require_jax()
    import jax.numpy as jnp
    random.seed(0)

    print("== soft H^2 at one-hot S == canonical 2D-SE ==")
    for gi, G in enumerate([nx.karate_club_graph(),
                            nx.gnp_random_graph(40, 0.15, seed=1),
                            nx.connected_caveman_graph(4, 6)]):
        G = nx.convert_node_labels_to_integers(G)
        n = G.number_of_nodes()
        labels = [random.randrange(4) for _ in range(n)]
        A = nx.to_numpy_array(G).astype("float32")
        S = np.zeros((n, 4), dtype="float32")
        for i, l in enumerate(labels):
            S[i, l] = 1.0
        soft = float(soft_se2d(jnp.asarray(A), jnp.asarray(S)))
        hard = M.structural_entropy_2d(G, labels)
        ok = abs(soft - hard) < 1e-4
        print(f"  graph{gi}: soft={soft:.6f} canonical={hard:.6f} {'OK' if ok else 'MISMATCH'}")
        assert ok

    print("== training reduces soft H^2 (Karate, identity features) ==")
    G = nx.convert_node_labels_to_integers(nx.karate_club_graph())
    A = nx.to_numpy_array(G).astype("float32")
    X = np.eye(G.number_of_nodes(), dtype="float32")
    _, l_short = se_gnn_fit(A, X, k=2, seed=0, iters=1)
    _, l_full = se_gnn_fit(A, X, k=2, seed=0, iters=200)
    print(f"  loss iter1={l_short:.4f} -> iter200={l_full:.4f} "
          f"{'OK' if l_full < l_short - 1e-6 else 'NO-DECREASE'}")
    assert l_full < l_short - 1e-6
    print("ALL SEGNN SELFTESTS PASSED")


if __name__ == "__main__":
    _selftest()
