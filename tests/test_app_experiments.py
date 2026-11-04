"""Pfade der App, die der Rauchtest nicht erreicht: die Experimente im Seiteninhalt, PDF, jede Familie, große Instanzen, die Rechenknöpfe (DEMO-PLAYBOOK §1d)."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

import sib_constants as C

APP = str(Path(__file__).resolve().parent.parent / "app.py")
KIND = {"family_select": "selectbox", "n_select": "select_slider", "seed_input": "number_input", "order_select": "selectbox", "incumbent_select": "selectbox"}


def _app(**state) -> AppTest:
    at = AppTest.from_file(APP, default_timeout=300)
    at.run()
    for key, value in state.items():
        getattr(at.sidebar, KIND[key])(key=key).set_value(value)
    if state:
        at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _texts(at):
    return " ".join(str(e.value) for e in list(at.success) + list(at.info) + list(at.warning) + list(at.error) + list(at.markdown))


def test_default_page_shows_the_metrics_and_the_verdicts():
    at = _app()
    values = {m.label: m.value for m in at.metric}
    assert set(values) == {"Knoten mit Gilmore–Lawler", "Voller Baum", "Wurzelschranke", "Optimum", "Anfangswert"}
    assert values["Optimum"] == "31" and values["Wurzelschranke"] == "27" and values["Voller Baum"] == "109 600" and values["Knoten mit Gilmore–Lawler"] == "64"
    text = _texts(at)
    for part in ("Familie **Netzliste**, 8 Bauteile, Raster 2×4, Seed 35", "bewertet der Suchbaum **64** Knoten", "Knoten je Art: ohne 17 024; linear 3 404; Gilmore–Lawler 64; projiziert 560; Maximum 64", "scharf in", "Experiment 2 bis 5"):
        assert part in text, part


def test_the_experiments_the_hand_example_the_limits_table_and_the_formulation_are_on_the_page():
    at = _app()
    headings = [s.value for s in at.subheader]
    assert [h.split(":")[0] for h in headings if h.startswith("🔬 Experiment")] == [f"🔬 Experiment {i}" for i in (1, 2, 4, 5)] and "🔬 Vergleich über feste Instanzen (zu Experiment 2 und 3)" in headings and "🚧 Wo die Annahmen enden" in headings
    assert [e.label for e in at.expander] == ["So funktioniert es", "Handbeispiel zum Nachrechnen", "📐 Mathematische Formulierung"]
    assert not at.error and len(at.get("plotly_chart")) == 6
    assert any("Ohne Anfangswert" in str(m.value) or "**Ohne Anfangswert**" in str(m.value) for m in at.markdown)


def test_every_family_renders_and_a_size_beyond_nine_waits_for_the_button(monkeypatch):
    for fam in C.FAMILIES:
        at = _app(family_select=fam, n_select=6)
        assert f"Familie **{C.FAMILY_NAMES[fam]}**" in _texts(at) and len(at.get("plotly_chart")) == 6
    monkeypatch.setattr(C, "NODE_CAP", 3000)
    at = _app(n_select=12)
    assert any(b.label == "⏱️ n = 12 rechnen" for b in at.button) and not at.metric
    at.button(key="big_button").click().run()
    assert not at.exception
    values = {m.label: m.value for m in at.metric}
    assert "Knoten mit Gilmore–Lawler" in values and "Optimum" not in values and "Voller Baum" in values and values["Voller Baum"] == "1 302 061 344"
    assert any("ab n = 12" in str(i.value) or "Ab n = 12" in str(i.value) for i in at.info)


def test_nine_waits_for_the_button():
    at9 = _app(n_select=9)
    assert any("362 880 Anordnungen" in str(i.value) for i in at9.info) and any(b.label == "⏱️ n = 9 rechnen" for b in at9.button)
    assert not at9.metric and "Familie **" not in _texts(at9)


def test_order_and_incumbent_change_the_page():
    base = {m.label: m.value for m in _app(n_select=6).metric}["Knoten mit Gilmore–Lawler"]
    light = {m.label: m.value for m in _app(n_select=6, order_select="light", incumbent_select="none").metric}["Knoten mit Gilmore–Lawler"]
    assert base != light


def test_the_pdf_button_makes_a_download():
    at = _app(n_select=6)
    at.button(key="pdf_make").click().run()
    assert not at.exception
    assert any(d.proto.label == "⬇️ PDF herunterladen" for d in at.get("download_button"))


def test_dual_ascent_button_fills_the_comparison():
    at = _app(n_select=6)
    assert any(b.label == "⏱️ Dual Ascent im Baum rechnen" for b in at.button)
    at.button(key="da_button").click().run()
    assert not at.exception and any("Dual Ascent, zwei Runden:" in str(m.value) for m in at.markdown) and any("Zwei Runden Dual Ascent bewerten" in str(i.value) for i in at.info)


def test_the_comparison_for_six_components_fills_the_sweep_section():
    at = _app(n_select=6)
    assert any(b.label == "⏱️ Vergleich für n = 6 rechnen" for b in at.button)
    at.button(key="sweep_button_6").click().run()
    assert not at.exception
    text = _texts(at)
    for part in ("Bei n = 6, Median über 120 Instanzen", "Rangkorrelation der Knotenzahl (Gilmore–Lawler)", "Median der Knoten je Familie"):
        assert part in text, part
    assert len(at.get("plotly_chart")) == 6 + 2


def test_the_size_choice_of_the_comparison_switches_the_button():
    at = _app()
    at.radio(key="sweep_n").set_value(8).run()
    assert any(b.label == "⏱️ Vergleich für n = 8 rechnen" for b in at.button) and not at.exception


def test_the_growth_button_fills_experiment_five(monkeypatch):
    monkeypatch.setattr(C, "NODE_CAP", 2000)                       # nur für die Geschwindigkeit des Tests: die echte Obergrenze steht in den Zahlen der README
    monkeypatch.setattr(C, "GROWTH_SEEDS_N", {6: C.SWEEP_SEEDS[:2], 8: C.SWEEP_SEEDS[:1], 9: C.SWEEP_SEEDS[:1], 12: C.SWEEP_SEEDS[:1]})
    at = _app(n_select=6)
    assert any(b.label == "⏱️ Wachstum rechnen (n = 6, 8, 9, 12)" for b in at.button)
    at.button(key="growth_button").click().run()
    assert not at.exception
    text = _texts(at)
    assert "Gilmore–Lawler, Median über alle Instanzen" in text and "n = 12: Median" in text and len(at.get("plotly_chart")) == 6 + 1
