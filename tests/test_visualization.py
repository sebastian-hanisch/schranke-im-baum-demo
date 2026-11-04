"""Abbildungen: sie entstehen für jede Eingabe, Achsen sind gesperrt, Beschriftungen und Daten stimmen mit den Werten überein; PDF-Export."""

import sib_constants as C
import sib_evaluation as ev
import sib_instance as I
import sib_tree as T
import sib_visualization as V
from sib_pdf_export import build_pdf


def _locked(fig):
    return fig.layout.xaxis.fixedrange and fig.layout.yaxis.fixedrange


def test_nodes_bar_shows_every_art_with_its_count(land6):
    s = ev.Settings("netlist", 6, 35)
    v = ev.instance_data(s, land6[1])
    fig = V.build_nodes_bar(v)
    assert list(fig.data[0].y) == [T.ART_SHORT[a] for a in v["arts"]] and list(fig.data[0].x) == [max(v["trees"][a].nodes, 1) for a in v["arts"]] and fig.layout.xaxis.type == "log" and _locked(fig)
    big = ev.instance_data(ev.Settings("sparse", 12, 100000))
    assert list(V.build_nodes_bar(big).data[0].y) == [T.ART_SHORT["glb"]]


def test_depth_chart_has_one_series_per_art_and_the_counts(land6):
    s = ev.Settings("netlist", 6, 35)
    v = ev.instance_data(s, land6[1])
    fig = V.build_depth(v)
    assert [t.name for t in fig.data] == [T.ART_SHORT[a] for a in v["arts"]] and fig.layout.yaxis.type == "log" and _locked(fig)
    glb = next(t for t in fig.data if t.name == T.ART_SHORT["glb"])
    assert [y for y in glb.y if y] == [d for d in v["trees"]["glb"].depth if d]


def test_inspector_shows_bounds_and_the_cheapest_completion(land6):
    inst, ls = land6
    cb = T.child_bounds(inst.F, inst.D, ("lin", "glb"))
    fig = V.build_inspector(cb, ("lin", "glb"))
    assert [t.name for t in fig.data] == ["linear", "Gilmore–Lawler", "kleinste Fortsetzung"] and list(fig.data[2].y) == cb["min_completion"] and list(fig.data[1].y) == cb["glb"] and _locked(fig)
    big = T.child_bounds(I.make_instance("netlist", 12, 1).F, I.make_instance("netlist", 12, 1).D, ("glb",))
    assert [t.name for t in V.build_inspector(big, ("glb",)).data] == ["Gilmore–Lawler"]


def test_time_bar_and_board(land6):
    inst, ls = land6
    v = ev.instance_data(ev.Settings("netlist", 6, 35), ls)
    fig = V.build_time_bar(v)
    assert len(fig.data) == 2 and list(fig.data[0].x) == [T.ART_SHORT[a] for a in v["arts"]] and _locked(fig)
    assert len(V.build_board(inst, v["perm"], "Test").data[-1].x) == 6


def _by(n=6, seeds=(100000, 100001, 100002)):
    return {f: ev.sweep(f, n, seeds) for f in C.FAMILIES}


def test_sweep_scatter_and_growth_charts():
    by = _by()
    fig = V.build_sweep_bars(6, by, ev.median_of)
    assert [t.name for t in fig.data] == [T.ART_SHORT[a] for a in C.SWEEP_ARTS] and len(fig.data[0].x) == 6 and fig.layout.yaxis.type == "log" and _locked(fig)
    sc = V.build_scatter(6, by)
    assert [t.name for t in sc.data] == [C.FAMILY_NAMES[f] for f in C.FAMILIES] and all(len(t.x) == 3 for t in sc.data) and _locked(sc)
    by_n = {6: {f: ev.growth(f, 6, seeds=(100000, 100001)) for f in C.FAMILIES}, 8: {f: ev.growth(f, 8, seeds=(100000,)) for f in C.FAMILIES}}
    gr = V.build_growth(by_n, ev.median_of)
    assert [t.name for t in gr.data] == ["voller Baum", "Gilmore–Lawler, Median", "Gilmore–Lawler, größte Instanz"] and list(gr.data[0].x) == [6, 8] and list(gr.data[0].y) == [1956, 109600] and _locked(gr)


def test_charts_skip_families_without_rows():
    by = _by()
    by["star"] = []
    assert len(V.build_sweep_bars(6, by, ev.median_of).data[0].x) == 5 and [t.name for t in V.build_scatter(6, by).data] == [C.FAMILY_NAMES[f] for f in C.FAMILIES if f != "star"]


def test_board_chart_for_every_family_and_size(hand):
    for fam in C.FAMILIES:
        for n in (6, 9, 12, 16):
            assert len(V.build_board(I.make_instance(fam, n, 3), list(range(n)), fam).data[-1].x) == n
    assert len(V.build_board(hand, [0, 1, 2], "Hand").data[-1].x) == 3


def test_the_pdf_export_returns_a_pdf_for_an_exact_and_a_capped_instance(land6):
    s = ev.Settings("netlist", 6, 35)
    assert build_pdf(s, ev.instance_data(s, land6[1]))[:5] == b"%PDF-"
    s2 = ev.Settings("uniform", 12, 35, order="index", incumbent="none")
    data = build_pdf(s2, ev.instance_data(s2))
    assert data[:5] == b"%PDF-" and len(data) > 1500
