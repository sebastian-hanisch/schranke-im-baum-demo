"""Branch and Bound mit Schranke - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Stück 8 der Reihe „Anordnen: relaxieren und runden“: die Schranken der Reihe (Gilmore–Lawler, projizierte Schranke, Dual Ascent) im Suchbaum des quadratischen Zuordnungsproblems. Gemessen werden bewertete Knoten und Zeit je Knoten:
die Schranke, die an der Wurzel stärker ist, ist im Baum nicht immer die bessere. Aufbau und Regeln: DEMO-PLAYBOOK.md (§2).

Lauffähig mit: streamlit run app.py
"""

import pandas as pd
import streamlit as st

import sib_constants as C
import sib_tree as T
from sib_evaluation import (
    Settings,
    count,
    da_tree,
    de,
    fam,
    family_summary,
    grid_data,
    growth,
    hand_data,
    instance_data,
    median_of,
    num,
    pct,
    sweep,
    verdict_arts,
    verdict_core,
    verdict_corr,
    verdict_da,
    verdict_growth,
    verdict_inspect,
    verdict_start,
    verdict_sweep,
    verdict_tree,
)
from sib_layout import dunkles_design, kopf_css
from sib_pdf_export import build_pdf
from sib_presets import bounds, init_session_state_defaults, load_permalink_settings, randomize_seed, sidebar_presets, sync_query_params
from sib_visualization import build_board, build_depth, build_growth, build_inspector, build_nodes_bar, build_scatter, build_sweep_bars, build_time_bar

st.set_page_config(page_title="Branch and Bound mit Schranke – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner="Rechne den Suchbaum …")
def _instance(settings: Settings):
    return instance_data(settings)


@st.cache_data(show_spinner="Rechne den Dual Ascent im Baum …")
def _da(settings: Settings):
    return da_tree(settings, _instance(settings))


@st.cache_data(show_spinner=False)
def _grid(settings: Settings):
    return grid_data(settings, _instance(settings))


@st.cache_data(show_spinner=False)
def _child_bounds(settings: Settings, arts: tuple):
    v = _instance(settings)
    return T.child_bounds(v["inst"].F, v["inst"].D, arts, settings.order)


@st.cache_data(show_spinner=False)
def _sweep(family, n):
    return sweep(family, n)


@st.cache_data(show_spinner=False)
def _growth(family, n):
    return growth(family, n)


def verdict(pair):
    kind, text = pair
    getattr(st, kind)(text)


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in sib_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("🌳 Branch and Bound mit Schranke")
st.markdown(
    """
**Welche Schranke lohnt im Suchbaum?** Dieselbe Aufgabe wie in Stück 1 bis 7: `n` Bauteile auf `n` Plätze, Kosten gleich der Summe aus **Fluss mal Abstand** über alle Paare. Hier wird das Optimum **bewiesen**, nicht nur gefunden: ein Baum setzt Bauteil für Bauteil auf einen Platz (ein **Knoten** ist eine
Teilzuordnung), und eine **Schranke** sagt für jeden Knoten, was jede Fortsetzung mindestens kostet. Ist das schon so viel wie die beste bekannte Anordnung, wird der ganze Ast **beschnitten**. Je schärfer die Schranke, desto weniger Knoten; je schärfer, desto mehr Rechenarbeit je Knoten.
Gemessen werden die Schranken der Reihe (Stück 3 bis 5) im Baum: **Gilmore–Lawler** (eine lineare Zuordnung je Knoten), die **projizierte Schranke** (Spektrum, Stück 4) und **zwei Runden Dual Ascent** (Stück 5), dazu zwei einfache Maßstäbe.
Die sechs Familien der Flussmatrix sind **eigene, einfache Erfindungen** (aus Stück 2); alle Knotenschranken sind **eigene einfache Fassungen**, nicht die Verfahren der Literatur. Stück 8 der Reihe „Anordnen: relaxieren und runden“.

Weiter unten: **fünf Experimente** (**🔬**), **🚧 Wo die Annahmen enden** und der Expander **📐 Mathematische Formulierung**.
"""
)

with st.expander("So funktioniert es", expanded=True):
    st.markdown(
        """
1. **Der Baum:** das erste Bauteil wird auf jeden der `n` Plätze gesetzt (n Knoten), dann das zweite auf jeden freien Platz, und so weiter. Ohne Beschneiden hat der Baum `Σ n!/(n−k)!` Knoten (n = 8: 109 600; n = 12: über eine Milliarde). **Ein Knoten zählt, wenn seine Schranke berechnet wird.**
2. **Die Schranke eines Knotens:** feste Kosten der gesetzten Paare plus eine untere Abschätzung des Rests. **Ohne:** nur die festen Kosten. **Linear:** dazu die kleinste Zuordnung der Wechselwirkung zwischen freien und gesetzten Bauteilen. **Gilmore–Lawler:** dieselbe Zuordnung, in der zusätzlich für jedes freie Bauteil auf jedem freien Platz das kleinste Skalarprodukt der übrigen Flüsse und Abstände steht.
   **Projiziert:** die projizierte Schranke (Stück 4) der freien Teilmatrizen plus die lineare Zuordnung. **Dual Ascent:** zwei Runden aus Stück 5 auf dem Rest.
3. **Beschneiden:** ein Knoten fällt weg, wenn seine Schranke (aufgerundet, die Kosten sind ganzzahlig) nicht unter den besten bekannten Kosten liegt. Der **Anfangswert** ist die beste von 200 steilsten Abstiegen (Stück 3); gefundene bessere Anordnungen senken ihn.
4. **Die Reihenfolge:** welches Bauteil als nächstes gesetzt wird (Standard: das mit dem größten Gesamtfluss) und welcher Ast zuerst (der mit der kleinsten Schranke).
5. **Feste Instanzen:** Vergleiche laufen über feste Seeds (n = 6: 20, n = 8: 10 Instanzen je Familie), nie über einen einzelnen.
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Die Instanz**")
    family = st.selectbox("Familie der Flussmatrix", C.FAMILIES, key="family_select", format_func=lambda f: C.FAMILY_NAMES[f], help="Wie der Fluss zwischen den Bauteilen verteilt ist. Die Beschreibung steht unter dem Regler.")
    st.caption(C.FAMILY_HELP[family])
    n = st.select_slider("Bauteile n", options=C.SIZES, key="n_select", help="Bis n = 8 rechnet die App alle Schranken sofort; n = 9 auf Knopfdruck (ohne Schranke rund eine Million Knoten); ab n = 12 nur mit Gilmore–Lawler und einer Obergrenze von 100 000 Knoten.")
    seed = st.number_input("Zufalls-Seed", *bounds("seed_input"), key="seed_input", step=1)
    st.button("🎲 Neue Instanz", width="stretch", on_click=randomize_seed)
    st.markdown("**Die Suche**")
    order = st.selectbox("Reihenfolge der Bauteile", C.ORDERS, key="order_select", format_func=lambda o: T.ORDER_NAMES[o], help="Welches Bauteil als nächstes gesetzt wird: nach Gesamtfluss absteigend (Standard), nach Nummer oder nach Gesamtfluss aufsteigend.")
    incumbent = st.selectbox("Anfangswert", C.INCUMBENTS, key="incumbent_select", format_func=lambda k: C.INCUMBENT_NAMES[k], help="Die Kosten, mit denen die Suche beginnt: die beste von 200 steilsten Abstiegen, ein Abstieg oder keiner (unendlich).")

sync_query_params({"family_select": family, "n_select": int(n), "seed_input": int(seed), "order_select": order, "incumbent_select": incumbent})
settings = Settings(family, int(n), int(seed), order, incumbent)

done = st.session_state.setdefault("gates_done", set())
gated = (settings.n == 9 or settings.n >= 12) and (settings.family, settings.n, settings.seed, settings.order, settings.incumbent) not in done
if gated:
    if settings.n == 9:
        st.info("Bei n = 9 sind es 362 880 Anordnungen (die Aufzählung für die Probe) und ohne Schranke rund eine Million Knoten; die Rechnung dauert rund eine Minute (auf Streamlit Cloud länger). Mit dem Knopf starten:")
    else:
        st.info(f"Bei n = {settings.n} rechnet die App nur die Gilmore–Lawler-Schranke, höchstens {count(C.NODE_CAP)} Knoten; die Rechnung dauert bis zu einer Minute (auf Streamlit Cloud länger). Mit dem Knopf starten:")
    if st.button(f"⏱️ n = {settings.n} rechnen", key="n9_button" if settings.n == 9 else "big_button"):
        done.add((settings.family, settings.n, settings.seed, settings.order, settings.incumbent))
        st.rerun()
else:
    v = _instance(settings)
    glb = v["trees"]["glb"]
    ref_label = "Optimum" if v["exact"] else ("Optimum (bewiesen)" if glb.optimal else "Beste gefundene Lösung")

    # --- Ergebnis ------------------------------------------------------------------------------------------------------------------------------

    st.markdown("## 🎯 Ergebnis")
    m1, m2, m3 = st.columns(3)
    m4, m5 = st.columns(2)
    m1.metric("Knoten mit Gilmore–Lawler", count(glb.nodes), delta=f"{pct(glb.share, 3 if glb.share < 0.01 else 1)} des vollen Baums", delta_color="off", help="Bewertete Teilzuordnungen im Suchbaum mit der Gilmore–Lawler-Schranke.")
    m2.metric("Voller Baum", count(v["size"]), help="Zahl der Knoten ohne jedes Beschneiden: Σ n!/(n−k)!.")
    m3.metric("Wurzelschranke", num(glb.root), delta=(f"Lücke {pct(v['gap_glb'], 1)}" if v["exact"] else None), delta_color="off", help="Gilmore–Lawler-Schranke vor dem ersten Schritt (Stück 3).")
    m4.metric(ref_label, str(int(glb.best)), help="Die kleinsten Kosten aller n! Anordnungen (aufgezählt)." if v["exact"] else ("Der Baum ist zu Ende gerechnet: bewiesen." if glb.optimal else "Beste gefundene Kosten; der Baum wurde an der Obergrenze abgebrochen, kein Beweis."))
    m5.metric("Anfangswert", "keiner" if v["inc"] is None else str(int(v["inc"])), help="Kosten, mit denen die Suche beginnt.")
    st.plotly_chart(build_nodes_bar(v), width="stretch", key="nodes_chart")

    if st.button("📄 PDF des aktuellen Ergebnisses erstellen", key="pdf_make"):
        st.session_state["pdf_made"] = (settings, build_pdf(settings, v))
    made = st.session_state.get("pdf_made")
    if made and made[0] == settings:
        st.download_button("⬇️ PDF herunterladen", data=made[1], file_name="schranke-im-baum.pdf", mime="application/pdf", key="pdf_download")

    # --- Kernfrage -----------------------------------------------------------------------------------------------------------------------------

    st.markdown("## ❓ Kernfrage: Welche Schranke lohnt im Baum?")
    verdict(verdict_core(settings, v))

    st.markdown("---")

    # --- Experiment 1 ---------------------------------------------------------------------------------------------------------------------------

    st.subheader("🔬 Experiment 1: Der Baum und die Schranke im Knoten")
    st.caption("Links die beste Anordnung, die der Baum findet; rechts, wie viele Knoten in welcher Tiefe bewertet werden (logarithmische Achse). Darunter die Schranken der Kinder der Wurzel gegen die kleinste Fortsetzung.")
    e1, e2 = st.columns(2)
    with e1:
        perm = v["perm"]
        if perm is not None:
            st.plotly_chart(build_board(v["inst"], perm, f"Beste Anordnung (Kosten {int(glb.best)})"), width="stretch", key="board_chart")
        else:
            st.info("Der Anfangswert war schon bestmöglich und der Baum wurde nicht zu Ende gerechnet: eine Anordnung zu den besten Kosten liegt nicht vor.")
    with e2:
        st.plotly_chart(build_depth(v), width="stretch", key="depth_chart")
    verdict(verdict_tree(settings, v))
    if settings.n <= 9:
        cb = _child_bounds(settings, v["arts"])
        st.plotly_chart(build_inspector(cb, v["arts"]), width="stretch", key="inspector_chart")
        verdict(verdict_inspect(cb, v["arts"]))
    with st.expander("Handbeispiel zum Nachrechnen"):
        h = hand_data()
        cb_h = h["child"]
        st.markdown(
            f"**Drei Bauteile auf einer Zeile** (Plätze mit Abständen 1, 1 und 2), Fluss A–B 5, B–C 1, A–C 0; Reihenfolge: B (Gesamtfluss 6), A (5), C (1). Das erste Bauteil B auf Platz 1, 2, 3: Schranke **ohne** {', '.join(num(x) for x in cb_h['none'])}; "
            f"**linear** {', '.join(num(x) for x in cb_h['lin'])}; **Gilmore–Lawler** {', '.join(num(x) for x in cb_h['glb'])}; kleinste Fortsetzung {', '.join(str(x) for x in cb_h['min_completion'])}. Von Hand: B in der Mitte, A und C auf den Rändern; "
            f"A kostet 5·1, C kostet 1·1: zusammen 6. B auf einem Rand: A auf dem Platz daneben (5·1), C auf dem entfernten (1·2) = 7. **Ohne Anfangswert** bewertet der Baum {h['full'].nodes} Knoten (je Tiefe {', '.join(str(x) for x in h['full'].depth)}), "
            f"findet Kosten {num(h['full'].best)} und beschneidet die beiden Randäste; **mit Anfangswert 6** sind es {h['with_inc'].nodes}: schon die drei Kinder der Wurzel genügen für den Beweis."
        )

    st.markdown("---")

    # --- Experiment 2 ---------------------------------------------------------------------------------------------------------------------------

    st.subheader("🔬 Experiment 2: Welche Schranke lohnt?")
    if settings.n >= 12:
        st.info("Ab n = 12 wird nur mit Gilmore–Lawler gerechnet; der Vergleich der Arten (und Experiment 4) steht für n = 6, 8 und 9 zur Verfügung.")
    else:
        st.caption("Bewertete Knoten je Art (links, logarithmisch) und die gemessene Zeit (rechts; rechnerabhängig, nur zum Vergleich der Arten). Die stärkere Schranke spart Knoten, kostet aber Rechenarbeit je Knoten.")
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(build_nodes_bar(v), width="stretch", key="nodes_chart_2")
        with c2:
            st.plotly_chart(build_time_bar(v), width="stretch", key="time_chart")
        verdict(verdict_arts(settings, v))
        if settings.n in C.DA_SIZES:
            key = (settings.family, settings.n, settings.seed, settings.order, settings.incumbent)
            da_done = st.session_state.setdefault("da_done", set())
            if key not in da_done:
                st.info("Zwei Runden Dual Ascent (Stück 5) je Knoten rechnen rund eine halbe Minute (auf Streamlit Cloud länger). Mit dem Knopf starten:")
                if st.button("⏱️ Dual Ascent im Baum rechnen", key="da_button"):
                    da_done.add(key)
                    st.rerun()
            else:
                dt = _da(settings)
                st.markdown(f"**Dual Ascent, zwei Runden:** {count(dt.nodes)} Knoten in {de(dt.seconds, 1)} s (Gilmore–Lawler: {count(glb.nodes)} Knoten in {de(glb.seconds, 2)} s; rechnerabhängig).")
                verdict(verdict_da(settings, glb, dt))

    st.markdown("---")

# --- Vergleich über feste Instanzen (Experiment 2 und 3) -----------------------------------------------------------------------------------------

st.subheader("🔬 Vergleich über feste Instanzen (zu Experiment 2 und 3)")
st.caption("Je Familie feste Instanzen, Optimum aufgezählt: Median der bewerteten Knoten je Art, dann die Baumgröße gegen die Lücke der Wurzelschranke und gegen die Dichte des Flusses. Anfangswert: beste von 200 Abstiegen, Reihenfolge nach Fluss. Die Größe wählen und starten.")
sweep_n = st.radio("Größe des Vergleichs", C.SWEEP_SIZES, key="sweep_n", horizontal=True, format_func=lambda x: f"n = {x}")
sdone = st.session_state.setdefault("sweeps_done", {})
if not sdone.get(sweep_n):
    wait = "rund eine halbe Minute" if sweep_n == 6 else "rund zwei bis drei Minuten (auf Streamlit Cloud länger)"
    st.info(f"Der Vergleich für n = {sweep_n} rechnet 6 Reihen zu je {len(C.SWEEP_SEEDS_N[sweep_n])} Instanzen (mit Aufzählung und vier Arten) und dauert {wait}. Mit dem Knopf starten:")
    if st.button(f"⏱️ Vergleich für n = {sweep_n} rechnen", key=f"sweep_button_{sweep_n}"):
        bar = st.progress(0.0, text="Rechne die Familien …")
        for i, f in enumerate(C.FAMILIES):
            _sweep(f, sweep_n)
            bar.progress((i + 1) / len(C.FAMILIES), text=f"{C.FAMILY_NAMES[f]} fertig")
        sdone[sweep_n] = True
        st.rerun()
else:
    by = {f: _sweep(f, sweep_n) for f in C.FAMILIES}
    st.markdown("**Welche Schranke lohnt?** (Experiment 2): Median der Knoten je Familie und Art (logarithmische Achse).")
    st.plotly_chart(build_sweep_bars(sweep_n, by, median_of), width="stretch", key="sweep_chart")
    table = []
    for f in C.FAMILIES:
        s_ = family_summary(by[f])
        table.append({"Familie": fam(f), "ohne": count(s_["none"]), "linear": count(s_["lin"]), "Gilmore–Lawler": count(s_["glb"]), "projiziert": count(s_["pb"]), "projiziert besser an der Wurzel": f"{s_['pb_root_better']} von {s_['count']}",
                      "projiziert mehr Knoten": f"{s_['pb_more']} von {s_['count']}"})
    st.dataframe(pd.DataFrame(table), hide_index=True, width="stretch")
    verdict(verdict_sweep(sweep_n, by))

    st.markdown("**Wurzelschärfe und Baumgröße** (Experiment 3): jede Instanz ein Punkt; die Rangkorrelation steht im Text.")
    st.plotly_chart(build_scatter(sweep_n, by), width="stretch", key="scatter_chart")
    table = []
    for f in C.FAMILIES:
        s_ = family_summary(by[f])
        table.append({"Familie": fam(f), "Lücke der Wurzelschranke (Median)": pct(s_["gap_glb"], 1), "Dichte des Flusses (Median)": pct(s_["density"]), "Knoten Gilmore–Lawler (Median)": count(s_["glb"]), "Anfangswert = Optimum": f"{s_['inc_hit']} von {s_['count']}"})
    st.dataframe(pd.DataFrame(table), hide_index=True, width="stretch")
    verdict(verdict_corr(sweep_n, by))

st.markdown("---")

# --- Experiment 4: Anfangswert und Reihenfolge -----------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 4: Anfangswert und Reihenfolge")
if gated or settings.n >= 12:
    st.info("Für die gewählte Instanz (n = 6, 8, 9, nach dem Start bei n = 9) rechnet die App alle neun Kombinationen aus Reihenfolge und Anfangswert mit Gilmore–Lawler.")
else:
    st.caption("Knoten (Gilmore–Lawler) für jede Reihenfolge der Bauteile und jeden Anfangswert, gleiche Instanz wie oben.")
    g = _grid(settings)
    rows = [{"Reihenfolge": T.ORDER_NAMES[o], **{C.INCUMBENT_NAMES[k]: count(g[(o, k)].nodes) for k in C.INCUMBENTS}} for o in C.ORDERS]
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    verdict(verdict_start(settings, g))

st.markdown("---")

# --- Experiment 5: Wachstum und Grenze ---------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 5: Wachstum und Grenze")
st.caption("Knoten (Gilmore–Lawler) für n = 6, 8, 9 und 12 über feste Instanzen (n = 6: 20, n = 8: 10, n = 9: 5, n = 12: 5 je Familie; bei n = 12 höchstens 100 000 Knoten). Der volle Baum wächst viel schneller.")
if not st.session_state.get("growth_ok"):
    st.info("Die Rechnung dauert einige Minuten (auf Streamlit Cloud länger; bei n = 12 sind einzelne Bäume groß). Mit dem Knopf starten:")
    if st.button("⏱️ Wachstum rechnen (n = 6, 8, 9, 12)", key="growth_button"):
        bar = st.progress(0.0, text="Rechne die Instanzen …")
        todo = [(f, m) for m in C.GROWTH_SIZES for f in C.FAMILIES]
        for i, (f, m) in enumerate(todo):
            _growth(f, m)
            bar.progress((i + 1) / len(todo), text=f"n = {m}, {C.FAMILY_NAMES[f]} fertig")
        st.session_state["growth_ok"] = True
        st.rerun()
else:
    by_n = {m: {f: _growth(f, m) for f in C.FAMILIES} for m in C.GROWTH_SIZES}
    st.plotly_chart(build_growth(by_n, median_of), width="stretch", key="growth_chart")
    table = []
    for m in C.GROWTH_SIZES:
        for f in C.FAMILIES:
            rows_ = by_n[m][f]
            table.append({"n": m, "Familie": fam(f), "Knoten (Median)": count(median_of(rows_, "nodes")), "größte Instanz": count(max(r["nodes"] for r in rows_)), "an der Obergrenze": f"{sum(r['capped'] for r in rows_)} von {len(rows_)}"})
    st.dataframe(pd.DataFrame(table), hide_index=True, width="stretch")
    verdict(verdict_growth(by_n))

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Alle Knotenschranken sind einfache Eigenfassungen** | Die projizierte Schranke im Knoten ist eine **einfache Summe** (linearer und quadratischer Teil getrennt abgeschätzt), nicht die Originalform der Literatur; der Befund „im Baum schlechter als Gilmore–Lawler“ gilt für diese Fassung. Der Dual Ascent ist die einfache Fassung aus Stück 5. | – |
| **Die sechs Familien sind erfunden** | Echte Platinen oder QAPLIB-Instanzen haben andere Strukturen; Aussagen wie „gleichverteilte Flüsse sind am schwersten“ gelten nur für diese Familien. | – |
| **Der Beweis endet bei n = 12 bis 16** | Bei n = 12 sind einzelne Bäume über 100 000 Knoten groß, bei n = 16 reicht die Obergrenze in fast allen Instanzen nicht. Die Literatur nennt mit viel Rechenzeit etwa n = 30 (Angabe aus zweiter Hand, nicht nachgelesen). | Stück 7 (SDP), Stück 13 (Symmetrie) |
| **Keine Symmetrie** | Das Raster hat Spiegelungen, der Baum zählt gleichwertige Äste mehrfach. | Stück 13 |
| **Feste Reihenfolge der Bauteile** | Es wird nicht dynamisch das nächste Bauteil gewählt; andere Reihenfolgen ändern die Knotenzahl (Experiment 4). | – |
| **Zeiten sind rechnerabhängig** | Die gemessene Zeit je Knoten steht nur zum Vergleich der Arten untereinander; auf Streamlit Cloud ist alles langsamer. | – |
| **Wenige Instanzen** | n = 6: 20 Instanzen je Familie, n = 8: 10, n = 9: 5, n = 12: 5; Unterschiede zwischen Familien sind nicht belastbar, wenn sie klein sind. | – |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Die Aufgabe (wie in Stück 1).** Symmetrischer Fluss $F$, symmetrischer Abstand $D$ der Plätze, beide mit Diagonale 0; für die Anordnung $p$ ($p_i$ = Platz des Bauteils $i$) sind die Kosten $\mathrm{cost}(p) = \sum_{i<k} F_{ik}\, D_{p_i p_k}$.

**Knoten.** Eine Teilzuordnung setzt die Bauteile $a \in A$ auf die Plätze $p_a$; frei bleiben die Bauteile $R$ und die Plätze $S$ ($|R| = |S| = r$). Jede Fortsetzung $q: R \to S$ kostet
$$\underbrace{\sum_{a<b \in A} F_{ab} D_{p_a p_b}}_{\text{fest}} \;+\; \underbrace{\sum_{i \in R} c_{i, q_i}}_{\text{linear}} \;+\; \underbrace{\sum_{i<k \in R} F_{ik} D_{q_i q_k}}_{\text{quadratisch}}, \qquad c_{ij} = \sum_{a \in A} F_{ia} D_{j\, p_a}.$$

**Schranken des Knotens.** (lin) $\text{fest} + \min_q \sum_i c_{i q_i}$ (lineare Zuordnung). (glb) Für das freie Bauteil $i$ auf dem freien Platz $j$ kosten die übrigen freien Paare mindestens $L_{ij}$ = kleinstes Skalarprodukt der Flusszeile von $i$ (unter $R$, aufsteigend) mit der Abstandszeile von $j$ (unter $S$, absteigend); jedes Paar kommt in $\sum_i L_{i q_i}$ zweimal vor:
$$\text{fest} + \min_q \sum_i \left(c_{i q_i} + \tfrac12 L_{i q_i}\right).$$
(pb) Die projizierte Schranke (Stück 4) der Teilmatrizen $F_{RR}$, $D_{SS}$ schätzt den quadratischen Teil, die lineare Zuordnung über $c$ den linearen Teil; die Summe zweier Minima ist höchstens das Minimum der Summe, die Schranke ist also gültig, aber sie verschenkt das Zusammenspiel beider Teile. (da2) Zwei Runden Dual Ascent (Stück 5) mit $c$ als lineare Anfangskosten; Runde 1 ist genau (glb).

**Beschneiden.** Sind die Kosten ganzzahlig, genügt $\lceil \text{Schranke} \rceil \ge U$ für den besten bekannten Wert $U$. Bei festem Anfangswert und fester Reihenfolge gilt: ist eine Schranke in **jedem** Knoten mindestens so groß wie eine andere, bewertet ihr Baum nur Knoten, die auch der andere bewertet (none ⊆ lin ⊆ glb ⊆ max).

**Voller Baum.** Ohne Beschneiden hat der Baum $\sum_{k=1}^{n} n!/(n-k)! = \lfloor e \cdot n! \rfloor - 1$ Knoten.

**Literatur.** Gilmore (1962) und Lawler (1963) (Gilmore–Lawler-Schranke und Branch and Bound), R. E. Burkard u. a. und M. Loiola u. a. (Überblicke), P. Hahn und T. Grant (Dual Ascent), K. M. Anstreicher (Branch and Bound mit QP-Schranke): Angaben aus der Fachliteratur übernommen, hier **nicht nachgelesen**.
Die Zerlegung der Kosten, die Gültigkeit der Knotenschranken und die Zählung sind **eigene** Herleitungen und werden durch Tests (Aufzählung aller Fortsetzungen, Handrechnung, `scipy`) geprüft. Die Zahlen dieser Demo sind eigene Rechnungen an eigenen, erfundenen Familien.
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html)."
)
