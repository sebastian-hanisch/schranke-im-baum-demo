"""Die Zahlen der README (Abschnitte „Befunde“ und „Grenzen“) als Tests: Standardfall, Handbeispiel und die Vergleiche über feste Instanzen.
Knotenzahlen der ganzzahligen Arten (ohne, linear, Gilmore–Lawler) sind exakt; Prozentwerte auf ganze Prozent, keine Zahl liegt an einer Rundungsgrenze; Zeiten stehen nie in Tests (DEMO-PLAYBOOK §1b, Wiederholbarkeit)."""

import numpy as np
import pytest

import sib_constants as C
import sib_evaluation as ev
import sib_tree as T


@pytest.fixture(scope="module")
def standard():
    s = ev.Settings()
    return s, ev.instance_data(s)


@pytest.fixture(scope="module")
def sweeps():
    return {n: {f: ev.sweep(f, n) for f in C.FAMILIES} for n in C.SWEEP_SIZES}


@pytest.fixture(scope="module")
def growths():
    return {n: {f: ev.growth(f, n) for f in C.FAMILIES} for n in C.GROWTH_SIZES}


def test_standard_instance_numbers(standard):
    s, v = standard
    assert (s.family, s.n, s.seed, s.order, s.incumbent) == ("netlist", 8, 35, "flow", "descents200")
    assert {a: v["trees"][a].nodes for a in v["arts"]} == {"none": 17024, "lin": 3404, "glb": 64, "pb": 560, "max": 64}
    assert v["opt"] == 31 and v["inc"] == 31 and v["glb"] == 27.0 and v["pb"] == pytest.approx(13.68, abs=0.01) and v["size"] == 109600 and round(100 * v["gap_glb"], 1) == 12.9
    t = v["trees"]["glb"]
    assert t.depth == (8, 56, 0, 0, 0, 0, 0, 0) and t.pruned == (0, 56, 0, 0, 0, 0, 0, 0) and t.optimal and t.perm is None
    assert round(100 * t.share, 2) == 0.06 and round(v["trees"]["none"].nodes / t.nodes) == 266 and round(v["trees"]["lin"].nodes / t.nodes, 1) == 53.2


def test_standard_instance_order_incumbent_grid_and_dual_ascent(standard):
    s, v = standard
    g = ev.grid_data(s, v)
    assert {f"{o}/{k}": t.nodes for (o, k), t in g.items()} == {"flow/descents200": 64, "flow/descent1": 177, "flow/none": 187, "index/descents200": 64, "index/descent1": 96, "index/none": 106,
                                                                  "light/descents200": 644, "light/descent1": 1115, "light/none": 1157}
    assert ev.da_tree(s, v).nodes == 64


def test_hand_example():
    h = ev.hand_data()
    assert h["child"]["none"] == [0.0, 0.0, 0.0] and h["child"]["lin"] == [7.0, 6.0, 7.0] and h["child"]["glb"] == [7.0, 6.0, 7.0] and h["child"]["min_completion"] == [7, 6, 7]
    assert (h["full"].nodes, h["full"].depth, h["full"].pruned, h["with_inc"].nodes) == (6, (3, 2, 1), (2, 1, 0), 3)


def test_sweep_sizes_instance_counts_and_validity(sweeps):
    assert {n: sum(len(r) for r in by.values()) for n, by in sweeps.items()} == {6: 120, 8: 60}
    assert all(r["valid"] and r["inc_hit"] for n in sweeps for rows in sweeps[n].values() for r in rows)


@pytest.mark.parametrize("n,med,pb_more,pb_fewer,root_better,gap_corr,den_corr", [(6, (1240, 212, 38, 68), 94, 1, 24, 0.68, 0.42), (8, (40566, 2204, 276, 604), 60, 0, 19, 0.19, 0.64)])
def test_pooled_medians_counts_and_correlations(sweeps, n, med, pb_more, pb_fewer, root_better, gap_corr, den_corr):
    rows = ev.pooled(sweeps[n])
    assert tuple(ev.median_of(rows, f"nodes_{a}") for a in C.SWEEP_ARTS) == med
    assert (sum(r["nodes_pb"] > r["nodes_glb"] for r in rows), sum(r["nodes_pb"] < r["nodes_glb"] for r in rows), sum(r["pb"] > r["glb"] for r in rows)) == (pb_more, pb_fewer, root_better)
    nodes = [r["nodes_glb"] for r in rows]
    assert round(ev.spearman(nodes, [r["gap_glb"] for r in rows]), 2) == gap_corr and round(ev.spearman(nodes, [r["density"] for r in rows]), 2) == den_corr


def test_share_of_the_full_tree_by_art(sweeps):
    for n, shares in ((6, (63.40, 10.84, 1.94, 3.48)), (8, (37.01, 2.01, 0.25, 0.55))):
        rows = ev.pooled(sweeps[n])
        got = [100 * ev.median_of(rows, f"nodes_{a}") / T.tree_size(n) for a in C.SWEEP_ARTS]
        assert got == pytest.approx(shares, abs=0.006), (n, got)


def test_family_medians(sweeps):
    exp = {6: {"netlist": (1374, 248, 48, 70), "uniform": (1724, 376, 52, 76), "sparse": (500, 60, 16, 36), "cluster": (1830, 456, 156, 196), "star": (952, 88, 16, 20), "skewed": (732, 170, 39, 68)},
           8: {"netlist": (40566, 2636, 210, 544), "uniform": (89948, 8134, 560, 900), "sparse": (12152, 570, 126, 418), "cluster": (73852, 6326, 416, 762), "star": (36540, 1100, 184, 240), "skewed": (11080, 1062, 212, 538)}}
    for n in exp:
        for f, vals in exp[n].items():
            sm = ev.family_summary(sweeps[n][f])
            assert tuple(sm[a] for a in C.SWEEP_ARTS) == vals, (n, f)


def test_root_gaps_and_pb_root_better_per_family(sweeps):
    gaps = {6: (7.3, 5.2, 10.3, 17.0, 7.7, 3.4), 8: (10.5, 8.0, 6.1, 9.8, 14.1, 6.4)}
    better = {6: (0, 4, 0, 20, 0, 0), 8: (0, 5, 0, 8, 6, 0)}
    for n in (6, 8):
        for k, f in enumerate(C.FAMILIES):
            sm = ev.family_summary(sweeps[n][f])
            assert 100 * sm["gap_glb"] == pytest.approx(gaps[n][k], abs=0.051), (n, f)
            assert sm["pb_root_better"] == better[n][k], (n, f)


def test_growth_of_the_node_count(growths):
    exp = {6: (38, 268, 120), 8: (276, 924, 60), 9: (691, 11749, 30)}
    for n, (med, mx, cnt) in exp.items():
        rows = ev.pooled(growths[n])
        assert (ev.median_of(rows, "nodes"), max(r["nodes"] for r in rows), len(rows), sum(r["capped"] for r in rows)) == (med, mx, cnt, 0), n
    rows12 = ev.pooled(growths[12])
    assert (ev.median_of(rows12, "nodes"), max(r["nodes"] for r in rows12), len(rows12), sum(r["capped"] for r in rows12)) == (7990, 100000, 30, 5)
    assert {f: ev.median_of(growths[12][f], "nodes") for f in C.FAMILIES} == {"netlist": 3196, "uniform": 100000, "sparse": 2164, "cluster": 85868, "star": 3648, "skewed": 9110}
    assert {f: sum(r["capped"] for r in growths[12][f]) for f in C.FAMILIES} == {"netlist": 0, "uniform": 4, "sparse": 0, "cluster": 1, "star": 0, "skewed": 0}
    fam9 = {"netlist": 685, "uniform": 1813, "sparse": 365, "cluster": 5565, "star": 157, "skewed": 585}
    assert {f: ev.median_of(growths[9][f], "nodes") for f in C.FAMILIES} == fam9


def test_two_rounds_of_dual_ascent_save_nodes_n_eight():
    """n = 8, je Familie die ersten vier Instanzen (24): Knoten Gilmore–Lawler gegen zwei Runden Dual Ascent."""
    import sib_bound as B
    from sib_instance import make_instance

    g, d = [], []
    for f in C.FAMILIES:
        for seed in C.SWEEP_SEEDS[:4]:
            inst = make_instance(f, 8, seed)
            inc = B.best_found(inst.F, inst.D, seed, C.STARTS)[0]
            g.append(T.solve(inst.F, inst.D, "glb", inc, "flow", None).nodes)
            d.append(T.solve(inst.F, inst.D, "da2", inc, "flow", None).nodes)
    assert (float(np.median(g)), float(np.median(d))) == (302.0, 232.0)
    assert (sum(x < y for x, y in zip(d, g)), sum(x == y for x, y in zip(d, g)), sum(x > y for x, y in zip(d, g))) == (18, 6, 0)
    assert round(100 * (1 - sum(d) / sum(g))) == 21
