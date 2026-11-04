"""Verdikte (reine Funktionen in sib_evaluation.py) an handgesetzten Werten: Art, Schwellen und jede Zahl im Text (DEMO-PLAYBOOK §1b)."""

import pytest

import sib_constants as C
import sib_evaluation as ev
import sib_tree as T


def _tree(nodes, art="glb", best=31.0, capped=False, root=27.0, n=8, perm=None):
    depth = (8, nodes - 8, 0) if nodes >= 8 else (nodes,)
    return T.Tree(art, "flow", n, nodes, best, perm, capped, 0.01, depth, tuple(0 for _ in depth), root, 31)


def _row(glb=100, pb=300, lin=2000, none=40000, gap=0.1, pbs=40.0, glbs=60.0, dens=0.5, valid=True, inc_hit=True, pbroot=None):
    return {"nodes_glb": glb, "nodes_pb": pb, "nodes_lin": lin, "nodes_none": none, "gap_glb": gap, "density": dens, "valid": valid, "inc_hit": inc_hit, "glb": glbs, "pb": pbs if pbroot is None else pbroot}


def _v(trees, exact=True, opt=31, inc=31, n=8, glb=27.0):
    inst = type("I", (), {"rows": 2, "cols": 4})()
    return {"inst": inst, "exact": exact, "opt": opt, "ref": opt or 0, "inc": inc, "arts": tuple(trees), "trees": trees, "glb": glb, "pb": 13.7, "size": T.tree_size(n), "density": 0.4, "gap_glb": (opt - glb) / opt if opt else float("nan")}


def test_tree_verdict_for_a_finished_and_a_capped_run():
    s = ev.Settings("netlist", 8, 35)
    v = _v({"glb": _tree(220)})
    kind, text = ev.verdict_tree(s, v)
    assert kind == "success" and "Familie **Netzliste**, 8 Bauteile, Raster 2×4, Seed 35" in text and "109 600 Knoten" in text and "**220** Knoten (0,20 % davon)" in text and "Optimum **31** bewiesen (gleich dem aufgezählten)" in text
    assert "Wurzelschranke ist 27 (Lücke 12,9 %)" in text and "Anfangswert 31" in text
    wrong = _v({"glb": _tree(220, best=32.0)})
    assert "ACHTUNG: aufgezählt 31" in ev.verdict_tree(s, wrong)[1]
    cap = _v({"glb": _tree(100000, capped=True, best=70.0, root=60.0, n=12)}, exact=False, opt=None, n=12)
    k2, t2 = ev.verdict_tree(ev.Settings("uniform", 12, 1), cap)
    assert k2 == "warning" and "100 000)" in t2 and "**nicht zu Ende gerechnet**" in t2 and "Kosten 70" in t2 and "Schranke der Wurzel 60" in t2 and "1 302 061 344" in t2
    none_inc = dict(v, inc=None)
    assert "der Anfangswert keiner" in ev.verdict_tree(s, none_inc)[1]


def test_arts_verdict_quotes_the_counts_and_the_ratios():
    s = ev.Settings("netlist", 8, 35)
    trees = {"none": _tree(40000, "none"), "lin": _tree(2000, "lin"), "glb": _tree(200), "pb": _tree(500, "pb"), "max": _tree(200, "max")}
    kind, text = ev.verdict_arts(s, _v(trees))
    assert kind == "success" and "ohne 40 000; linear 2 000; Gilmore–Lawler 200; projiziert 500; Maximum 200" in text and "200-mal weniger Knoten als der Baum ohne Schranke" in text and "10,0-mal weniger als die lineare Zuordnung" in text and "**mehr** Knoten" in text
    trees["pb"] = _tree(200, "pb")
    assert "**gleich viele** Knoten" in ev.verdict_arts(s, _v(trees))[1]
    trees["pb"] = _tree(100, "pb")
    assert "**weniger** Knoten" in ev.verdict_arts(s, _v(trees))[1]
    trees["lin"] = _tree(100, "lin")
    assert ev.verdict_arts(s, _v(trees))[0] == "warning"
    assert ev.verdict_arts(ev.Settings("netlist", 12, 1), _v({"glb": _tree(5, n=12)}, n=12))[0] == "info"


def test_inspect_verdict():
    cb = {"none": [0, 0, 0], "glb": [7.0, 6.0, 7.0], "min_completion": [7, 6, 8]}
    kind, text = ev.verdict_inspect(cb, ("none", "glb"))
    assert kind == "success" and "gültig" in text and "ohne scharf in 0 von 3; Gilmore–Lawler scharf in 2 von 3" in text and "Kleinste Fortsetzung insgesamt: 6" in text
    bad = dict(cb, glb=[7.0, 6.0, 9.0])
    assert ev.verdict_inspect(bad, ("glb",))[0] == "error" and "ACHTUNG" in ev.verdict_inspect(bad, ("glb",))[1]
    assert ev.verdict_inspect(dict(cb, min_completion=None), ("glb",))[0] == "info"


def test_da_verdict():
    s = ev.Settings()
    kind, text = ev.verdict_da(s, _tree(200), _tree(150, "da2"))
    assert kind == "info" and "**150** Knoten" in text and "Gilmore–Lawler 200" in text and "spart 25 %" in text
    assert "keine Ersparnis" in ev.verdict_da(s, _tree(200), _tree(200, "da2"))[1]


def test_sweep_verdict_counts_and_validity():
    by = {"netlist": [_row(), _row(glb=300, pb=250, pbroot=70.0)], "uniform": [_row(glb=500, pb=400, pbroot=80.0, glbs=60.0), _row()]}
    kind, text = ev.verdict_sweep(8, by)
    assert kind == "success" and "Bei n = 8, Median über 4 Instanzen" in text and "ohne 40 000; linear 2 000; Gilmore–Lawler 200; projiziert 300 Knoten (voller Baum 109 600)" in text
    assert "in 2 von 4 Instanzen besser als Gilmore–Lawler, braucht im Baum aber in 2 mehr Knoten (weniger in 2)" in text and "(gültig)" in text
    by["netlist"][0] = _row(valid=False)
    assert ev.verdict_sweep(8, by)[0] == "error" and "ACHTUNG" in ev.verdict_sweep(8, by)[1]


def test_corr_verdict():
    rows = [_row(glb=g, gap=0.1 * i, dens=d) for i, (g, d) in enumerate([(10, 0.1), (20, 0.2), (30, 0.3), (40, 0.4), (50, 0.5), (60, 0.6)])]
    kind, text = ev.verdict_corr(6, {"netlist": rows})
    assert kind == "info" and "Bei n = 6 (6 Instanzen)" in text and "Lücke der Wurzelschranke** 1,00" in text and "Dichte des Flusses** 1,00" in text and "Netzliste 35" in text and "±" in text


def test_start_verdict_and_cap_case():
    s = ev.Settings("netlist", 8, 35)
    grid = {(o, k): _tree(100 + 10 * i + 5 * j) for i, o in enumerate(C.ORDERS) for j, k in enumerate(C.INCUMBENTS)}
    kind, text = ev.verdict_start(s, grid)
    assert kind == "info" and "100 Knoten mit starken Flüssen zuerst" in text and "ohne Anfangswert 110 (10 %" in text and "nach Nummer 110" in text and "schwache Flüsse zuerst 120" in text and "Am meisten Knoten: 130 (schwache Flüsse zuerst, Anfangswert keiner)" in text
    grid[("index", "none")] = _tree(100000, capped=True)
    assert ev.verdict_start(s, grid)[0] == "warning"


def test_growth_verdict():
    g = lambda nodes, cap=False, share=0.001: {"nodes": nodes, "capped": cap, "share": share}
    by_n = {6: {"netlist": [g(30), g(50)]}, 12: {"netlist": [g(1000), g(100000, True, 7.7e-5)]}}
    kind, text = ev.verdict_growth(by_n)
    assert kind == "info" and "n = 6: Median 40 Knoten von 1 956 im vollen Baum" in text and "höchstens 50" in text and "n = 12: Median 50 500 Knoten" in text and "1 von 2 an der Obergrenze" in text and "höchstens 100 000" in text


def test_core_verdict():
    s = ev.Settings()
    trees = {"none": _tree(40000, "none"), "lin": _tree(2000, "lin"), "glb": _tree(200), "pb": _tree(500, "pb"), "max": _tree(200, "max")}
    text = ev.verdict_core(s, _v(trees))[1]
    assert "200 von 109 600 möglichen Knoten" in text and "ohne Schranke wären es 40 000" in text and "mit der linearen Zuordnung 2 000" in text and "projizierten Schranke 500" in text and "Experiment 2 bis 5" in text
    assert "ohne Schranke" not in ev.verdict_core(s, _v({"glb": _tree(200)}))[1]
