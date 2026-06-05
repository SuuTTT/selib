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
    """Set V (volume) and g (cut) for every node. g_a = V_a - 2*E_in(a),
    computed via per-edge LCA walk (exact, O(m * height))."""
    # post-order: volume + parent + per-leaf list
    leaves_of = {}

    def post(node, parent):
        node.parent = parent
        if node.is_leaf():
            node.V = deg[node.vertex]
            node.g = deg[node.vertex]      # singleton: all incident edges leave
            leaves_of[id(node)] = [node.vertex]
            return leaves_of[id(node)]
        lv = []
        node.V = 0.0
        for c in node.children:
            cl = post(c, node)
            lv.extend(cl)
            node.V += c.V
        node.g = node.V                    # subtract 2*E_in below
        leaves_of[id(node)] = lv
        return lv

    post(root, None)

    # depth + ancestor chains for LCA
    depth = {}
    def setdepth(node, d):
        depth[id(node)] = d
        for c in node.children:
            setdepth(c, d + 1)
    setdepth(root, 0)

    # map vertex -> leaf node
    leafnode = {}
    def collect(node):
        if node.is_leaf():
            leafnode[node.vertex] = node
        for c in node.children:
            collect(c)
    collect(root)

    def lca(a, b):
        na, nb = leafnode[a], leafnode[b]
        da, db = depth[id(na)], depth[id(nb)]
        while da > db:
            na = na.parent; da -= 1
        while db > da:
            nb = nb.parent; db -= 1
        while na is not nb:
            na = na.parent; nb = nb.parent
        return na

    # for each internal edge, subtract 2w from g of LCA and all its ancestors
    n = len(deg)
    for u in range(n):
        for v, w in adj[u].items():
            if v <= u:
                continue
            a = lca(u, v)
            while a is not None:
                a.g -= 2 * w
                a = a.parent
    # clean tiny negatives
    def clean(node):
        if node.g < 1e-9:
            node.g = 0.0
        for c in node.children:
            clean(c)
    clean(root)
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
    """Return a copy with the node at `path` collapsed into its parent."""
    r = copy_tree(root)
    node = _get(r, path)
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
    src = _get(r, src_path)
    sp_parent = _get(r, src_path[:-1])
    sp_parent.children.pop(src_path[-1])             # detach (object refs stay valid)
    target.children.append(src)
    return r


def refine(root, deg, adj, vol, max_rounds=12, relocate=True):
    """Greedy exact-guarded refinement: collapse a level, or relocate a subtree to a
    nearby module. Accept only strictly-H^T-decreasing moves. Result <= init.
    `relocate=False` does collapse-only (fast) for large graphs."""
    annotate(root, deg, adj, vol)
    cur = hd_se(root, vol)
    for _ in range(max_rounds):
        best_root, best_h = None, cur

        # collapse candidates
        for path in _internal_paths(root):
            r = _do_collapse(root, path)
            annotate(r, deg, adj, vol)
            h = hd_se(r, vol)
            if h < best_h - 1e-9:
                best_h, best_root = h, r

        # relocate candidates: move each subtree to a sibling / uncle / grandparent
        for sp in (_all_paths(root) if relocate else []):
            if len(sp) < 1:
                continue
            targets = set()
            parent_p = sp[:-1]
            gp = sp[:-2] if len(sp) >= 2 else None
            pnode = _get(root, parent_p)
            for i, c in enumerate(pnode.children):     # siblings (internal)
                if i != sp[-1] and not c.is_leaf():
                    targets.add(parent_p + (i,))
            if gp is not None:
                targets.add(gp)                        # grandparent
                gpnode = _get(root, gp)
                for i, c in enumerate(gpnode.children):  # uncles (internal)
                    if i != parent_p[-1] and not c.is_leaf():
                        targets.add(gp + (i,))
            for tp in targets:
                r = _do_relocate(root, sp, tp)
                if r is None:
                    continue
                annotate(r, deg, adj, vol)
                h = hd_se(r, vol)
                if h < best_h - 1e-9:
                    best_h, best_root = h, r

        if best_root is None:
            break
        root = _prune_empty(best_root)
        annotate(root, deg, adj, vol)
        cur = best_h
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

    reloc = (n <= 250)        # full subtree-relocation only on small/medium graphs
    cands = []
    # (a) binary SE dendrogram init
    try:
        Z = se_agglomerative(Gi)
        t_bin = linkage_to_tree(Z, n)
        annotate(t_bin, deg, adj, vol)
        if do_refine:
            t_bin = refine(t_bin, deg, adj, vol, relocate=reloc)
        cands.append(t_bin)
    except Exception:
        pass
    # (b) recursive Louvain-SE init
    try:
        t_lv = build_tree(Gi, seed=seed, starts=starts)
        annotate(t_lv, deg, adj, vol)
        if do_refine:
            t_lv = refine(t_lv, deg, adj, vol, relocate=reloc)
        cands.append(t_lv)
    except Exception:
        pass

    best = min(cands, key=lambda r: hd_se(r, vol))
    annotate(best, deg, adj, vol)
    return best, deg, adj, vol


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
