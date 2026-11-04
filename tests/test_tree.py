"""Knotenschranken und Tiefensuche: Handwerte, Gültigkeit gegen die Aufzählung aller Fortsetzungen, Eigenschaften (Monotonie der Arten, Zählung), Randfälle (DEMO-PLAYBOOK §1b, ORACLE-PLAYBOOK §5)."""

from itertools import permutations

import numpy as np
import pytest

import sib_bound as B
import sib_constants as C
import sib_cost as K
import sib_instance as I
import sib_spectral as S
import sib_tree as T
from test_landscape import _inst

ALL = ("none", "lin", "glb", "pb", "max")


def _min_completion(F, D, fac, loc):
    n = len(F)
    free_f = [i for i in range(n) if i not in fac]
    free_l = [j for j in range(n) if j not in loc]
    best = None
    for q in permutations(free_l):
        p = [0] * n
        for a, l in zip(fac, loc):
            p[a] = l
        for a, l in zip(free_f, q):
            p[a] = l
        c = K.cost(p, F, D)
        best = c if best is None else min(best, c)
    return best


def _fixed(F, D, fac, loc):
    return sum(int(F[a, b]) * int(D[loc[x], loc[y]]) for x, a in enumerate(fac) for y, b in enumerate(fac) if x < y)


def test_helpers():
    assert [T.tree_size(n) for n in (1, 2, 3, 6, 8, 9)] == [1, 4, 15, 1956, 109600, 986409] and T.tree_size(12) == 1302061344
    assert T.ORDERS == C.ORDERS and set(T.ORDER_NAMES) == set(T.ORDERS) and set(T.ART_NAMES) == set(T.ARTS) == set(T.ART_SHORT)
    F = np.array([[0, 5, 0], [5, 0, 1], [0, 1, 0]])
    assert T.branch_order(F, "flow") == [1, 0, 2] and T.branch_order(F, "index") == [0, 1, 2] and T.branch_order(F, "light") == [2, 0, 1]
    with pytest.raises(ValueError):
        T.branch_order(F, "x")


def test_hand_example_the_tree_by_hand(hand):
    """Fluss A–B 5, B–C 1 auf einer Zeile (Abstände 1, 1, 2), Reihenfolge B, A, C: B auf der Mitte hat Schranke 6, B am Rand 7 (Wurzelkinder), Optimum 6."""
    F, D = hand.F, hand.D
    for art in ("lin", "glb", "pb", "max", "none"):
        b = [T.node_bound(art, F, D, [1], [j], [0, 2], [x for x in range(3) if x != j], 0) for j in range(3)]
        if art == "none":
            assert b == [0.0, 0.0, 0.0]
        else:
            assert b[1] == pytest.approx(6.0) and b[0] == pytest.approx(7.0 if art in ("lin", "glb") else b[0]) and b[0] >= 6.0 - 1e-9
    t = T.solve(F, D, "lin", None)
    assert (t.nodes, t.depth, t.pruned, t.best, t.perm, t.optimal) == (6, (3, 2, 1), (2, 1, 0), 6, [0, 1, 2], True)
    t2 = T.solve(F, D, "lin", 6)
    assert (t2.nodes, t2.best, t2.perm, t2.optimal, t2.depth) == (3, 6, None, True, (3, 0, 0)) and t2.root == 0.0 + T.node_bound("lin", F, D, [], [], [1, 0, 2], [0, 1, 2], 0)


def test_node_bounds_never_exceed_the_cheapest_completion():
    rng = np.random.default_rng(3)
    checked = 0
    for fam in C.FAMILIES:
        for seed in (100000, 100001):
            inst = I.make_instance(fam, 6, seed)
            F, D = inst.F, inst.D
            for _ in range(6):
                k = int(rng.integers(0, 6))
                fac = [int(x) for x in rng.permutation(6)[:k]]
                loc = [int(x) for x in rng.permutation(6)[:k]]
                free_f = [i for i in range(6) if i not in fac]
                free_l = [j for j in range(6) if j not in loc]
                best = _min_completion(F, D, fac, loc)
                fixed = _fixed(F, D, fac, loc)
                for art in ALL + ("da2",) if len(free_f) <= 4 else ALL:
                    assert T.node_bound(art, F, D, fac, loc, free_f, free_l, fixed) <= best + 1e-6, (fam, seed, art, fac, loc)
                checked += 1
    assert checked == 72


def test_arts_are_ordered_node_by_node_and_glb_includes_the_root_bounds():
    for fam in C.FAMILIES:
        inst = I.make_instance(fam, 8, 100003)
        F, D = inst.F, inst.D
        free = list(range(8))
        root = {a: T.node_bound(a, F, D, [], [], free, free, 0) for a in ALL}
        assert root["none"] == 0 and root["lin"] == 0 and root["glb"] == pytest.approx(B.gilmore_lawler(F, D).glb) and root["pb"] == pytest.approx(S.spectral_bounds(F, D).pb)
        assert root["max"] == pytest.approx(max(root["glb"], root["pb"]))
        for j in range(8):
            rest = [x for x in range(8) if x != j]
            vals = {a: T.node_bound(a, F, D, [3], [j], [i for i in range(8) if i != 3], rest, 0) for a in ALL}
            assert vals["none"] <= vals["lin"] + 1e-9 <= vals["glb"] + 1e-9 and vals["glb"] <= vals["max"] + 1e-9 and vals["pb"] <= vals["max"] + 1e-9


def test_da2_round_one_is_glb_and_two_rounds_do_not_get_worse():
    inst = I.make_instance("cluster", 6, 100000)
    F, D = inst.F, inst.D
    fac, loc = [2], [1]
    free_f, free_l = [0, 1, 3, 4, 5], [0, 2, 3, 4, 5]
    c = T.linear_costs(F, D, fac, loc, free_f, free_l)
    Ff, Dd = F[np.ix_(free_f, free_f)], D[np.ix_(free_l, free_l)]
    one, two = T.dual_ascent_value(Ff, Dd, c, 1), T.dual_ascent_value(Ff, Dd, c, 2)
    g = T.node_bound("glb", F, D, fac, loc, free_f, free_l, 0)
    assert one == pytest.approx(g) and two >= one - 1e-9


@pytest.mark.parametrize("art", ALL)
def test_every_art_proves_the_enumerated_optimum(art, land6):
    inst, ls = land6
    t = T.solve(inst.F, inst.D, art, None)
    assert t.optimal and t.best == ls.opt and K.cost(t.perm, inst.F, inst.D) == ls.opt and t.nodes == sum(t.depth) and all(0 <= p <= d for p, d in zip(t.pruned, t.depth))


def test_with_the_optimum_as_incumbent_the_nodes_are_nested_by_strength(land6):
    inst, ls = land6
    nodes = {a: T.solve(inst.F, inst.D, a, ls.opt).nodes for a in ALL}
    assert nodes["max"] <= nodes["glb"] <= nodes["lin"] <= nodes["none"] and nodes["max"] <= nodes["pb"] and nodes["none"] < T.tree_size(6)
    t = T.solve(inst.F, inst.D, "glb", ls.opt)
    assert t.perm is None and t.best == ls.opt and t.optimal


def test_a_worse_incumbent_is_improved_and_a_cap_stops_the_search(land6):
    inst, ls = land6
    t = T.solve(inst.F, inst.D, "glb", ls.opt + 5)
    assert t.best == ls.opt and t.perm is not None
    c = T.solve(inst.F, inst.D, "none", None, cap=100)
    assert c.capped and not c.optimal and c.nodes == 100 and c.best >= ls.opt
    d = T.solve(inst.F, inst.D, "none", None, cap=10**9)
    assert not d.capped and d.nodes == T.solve(inst.F, inst.D, "none", None).nodes


@pytest.mark.parametrize("order", C.ORDERS)
def test_every_order_finds_the_optimum(order, land6):
    inst, ls = land6
    assert T.solve(inst.F, inst.D, "glb", None, order=order).best == ls.opt


def test_share_depth_and_root():
    inst = I.make_instance("netlist", 6, 35)
    t = T.solve(inst.F, inst.D, "glb", None)
    assert t.share == t.nodes / 1956 and len(t.depth) == 6 and t.root == pytest.approx(B.gilmore_lawler(inst.F, inst.D).glb)
    with pytest.raises(ValueError):
        T.node_bound("x", inst.F, inst.D, [], [], list(range(6)), list(range(6)), 0)


def test_child_bounds_and_completion_minima(land6):
    inst, ls = land6
    cb = T.child_bounds(inst.F, inst.D, ALL)
    mc = cb["min_completion"]
    assert min(mc) == ls.opt and len(mc) == 6 and cb["first"] == T.branch_order(inst.F, "flow")[0]
    assert all(cb[a][j] <= mc[j] + 1e-6 for a in ALL for j in range(6))
    big = T.child_bounds(I.make_instance("netlist", 12, 1).F, I.make_instance("netlist", 12, 1).D, ("glb",))
    assert big["min_completion"] is None and len(big["glb"]) == 12


def test_edge_cases():
    z = _inst(np.zeros((4, 4)))
    t = T.solve(z.F, z.D, "glb", None)
    assert t.best == 0 and t.optimal
    two = _inst([[0, 3], [3, 0]])
    t2 = T.solve(two.F, two.D, "pb", None)
    assert t2.best == 3 and t2.perm in ([0, 1], [1, 0])
    ones = np.ones((5, 5), dtype=np.int16) - np.eye(5, dtype=np.int16)
    e = _inst(ones)
    assert T.solve(e.F, e.D, "max", None).best == min(K.cost(p, e.F, e.D) for p in permutations(range(5)))
