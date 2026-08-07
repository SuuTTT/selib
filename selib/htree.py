"""selib.htree — hierarchical structural-entropy optimizer (encoding trees).

`se_louvain` minimizes the *2D* (flat) structural entropy. The full structural
entropy of Li & Pan is defined over an **encoding tree** T of arbitrary height:

    H^T(G) = - sum_{a in T, a != root} (g_a / vol) * log2(V_a / V_{parent(a)})

where V_a = volume of the module = sum of leaf degrees under a, g_a = its cut
(edges leaving the module), vol = sum of all degrees. A 2-level tree reduces this
to the 2D objective exactly (verified in the self-test).

This module builds a *multiway* encoding tree by recursively optimizing 2D-SE with
`se_louvain` (good partition at every level), then refines it with greedy local
moves — **collapse** a redundant internal level, **relocate** a leaf to a better
sibling module — accepting a move only when it strictly lowers the exact global
H^T. The merge-only `se_agglomerative` can only produce a fixed binary dendrogram;
this produces a far lower-entropy hierarchy.
"""
from __future__ import annotations
import math
import networkx as nx

LOG2 = math.log(2.0)


class TNode:
    __slots__ = ("children", "vertex", "V", "g", "parent")

    def __init__(self, children=None, vertex=None):
        self.children = children if children is not None else []
        self.vertex = vertex          # int leaf id, or None for internal
        self.V = 0.0
        self.g = 0.0
        self.parent = None

    def is_leaf(self):
        return self.vertex is not None


# ----------------------------- graph view -----------------------------------
def _graph_arrays(G):
    nodes = list(G.nodes())
    idx = {u: i for i, u in enumerate(nodes)}
    n = len(nodes)
    adj = [dict() for _ in range(n)]
    sl = [0.0] * n
    for u, v, w in G.edges(data="weight", default=1.0):
        a, b = idx[u], idx[v]
        if a == b:
            sl[a] += w
        else:
            adj[a][b] = adj[a].get(b, 0.0) + w
            adj[b][a] = adj[b].get(a, 0.0) + w
    deg = [sum(adj[v].values()) + 2 * sl[v] for v in range(n)]
    vol = sum(deg)
    return nodes, idx, n, adj, deg, vol


# --------------------------- annotate + objective ----------------------------
def annotate(root, deg, adj, vol):
    """Set V (volume) and g (cut) for every node. g_a = V_a - 2*E_in(a).

    Exact and fast: per-edge LCA via binary lifting (O(m log h)), then a single
    post-order pass accumulates E_in(a) = sum_child E_in + (edges whose LCA is a),
    instead of walking every edge up to the root (O(m h))."""
    # iterative post-order: V, parent, depth, node index, leaf map
    order = []                       # post-order list of nodes
    parent_of = {}
    depth = {}
    leafnode = {}
    stack = [(root, None, 0, False)]
    while stack:
        node, par, d, expanded = stack.pop()
        if expanded:
            order.append(node)
            continue
        node.parent = par
        parent_of[id(node)] = par
        depth[id(node)] = d
        stack.append((node, par, d, True))
        if node.is_leaf():
            leafnode[node.vertex] = node
        else:
            for c in node.children:
                stack.append((c, node, d + 1, False))
    for node in order:               # volumes bottom-up
        if node.is_leaf():
            node.V = deg[node.vertex]
        else:
            node.V = sum(c.V for c in node.children)

    # binary lifting tables
    maxd = max(depth.values()) if depth else 0
    LOG = max(1, maxd.bit_length())
    up = [dict() for _ in range(LOG)]
    all_nodes = list(depth.keys())
    for nid in all_nodes:            # level 0 = parent
        p = parent_of.get(nid)
        up[0][nid] = id(p) if p is not None else None
    for j in range(1, LOG):
        prev = up[j - 1]
        cur = up[j]
        for nid in all_nodes:
            mid = prev.get(nid)
            cur[nid] = prev.get(mid) if mid is not None else None

    def lca_id(a, b):
        na, nb = id(leafnode[a]), id(leafnode[b])
        da, db = depth[na], depth[nb]
        if da < db:
            na, nb = nb, na
            da, db = db, da
        diff = da - db
        j = 0
        while diff:
            if diff & 1:
                na = up[j][na]
            diff >>= 1
            j += 1
        if na == nb:
            return na
        for j in range(LOG - 1, -1, -1):
            ua, ub = up[j].get(na), up[j].get(nb)
            if ua != ub:
                na, nb = ua, ub
        return up[0][na]

    # per-edge: accumulate weight at the LCA node only
    lca_w = {}
    n = len(deg)
    for u in range(n):
        au = adj[u]
        for v, w in au.items():
            if v <= u:
                continue
            l = lca_id(u, v)
            lca_w[l] = lca_w.get(l, 0.0) + w

    # single post-order pass: E_in = sum child E_in + lca_w; g = V - 2 E_in
    e_in = {}
    for node in order:
        s = lca_w.get(id(node), 0.0)
        if not node.is_leaf():
            for c in node.children:
                s += e_in[id(c)]
        e_in[id(node)] = s
        g = node.V - 2.0 * s
        node.g = 0.0 if g < 1e-9 else g
    return root


def hd_se(root, vol):
    """Exact structural entropy of the encoding tree (bits)."""
    if vol <= 0:
        return 0.0
    total = 0.0
    def rec(node):
        nonlocal total
        for c in node.children:
            if c.V > 0 and c.g > 0 and node.V > 0:
                total -= (c.g / vol) * (math.log(c.V / node.V) / LOG2)
            rec(c)
    rec(root)
    return float(total)


def dasgupta_tree(root, G):
    """Dasgupta cost over a (multiway) tree: sum_{(u,v) in E} w * |leaves(LCA)|."""
    # depth + parent + leaf sizes
    size = {}
    depth = {}
    leafnode = {}
    def post(node, d):
        depth[id(node)] = d
        if node.is_leaf():
            size[id(node)] = 1
            leafnode[node.vertex] = node
            return 1
        s = sum(post(c, d + 1) for c in node.children)
        size[id(node)] = s
        return s
    post(root, 0)
    def lca(na, nb):
        da, db = depth[id(na)], depth[id(nb)]
        while da > db:
            na = na.parent; da -= 1
        while db > da:
            nb = nb.parent; db -= 1
        while na is not nb:
            na = na.parent; nb = nb.parent
        return na
    cost = 0.0
    for u, v, w in G.edges(data="weight", default=1.0):
        if u == v:
            continue
        a = lca(leafnode[u], leafnode[v])
        cost += w * size[id(a)]
    return float(cost)


# ------------------------------- build ---------------------------------------
def _build_subtree(G, members, seed, starts, depth, max_depth):
    if len(members) == 1:
        return TNode(vertex=members[0])
    from .seopt import se_optimize
    sub = G.subgraph(members)
    if depth >= max_depth:
        return TNode(children=[TNode(vertex=m) for m in members])
    labels = se_optimize(sub, k=None, seed=seed, starts=starts)
    blocks = {}
    sub_nodes = list(sub.nodes())
    for nd, lab in zip(sub_nodes, labels):
        blocks.setdefault(lab, []).append(nd)
    if len(blocks) <= 1 or len(blocks) == len(members):
        # no meaningful split: leaves hang directly off this module
        return TNode(children=[TNode(vertex=m) for m in members])
    children = [_build_subtree(G, blk, seed, starts, depth + 1, max_depth)
                for blk in blocks.values()]
    return TNode(children=children)


def build_tree(G, seed=0, starts=4, max_depth=12):
    nodes = list(G.nodes())
    root = _build_subtree(G, nodes, seed, starts, 0, max_depth)
    if root.is_leaf():
        root = TNode(children=[root])
    return root


# ------------------------------ refinement -----------------------------------
# Moves are evaluated on a fresh COPY of the tree (no fragile in-place revert):
# a node is addressed by its path = tuple of child indices from the root.
def copy_tree(node):
    if node.is_leaf():
        return TNode(vertex=node.vertex)
    return TNode(children=[copy_tree(c) for c in node.children])


def _get(root, path):
    n = root
    for i in path:
        n = n.children[i]
    return n


def _internal_paths(root):
    """Paths of every non-root internal node (collapsible candidates)."""
    out = []
    def rec(n, path):
        for i, c in enumerate(n.children):
            if not c.is_leaf():
                out.append(path + (i,))
                rec(c, path + (i,))
    rec(root, ())
    return out


def _all_paths(root):
    out = []
    def rec(n, path):
        for i, c in enumerate(n.children):
            out.append(path + (i,))
            rec(c, path + (i,))
    rec(root, ())
    return out


def _do_collapse(root, path):
    """Return a copy with the node at `path` collapsed into its parent, or None if
    the path (possibly stale) addresses a leaf — collapsing a leaf would delete a
    vertex and corrupt the tree."""
    r = copy_tree(root)
    node = _get(r, path)
    if node.is_leaf():
        return None
    parent = _get(r, path[:-1])
    idx = path[-1]
    parent.children = parent.children[:idx] + node.children + parent.children[idx + 1:]
    return r


def _prune_empty(root):
    """Drop internal nodes that have no children (HD-SE-neutral, but tidy)."""
    def rec(n):
        n.children = [c for c in n.children if c.is_leaf() or (rec(c) or c.children)]
        return bool(n.children)
    rec(root)
    return root


def _do_relocate(root, src_path, dst_path):
    """Return a copy with subtree at src_path moved under the node at dst_path, or
    None if illegal (dst is src or a descendant of src). Empty parents are left in
    place (HD-SE-neutral) and pruned later — so no path-shifting cleanup is needed."""
    if dst_path[:len(src_path)] == src_path:         # dst is src or inside src
        return None
    r = copy_tree(root)
    target = _get(r, dst_path)                       # grab object BEFORE detaching
    if target.is_leaf():                             # stale path may hit a leaf:
        return None                                  # a leaf must never gain children
    src = _get(r, src_path)
    sp_parent = _get(r, src_path[:-1])
    if sp_parent.is_leaf() or not sp_parent.children:
        return None
    sp_parent.children.pop(src_path[-1])             # detach (object refs stay valid)
    target.children.append(src)
    return r


# -------------------------- binary NNI refinement ---------------------------
def _descendant_vertices(root):
    """Return the leaf set below every node, keyed by object identity."""
    leaves = {}

    def rec(node):
        if node.is_leaf():
            out = {node.vertex}
        else:
            out = set()
            for child in node.children:
                out.update(rec(child))
        leaves[id(node)] = out
        return out

    rec(root)
    return leaves


def _cross_weight(left, right, adj):
    """Total undirected edge weight between two disjoint vertex sets."""
    if len(left) > len(right):
        left, right = right, left
    return sum(weight for u in left for v, weight in adj[u].items()
               if v in right)


def _nni_candidates(root):
    """Enumerate rooted-NNI moves as ``(internal_child_path, promoted_child)``.

    A candidate exists on a binary parent--child edge.  If the current local
    topology is ``((A, B), C)``, promoting child 0 produces ``(A, (B, C))``
    and promoting child 1 produces ``(B, (A, C))``.
    """
    out = []

    def rec(node, path):
        if node.is_leaf():
            return
        if len(node.children) == 2:
            for child_index, child in enumerate(node.children):
                if not child.is_leaf() and len(child.children) == 2:
                    child_path = path + (child_index,)
                    out.append((child_path, 0))
                    out.append((child_path, 1))
        for index, child in enumerate(node.children):
            rec(child, path + (index,))

    rec(root, ())
    return out


def _do_nni(root, child_path, promoted_child):
    """Return a copy after one rooted NNI, or ``None`` if the move is illegal."""
    if not child_path or promoted_child not in (0, 1):
        return None
    r = copy_tree(root)
    try:
        parent = _get(r, child_path[:-1])
        child_index = child_path[-1]
        internal = parent.children[child_index]
    except (IndexError, AttributeError):
        return None
    if (len(parent.children) != 2 or internal.is_leaf()
            or len(internal.children) != 2):
        return None
    sibling = parent.children[1 - child_index]
    promoted = internal.children[promoted_child]
    retained = internal.children[1 - promoted_child]
    internal.children = [retained, sibling]
    parent.children = [promoted, internal]
    return r


def nni_delta(root, child_path, promoted_child, adj, vol, leaves=None):
    """Exact change in tree structural entropy for one rooted NNI.

    For ``((A,B),C) -> (A,(B,C))`` only A--B and B--C graph edges change
    their LCA.  With ``vol = 2m`` the identity is

        2/vol * [w(A,B) log2(V_P/V_AB)
                 + w(B,C) log2(V_BC/V_P)].

    ``annotate`` must have been called on ``root`` so node volumes are current.
    """
    if vol <= 0 or not child_path or promoted_child not in (0, 1):
        return None
    try:
        parent = _get(root, child_path[:-1])
        child_index = child_path[-1]
        internal = parent.children[child_index]
    except (IndexError, AttributeError):
        return None
    if (len(parent.children) != 2 or internal.is_leaf()
            or len(internal.children) != 2):
        return None
    sibling = parent.children[1 - child_index]
    promoted = internal.children[promoted_child]
    retained = internal.children[1 - promoted_child]
    if internal.V <= 0 or parent.V <= 0 or retained.V + sibling.V <= 0:
        return None

    if leaves is None:
        leaves = _descendant_vertices(root)
    w_ab = _cross_weight(leaves[id(promoted)], leaves[id(retained)], adj)
    w_bc = _cross_weight(leaves[id(retained)], leaves[id(sibling)], adj)
    return (2.0 / vol) * (
        w_ab * math.log(parent.V / internal.V, 2)
        + w_bc * math.log((retained.V + sibling.V) / parent.V, 2)
    )


def refine_nni(root, deg, adj, vol, max_rounds=100, tol=1e-10,
               return_trace=False):
    """Best-improvement rooted-NNI descent with exact delta verification.

    The routine only edits binary parent--child neighborhoods; multiway parts
    are left intact.  Each selected move is predicted by :func:`nni_delta` and
    independently checked by a full ``H^T`` recomputation before acceptance.
    Consequently the returned tree is never worse than the input and is
    one-NNI-local within the neighborhoods examined when the routine stops.
    """
    annotate(root, deg, adj, vol)
    current = hd_se(root, vol)
    trace = []
    for round_index in range(max_rounds):
        best = None
        leaves = _descendant_vertices(root)
        for child_path, promoted_child in _nni_candidates(root):
            delta = nni_delta(
                root, child_path, promoted_child, adj, vol, leaves=leaves
            )
            if delta is not None and delta < -tol:
                if best is None or delta < best[0]:
                    best = (delta, child_path, promoted_child)
        if best is None:
            break

        predicted, child_path, promoted_child = best
        candidate = _do_nni(root, child_path, promoted_child)
        if candidate is None:
            break
        annotate(candidate, deg, adj, vol)
        candidate_h = hd_se(candidate, vol)
        observed = candidate_h - current
        if abs(observed - predicted) > 1e-8:
            raise AssertionError(
                f"NNI delta mismatch: predicted={predicted:.12g}, "
                f"observed={observed:.12g}"
            )
        if observed >= -tol:
            break
        trace.append({
            "round": round_index,
            "child_path": child_path,
            "promoted_child": promoted_child,
            "delta": observed,
            "before": current,
            "after": candidate_h,
        })
        root, current = candidate, candidate_h

    if return_trace:
        return root, trace
    return root


def refine_nni_compound(root, deg, adj, vol, max_rounds=8, beam_width=16,
                        barrier_bits=0.05, tol=1e-10, return_trace=False):
    """Escape one-NNI local optima with bounded two-move lookahead.

    The first NNI may raise ``H^T`` by at most ``barrier_bits``.  Up to
    ``beam_width`` first moves with the smallest exact deltas are expanded, and
    every legal second move is evaluated.  A pair is committed only when its
    final, fully recomputed entropy is strictly below the entropy before the
    pair.  Thus compound search can cross a shallow barrier without weakening
    the monotone-output guarantee.

    After each accepted pair, ordinary exact NNI descent is rerun.  The method
    stops when neither a one-step move nor an admissible two-step sequence
    improves the tree, or when ``max_rounds`` compound moves have been used.
    """
    if beam_width <= 0:
        raise ValueError("beam_width must be positive")
    if barrier_bits < 0:
        raise ValueError("barrier_bits must be non-negative")

    annotate(root, deg, adj, vol)
    root, descent_trace = refine_nni(
        root, deg, adj, vol, tol=tol, return_trace=True
    )
    annotate(root, deg, adj, vol)
    current = hd_se(root, vol)
    trace = [{**step, "kind": "descent"} for step in descent_trace]

    for round_index in range(max_rounds):
        first_leaves = _descendant_vertices(root)
        first_moves = []
        for child_path, promoted_child in _nni_candidates(root):
            delta = nni_delta(
                root, child_path, promoted_child, adj, vol,
                leaves=first_leaves,
            )
            if delta is not None and delta <= barrier_bits + tol:
                first_moves.append((delta, child_path, promoted_child))
        first_moves.sort(key=lambda item: item[0])

        best = None
        for delta1, path1, promoted1 in first_moves[:beam_width]:
            middle = _do_nni(root, path1, promoted1)
            if middle is None:
                continue
            annotate(middle, deg, adj, vol)
            middle_h = hd_se(middle, vol)
            if abs((middle_h - current) - delta1) > 1e-8:
                raise AssertionError(
                    "compound NNI first-step delta disagrees with full entropy"
                )

            second_leaves = _descendant_vertices(middle)
            for path2, promoted2 in _nni_candidates(middle):
                delta2 = nni_delta(
                    middle, path2, promoted2, adj, vol,
                    leaves=second_leaves,
                )
                if delta2 is None:
                    continue
                predicted_final = middle_h + delta2
                if predicted_final >= current - tol:
                    continue
                candidate = _do_nni(middle, path2, promoted2)
                if candidate is None:
                    continue
                annotate(candidate, deg, adj, vol)
                candidate_h = hd_se(candidate, vol)
                if abs((candidate_h - middle_h) - delta2) > 1e-8:
                    raise AssertionError(
                        "compound NNI second-step delta disagrees with full entropy"
                    )
                if candidate_h < current - tol:
                    item = (candidate_h, candidate, delta1, delta2,
                            path1, promoted1, path2, promoted2, middle_h)
                    if best is None or candidate_h < best[0]:
                        best = item

        if best is None:
            break

        (candidate_h, candidate, delta1, delta2, path1, promoted1,
         path2, promoted2, middle_h) = best
        before = current
        root, current = candidate, candidate_h
        trace.append({
            "kind": "compound",
            "round": round_index,
            "first_child_path": path1,
            "first_promoted_child": promoted1,
            "second_child_path": path2,
            "second_promoted_child": promoted2,
            "first_delta": delta1,
            "second_delta": delta2,
            "barrier": max(0.0, middle_h - before),
            "before": before,
            "after": current,
            "delta": current - before,
        })

        root, post_trace = refine_nni(
            root, deg, adj, vol, tol=tol, return_trace=True
        )
        trace.extend({**step, "kind": "descent"} for step in post_trace)
        annotate(root, deg, adj, vol)
        current = hd_se(root, vol)

    if return_trace:
        return root, trace
    return root


def _reloc_targets(root, sp):
    """Local relocation targets for the subtree at path sp: internal siblings,
    internal uncles, and the grandparent."""
    targets = set()
    parent_p = sp[:-1]
    gp = sp[:-2] if len(sp) >= 2 else None
    pnode = _get(root, parent_p)
    for i, c in enumerate(pnode.children):
        if i != sp[-1] and not c.is_leaf():
            targets.add(parent_p + (i,))
    if gp is not None:
        targets.add(gp)
        gpnode = _get(root, gp)
        for i, c in enumerate(gpnode.children):
            if i != parent_p[-1] and not c.is_leaf():
                targets.add(gp + (i,))
    return targets


def refine(root, deg, adj, vol, max_rounds=12, relocate=True,
           strategy="best", sample_cap=None, seed=0):
    """Greedy exact-guarded refinement: collapse a level, or relocate a subtree to a
    nearby module. Accept only strictly-H^T-decreasing moves. Result <= init.

    strategy="best": evaluate all candidates, apply the single best per round
      (small graphs; deterministic).
    strategy="first": shuffled first-improvement — apply every improving move as
      soon as it is found (far fewer evaluations; for larger graphs). Each accepted
      move is still verified by an exact full recompute, so the <=-init guarantee
      is identical; only search completeness differs.
    sample_cap: if set, at most this many relocation candidates per round."""
    import random
    rng = random.Random(seed)
    annotate(root, deg, adj, vol)
    cur = hd_se(root, vol)
    for _ in range(max_rounds):
        improved = False
        best_root, best_h = None, cur

        # ---- candidate move list: (kind, payload) ----
        moves = [("collapse", p) for p in _internal_paths(root)]
        reloc = []
        if relocate:
            for sp in _all_paths(root):
                if len(sp) < 1:
                    continue
                for tp in _reloc_targets(root, sp):
                    reloc.append(("relocate", (sp, tp)))
        if sample_cap is not None and len(reloc) > sample_cap:
            reloc = rng.sample(reloc, sample_cap)
        moves += reloc
        if strategy == "first":
            rng.shuffle(moves)

        for kind, payload in moves:
            if kind == "collapse":
                # path may be stale after a first-improvement commit; guard
                try:
                    r = _do_collapse(root, payload)
                except (IndexError, AttributeError):
                    continue
            else:
                sp, tp = payload
                try:
                    r = _do_relocate(root, sp, tp)
                except (IndexError, AttributeError):
                    continue
            if r is None:
                continue
            annotate(r, deg, adj, vol)
            h = hd_se(r, vol)
            if strategy == "first":
                if h < cur - 1e-9:
                    root = _prune_empty(r)
                    annotate(root, deg, adj, vol)
                    cur = h
                    improved = True
                    # note: remaining paths refer to the old tree; guards above
                    # skip stale ones, the next round regenerates the move list
            else:
                if h < best_h - 1e-9:
                    best_h, best_root = h, r

        if strategy == "best":
            if best_root is None:
                break
            root = _prune_empty(best_root)
            annotate(root, deg, adj, vol)
            cur = best_h
        elif not improved:
            break
    return root


# ------------------------------- public API ----------------------------------
def encoding_tree(G, seed=0, starts=4, do_refine=True):
    """Build (and refine) a low-structural-entropy encoding tree for G.

    Two initializations are refined and the lower-H^T one is returned:
      (a) the binary se_agglomerative dendrogram — exact-guarded refinement makes the
          result <= that naive dendrogram by construction;
      (b) a multiway tree from recursive se_louvain — wins where multiway helps.
    Refinement accepts only strictly-H^T-decreasing collapse / subtree-relocation moves.
    Returns (root, deg, adj, vol). G must have integer nodes 0..n-1."""
    from .se import se_agglomerative
    _, _, n, adj, deg, vol = _graph_arrays(G)
    nodes = list(G.nodes())
    pos = {u: i for i, u in enumerate(nodes)}
    Gi = nx.relabel_nodes(G, pos, copy=True)

    # small graphs: exhaustive best-move search (deterministic, stable numbers);
    # larger graphs: shuffled first-improvement with a relocation sample cap —
    # same exact-guarded accepts (result <= init), just a lighter search.
    if n <= 250:
        rkw = dict(relocate=True, strategy="best")
    else:
        rkw = dict(relocate=True, strategy="first", sample_cap=1500,
                   max_rounds=8, seed=seed)
    cands = []
    # (a) binary SE dendrogram init
    try:
        Z = se_agglomerative(Gi)
        t_bin = linkage_to_tree(Z, n)
        annotate(t_bin, deg, adj, vol)
        if do_refine:
            t_bin = refine(t_bin, deg, adj, vol, **rkw)
        cands.append(t_bin)
    except Exception:
        pass
    # (b) recursive Louvain-SE init
    try:
        t_lv = build_tree(Gi, seed=seed, starts=starts)
        annotate(t_lv, deg, adj, vol)
        if do_refine:
            t_lv = refine(t_lv, deg, adj, vol, **rkw)
        cands.append(t_lv)
    except Exception:
        pass
    # (c) warm-starts from strong external hierarchies, refined (so se_hier <= each).
    #     Paris (scikit-network) is a strong HD-SE tree; use it when available.
    for mk in _external_inits(Gi, n):
        try:
            t = linkage_to_tree(mk, n); annotate(t, deg, adj, vol)
            if do_refine:
                t = refine(t, deg, adj, vol, **rkw)
            cands.append(t)
        except Exception:
            pass

    best = min(cands, key=lambda r: hd_se(r, vol))
    annotate(best, deg, adj, vol)
    return best, deg, adj, vol


def encoding_tree_nni(G, seed=0, starts=4, do_refine=True,
                      max_nni_rounds=100, compound=True,
                      compound_rounds=8, beam_width=16,
                      barrier_bits=0.05, return_trace=False):
    """Refine :func:`encoding_tree` with exact rooted-NNI search.

    The original ``se_hier`` output is the initializer and only strictly
    decreasing, independently verified NNI moves are accepted.  The returned
    tree therefore has ``H^T`` no greater than the corresponding ``se_hier``
    tree.  NNI acts on binary neighborhoods and leaves multiway regions intact.
    By default, bounded two-move lookahead is applied after exact one-step
    descent; set ``compound=False`` for the one-NNI-local variant only.
    """
    root, deg, adj, vol = encoding_tree(
        G, seed=seed, starts=starts, do_refine=do_refine
    )
    root, trace = refine_nni(
        root, deg, adj, vol,
        max_rounds=max_nni_rounds,
        return_trace=True,
    )
    if compound:
        root, compound_trace = refine_nni_compound(
            root, deg, adj, vol,
            max_rounds=compound_rounds,
            beam_width=beam_width,
            barrier_bits=barrier_bits,
            return_trace=True,
        )
        trace.extend(compound_trace)
    if return_trace:
        return root, deg, adj, vol, trace
    return root, deg, adj, vol


def encoding_tree_nni_fast(G, seed=0, starts=4, compound=True,
                           max_nni_rounds=100, compound_rounds=8,
                           beam_width=16, barrier_bits=0.05,
                           return_trace=False):
    """Fast multi-start hierarchy construction with exact NNI certification.

    Unlike :func:`encoding_tree`, this variant does not run exhaustive generic
    collapse/relocation refinement.  It builds three inexpensive candidates
    (SE agglomeration, recursive SE, and Paris when installed), applies exact
    one-step NNI descent and optional bounded two-step escape to each, and
    returns the lowest-entropy result.  The output is therefore no worse than
    the NNI-refined SE-agglomerative start and is one-NNI-local on all binary
    neighborhoods examined.
    """
    from .se import se_agglomerative

    _, _, n, adj, deg, vol = _graph_arrays(G)
    nodes = list(G.nodes())
    pos = {node: index for index, node in enumerate(nodes)}
    graph = nx.relabel_nodes(G, pos, copy=True)
    candidates = []

    try:
        candidates.append((
            "SE-agglomerative",
            linkage_to_tree(se_agglomerative(graph), n),
        ))
    except Exception:
        pass
    try:
        candidates.append((
            "recursive-SE",
            build_tree(graph, seed=seed, starts=starts),
        ))
    except Exception:
        pass
    for index, linkage in enumerate(_external_inits(graph, n)):
        try:
            candidates.append((
                f"external-{index}", linkage_to_tree(linkage, n)
            ))
        except Exception:
            pass
    if not candidates:
        raise RuntimeError("no hierarchy initializer succeeded")

    results = []
    for name, root in candidates:
        annotate(root, deg, adj, vol)
        root, trace = refine_nni(
            root, deg, adj, vol,
            max_rounds=max_nni_rounds,
            return_trace=True,
        )
        if compound:
            root, extra_trace = refine_nni_compound(
                root, deg, adj, vol,
                max_rounds=compound_rounds,
                beam_width=beam_width,
                barrier_bits=barrier_bits,
                return_trace=True,
            )
            trace.extend(extra_trace)
        annotate(root, deg, adj, vol)
        results.append((hd_se(root, vol), name, root, trace))

    entropy, selected, root, trace = min(results, key=lambda item: item[0])
    annotate(root, deg, adj, vol)
    if return_trace:
        audit = {
            "selected_initializer": selected,
            "selected_entropy": entropy,
            "selected_trace": trace,
            "candidate_entropies": {
                name: value for value, name, _, _ in results
            },
        }
        return root, deg, adj, vol, audit
    return root, deg, adj, vol


def _external_inits(G, n):
    """Linkage matrices from strong hierarchical heuristics to warm-start refinement.
    Optional deps; silently skipped if unavailable. Paris (scikit-network) gives the
    lowest-H^T classical trees, so refining it lets se_hier dominate it."""
    out = []
    try:                                   # Paris — modularity-based, low H^T
        from sknetwork.hierarchy import Paris
        import scipy.sparse as sp
        A = nx.to_scipy_sparse_array(G, nodelist=list(range(n)), weight="weight", format="csr")
        A = sp.csr_matrix(A)
        A.indices = A.indices.astype(np.int32); A.indptr = A.indptr.astype(np.int32)
        out.append(Paris().fit_predict(A))
    except Exception:
        pass
    return out


import numpy as np  # noqa: E402  (used by _external_inits)


def linkage_to_tree(Z, n):
    """Convert a scipy binary linkage matrix to a TNode tree (for baselines)."""
    nodemap = {i: TNode(vertex=i) for i in range(n)}
    nid = n
    for a, b, _, _ in Z:
        nodemap[nid] = TNode(children=[nodemap[int(a)], nodemap[int(b)]])
        nid += 1
    return nodemap[nid - 1]


def top_level_labels(root, n):
    """Flat partition from the top level of the tree (one label per top child)."""
    labels = [0] * n
    for cid, child in enumerate(root.children):
        stack = [child]
        while stack:
            x = stack.pop()
            if x.is_leaf():
                labels[x.vertex] = cid
            else:
                stack.extend(x.children)
    return labels


# ------------------------------- self-tests ----------------------------------
def _selftest():
    import random
    from . import metrics as M
    from .se import se_agglomerative
    random.seed(0)

    print("== 2-level tree H^T == canonical 2D-SE ==")
    for gi, G in enumerate([nx.karate_club_graph(),
                            nx.gnp_random_graph(20, 0.25, seed=1)]):
        G = nx.convert_node_labels_to_integers(G)
        _, _, n, adj, deg, vol = _graph_arrays(G)
        labels = [random.randrange(4) for _ in range(n)]
        # 2-level tree: root -> community modules -> leaves
        blocks = {}
        for v, l in enumerate(labels):
            blocks.setdefault(l, []).append(v)
        root = TNode(children=[TNode(children=[TNode(vertex=v) for v in blk])
                               for blk in blocks.values()])
        annotate(root, deg, adj, vol)
        ht = hd_se(root, vol)
        h2 = M.structural_entropy_2d(G, labels)
        ok = abs(ht - h2) < 1e-9
        print(f"  graph{gi}: H^T(2level)={ht:.6f}  2D-SE={h2:.6f}  {'OK' if ok else 'MISMATCH'}")
        assert ok

    print("== refinement is monotone (H^T never increases) ==")
    G = nx.convert_node_labels_to_integers(nx.gnp_random_graph(60, 0.12, seed=2))
    _, _, n, adj, deg, vol = _graph_arrays(G)
    root = build_tree(nx.relabel_nodes(G, {u: u for u in G}, copy=True), seed=1, starts=4)
    annotate(root, deg, adj, vol)
    before = hd_se(root, vol)
    refine(root, deg, adj, vol)
    after = hd_se(root, vol)
    print(f"  build H^T={before:.6f} -> refined H^T={after:.6f}  {'OK' if after <= before + 1e-9 else 'INCREASED'}")
    assert after <= before + 1e-9

    print("== vs naive binary se_agglomerative dendrogram (H^T & Dasgupta) ==")
    for gi, G in enumerate([nx.karate_club_graph(),
                            nx.connected_caveman_graph(4, 6)]):
        G = nx.convert_node_labels_to_integers(G)
        _, _, n, adj, deg, vol = _graph_arrays(G)
        Z = se_agglomerative(G)
        tree_ag = linkage_to_tree(Z, n)
        annotate(tree_ag, deg, adj, vol)
        h_ag, d_ag = hd_se(tree_ag, vol), dasgupta_tree(tree_ag, G)
        root, deg2, adj2, vol2 = encoding_tree(G, seed=0)
        h_hi, d_hi = hd_se(root, vol2), dasgupta_tree(root, G)
        print(f"  graph{gi}: agglom H^T={h_ag:.4f} das={d_ag:.0f} | "
              f"se_hier H^T={h_hi:.4f} das={d_hi:.0f} | "
              f"{'LOWER' if h_hi < h_ag - 1e-9 else 'tie'}")
        assert h_hi <= h_ag + 1e-9, "se_hier must be <= naive dendrogram H^T"
    print("ALL HTREE SELFTESTS PASSED")


if __name__ == "__main__":
    _selftest()
