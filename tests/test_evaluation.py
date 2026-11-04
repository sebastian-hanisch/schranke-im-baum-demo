"""Zeilen für die Vergleiche, Zusammenfassungen und Instanzdaten: Handwerte und Eigenschaften."""

import math

import numpy as np
import pytest

import sib_bound as B
import sib_constants as C
import sib_evaluation as ev
import sib_instance as I
import sib_landscape as L
import sib_tree as T


def test_helpers():
    assert ev.de(-1.5, 1) == "−1,5" and ev.pct(0.266, 1) == "26,6 %" and ev.fam("star") == "Stern" and ev.num(27.0) == "27" and ev.num(26.5) == "26,5" and ev.count(109600) == "109 600" and ev.count(64) == "64"
    assert ev.median_of([{"v": 1}, {"v": 5}, {"v": 2}], "v") == 2.0 and ev.density(np.array([[0, 1, 0], [1, 0, 0], [0, 0, 0]])) == pytest.approx(2 / 6)


def test_rank_and_spearman_by_hand():
    assert list(ev.rank([10, 20, 20, 5])) == [2.0, 3.5, 3.5, 1.0]
    assert ev.spearman([1, 2, 3, 4], [10, 20, 30, 40]) == pytest.approx(1.0) and ev.spearman([1, 2, 3, 4], [4, 3, 2, 1]) == pytest.approx(-1.0) and math.isnan(ev.spearman([1, 1, 1], [1, 2, 3]))
    x, y = [1, 2, 3, 4, 5, 6], [2, 1, 4, 3, 6, 5]
    assert ev.spearman(x, y) == pytest.approx(1 - 6 * 6 / (6 * 35))     # 1 − 6 Σ d² / (n (n² − 1)) ohne Gleichstände


def test_incumbents():
    inst = I.make_instance("netlist", 6, 35)
    assert ev.incumbent_value(inst, 35, "none") is None
    one, many = ev.incumbent_value(inst, 35, "descent1"), ev.incumbent_value(inst, 35, "descents200")
    assert many <= one and many == B.best_found(inst.F, inst.D, 35, 200)[0] and one == B.best_found(inst.F, inst.D, 35, 1)[0]
    with pytest.raises(ValueError):
        ev.incumbent_value(inst, 35, "x")


def test_instance_data_for_an_enumerated_size(land6):
    inst, ls = land6
    s = ev.Settings("netlist", 6, 35)
    v = ev.instance_data(s, ls)
    assert v["exact"] and v["opt"] == ls.opt == v["ref"] and v["all_optimal"] and set(v["trees"]) == set(C.LIVE_ARTS) and v["size"] == 1956 and v["cap"] is None
    assert v["glb"] == pytest.approx(B.gilmore_lawler(inst.F, inst.D).glb) and v["gap_glb"] == pytest.approx((ls.opt - v["glb"]) / ls.opt)
    assert v["perm"] is not None and sorted(v["perm"]) == list(range(6)) and v["trees"]["glb"].best == ls.opt
    assert all(v["trees"][a].root <= ls.opt + 1e-9 for a in v["arts"])


def test_instance_data_for_a_large_size_uses_the_cap():
    s = ev.Settings("sparse", 12, 100000)
    v = ev.instance_data(s)
    assert not v["exact"] and v["arts"] == ("glb",) and v["cap"] == C.NODE_CAP and v["opt"] is None and v["size"] == 1302061344
    t = v["trees"]["glb"]
    assert t.nodes <= C.NODE_CAP and v["ref"] == int(t.best) and (v["perm"] is None or sorted(v["perm"]) == list(range(12)))


def test_row_of_and_family_summary():
    rows = ev.sweep("sparse", 6, seeds=(100000, 100001, 100002))
    assert len(rows) == 3 and all(r["valid"] and r["n"] == 6 and r["nodes_none"] >= r["nodes_lin"] >= r["nodes_glb"] for r in rows)
    r = rows[0]
    inst = I.make_instance("sparse", 6, 100000)
    assert r["opt"] == L.landscape(inst).opt and r["glb"] == pytest.approx(B.gilmore_lawler(inst.F, inst.D).glb) and r["density"] == ev.density(inst.F)
    sm = ev.family_summary(rows)
    assert sm["count"] == 3 and sm["valid"] and sm["glb"] == float(np.median([x["nodes_glb"] for x in rows])) and 0 <= sm["pb_more"] <= 3 and 0 <= sm["pb_root_better"] <= 3
    assert len(ev.pooled({"sparse": rows, "star": rows})) == 6


def test_growth_row_and_grid():
    g = ev.growth("star", 6, seeds=(100000, 100001))
    assert len(g) == 2 and all(0 < r["share"] < 1 and not r["capped"] for r in g)
    s = ev.Settings("netlist", 6, 35)
    v = ev.instance_data(s)
    grid = ev.grid_data(s, v)
    assert set(grid) == {(o, k) for o in C.ORDERS for k in C.INCUMBENTS} and all(t.best == v["opt"] for t in grid.values()) and grid[("flow", "descents200")].nodes == v["trees"]["glb"].nodes
    assert grid[("flow", "none")].nodes >= grid[("flow", "descents200")].nodes


def test_da_tree_round_one_equals_glb_and_two_rounds_never_more_nodes(land6):
    s = ev.Settings("netlist", 6, 35)
    v = ev.instance_data(s, land6[1])
    d = ev.da_tree(s, v)
    assert d.best == v["opt"] and d.nodes <= v["trees"]["glb"].nodes


def test_hand_data():
    h = ev.hand_data()
    assert h["child"]["lin"] == [7.0, 6.0, 7.0] and h["child"]["glb"] == [7.0, 6.0, 7.0] and h["child"]["none"] == [0.0, 0.0, 0.0] and h["child"]["min_completion"] == [7, 6, 7]
    assert h["full"].nodes == 6 and h["full"].depth == (3, 2, 1) and h["full"].best == 6 and h["with_inc"].nodes == 3
