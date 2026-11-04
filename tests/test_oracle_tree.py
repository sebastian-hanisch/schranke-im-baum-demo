"""Orakel (ORACLE-PLAYBOOK §5): `scipy` für die Zuordnung in den Knoten und eine zweite, unabhängig geschriebene Knotenschranke (Aufzählung aller Fortsetzungen) für die Gültigkeit; die Aufzählung aller Anordnungen für das Optimum.
Ohne scipy (nur requirements-dev.txt; die App braucht scipy nicht) werden die scipy-Tests übersprungen."""

from itertools import permutations

import numpy as np
import pytest

import sib_assignment as A
import sib_constants as C
import sib_cost as K
import sib_instance as I
import sib_landscape as L
import sib_tree as T

opt = pytest.importorskip("scipy.optimize")


def test_the_node_assignment_equals_scipy_on_the_node_matrices():
    rng = np.random.default_rng(5)
    for fam in C.FAMILIES:
        inst = I.make_instance(fam, 8, 100000)
        F, D = inst.F, inst.D
        for _ in range(4):
            k = int(rng.integers(1, 6))
            fac = [int(x) for x in rng.permutation(8)[:k]]
            loc = [int(x) for x in rng.permutation(8)[:k]]
            free_f = [i for i in range(8) if i not in fac]
            free_l = [j for j in range(8) if j not in loc]
            c = T.linear_costs(F, D, fac, loc, free_f, free_l)
            m2 = T._sorted_rows_asc(F[np.ix_(free_f, free_f)]) @ T._sorted_rows_desc(D[np.ix_(free_l, free_l)]).T
            for M in (c, 2 * c + m2):
                r, cc = opt.linear_sum_assignment(M)
                assert A.hungarian(M)[1] == M[r, cc].sum()


def test_the_dual_ascent_duals_are_feasible_and_complementary():
    rng = np.random.default_rng(6)
    for _ in range(8):
        M = rng.integers(0, 20, size=(5, 5)).astype(float)
        cols, u, v, val = A.hungarian_dual(M)
        r, cc = opt.linear_sum_assignment(M)
        assert val == pytest.approx(M[r, cc].sum()) and (M - u[:, None] - v[None, :]).min() >= -1e-9 and val == pytest.approx(u.sum() + v.sum())


@pytest.mark.parametrize("fam", C.FAMILIES)
def test_every_art_returns_the_enumerated_optimum_and_no_bound_exceeds_the_cheapest_completion(fam):
    inst = I.make_instance(fam, 6, 100007)
    ls = L.landscape(inst)
    for art in ("none", "lin", "glb", "pb", "max"):
        assert T.solve(inst.F, inst.D, art, None).best == ls.opt, art
    # unabhängige Gegenprobe der Knotenschranke: Aufzählung aller Fortsetzungen eines Knotens mit zwei gesetzten Bauteilen
    F, D = inst.F, inst.D
    fac, loc = [0, 3], [2, 5]
    free_f, free_l = [1, 2, 4, 5], [0, 1, 3, 4]
    fixed = int(F[0, 3]) * int(D[2, 5])
    best = min(K.cost(list(dict(zip(fac + free_f, loc + list(q))).get(i) for i in range(6)), F, D) for q in permutations(free_l))
    for art in ("none", "lin", "glb", "pb", "max", "da2"):
        assert T.node_bound(art, F, D, fac, loc, free_f, free_l, fixed) <= best + 1e-6, art
