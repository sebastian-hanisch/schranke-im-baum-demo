"""Plotly-Abbildungen. Alle 2D-Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

from __future__ import annotations

import math

import plotly.graph_objects as go
from plotly.subplots import make_subplots

import sib_constants as C
import sib_tree as T

ART_COLORS = {"none": "#9aa0a6", "lin": "#4c78a8", "glb": "#2F6B65", "pb": "#b08a2e", "max": "#8e6bb0", "da2": "#c0504d"}


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=380, legend_below=True):
    legend = dict(orientation="h", yanchor="top", y=-0.22, x=0) if legend_below else dict(orientation="h", yanchor="bottom", y=1.02, x=0)
    fig.update_layout(height=height + (40 if legend_below else 0), margin=dict(l=10, r=10, t=50, b=10), legend=legend, plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def build_board(inst, p, title: str) -> go.Figure:
    """Plätze als graue Quadrate, Bauteile als Punkte mit Namen auf ihrem Platz; Verbindungen mit Fluss als Linien (Dicke nach dem größten Fluss der Instanz skaliert)."""
    xs_, ys_ = inst.xy[:, 0].astype(float), -inst.xy[:, 1].astype(float)
    pos = [(xs_[int(p[i])], ys_[int(p[i])]) for i in range(inst.n)]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs_, y=ys_, mode="markers", marker=dict(symbol="square", size=34 if inst.n > 12 else 40, color="rgba(150,150,150,0.18)", line=dict(width=1, color="rgba(150,150,150,0.5)")), hoverinfo="skip", showlegend=False))
    fmax = max(1, int(inst.F.max()))
    level = lambda a, b: min(4, 1 + int(3 * int(inst.F[a, b]) / fmax))
    levels = sorted({level(a, b) for a in range(inst.n) for b in range(a + 1, inst.n) if inst.F[a, b]})
    for lv in levels:
        xs, ys = [], []
        for a in range(inst.n):
            for b in range(a + 1, inst.n):
                if inst.F[a, b] and level(a, b) == lv:
                    xs += [pos[a][0], pos[b][0], None]
                    ys += [pos[a][1], pos[b][1], None]
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(width=0.6 + 1.2 * lv, color="rgba(76,120,168,0.35)"), name=("schwacher Fluss", "mittlerer Fluss", "starker Fluss", "stärkster Fluss")[lv - 1], hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=[q[0] for q in pos], y=[q[1] for q in pos], mode="markers+text", text=list(inst.names), textposition="middle center", showlegend=False,
                             marker=dict(size=24 if inst.n > 12 else 28, color=C.COLORS["best"]), textfont=dict(color="white", size=10), hovertemplate="%{text}<extra></extra>"))
    fig.update_layout(title=title)
    fig.update_xaxes(visible=False, range=[xs_.min() - 0.7, xs_.max() + 0.7])
    fig.update_yaxes(visible=False, range=[ys_.min() - 0.7, ys_.max() + 0.7])
    return _base(fig, height=300, legend_below=True)


# ----------------------------------------------------------------------------- Knoten und Zeit

def build_nodes_bar(v: dict) -> go.Figure:
    """Bewertete Knoten je Art der gewählten Instanz (logarithmische Achse), dazu der volle Baum als Marke."""
    arts = [a for a in T.ARTS if a in v["trees"]]
    fig = go.Figure(go.Bar(y=[T.ART_SHORT[a] for a in arts], x=[max(v["trees"][a].nodes, 1) for a in arts], orientation="h", marker_color=[ART_COLORS[a] for a in arts],
                           text=[C.n_text(v["trees"][a].nodes) + (" (Obergrenze)" if v["trees"][a].capped else "") for a in arts], textposition="outside", cliponaxis=False, hovertemplate="%{y}: %{x} Knoten<extra></extra>"))
    fig.add_vline(x=v["size"], line_dash="dot", line_color="rgba(150,150,150,0.8)", annotation_text="voller Baum", annotation_position="top")
    fig.update_xaxes(type="log", title="bewertete Knoten (logarithmisch)", range=[0, max(math.log10(v["size"]), 1) + 0.6])
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(title="Knoten je Schranke")
    return _base(fig, height=300, legend_below=False)


def build_depth(v: dict) -> go.Figure:
    """Bewertete Knoten je Tiefe des Baums, je Art (logarithmische Achse): wo der Baum breit wird und wie früh eine Schranke beschneidet."""
    fig = go.Figure()
    for a in [x for x in T.ARTS if x in v["trees"]]:
        d = v["trees"][a].depth
        fig.add_trace(go.Bar(x=[k + 1 for k in range(len(d))], y=[x if x else None for x in d], name=T.ART_SHORT[a], marker_color=ART_COLORS[a], hovertemplate="Tiefe %{x}: %{y} Knoten<extra></extra>"))
    fig.update_xaxes(title="gesetzte Bauteile (Tiefe)", dtick=1)
    fig.update_yaxes(type="log", title="bewertete Knoten")
    fig.update_layout(title="Wo der Baum breit wird", barmode="group")
    return _base(fig, height=340)


def build_inspector(cb: dict, arts) -> go.Figure:
    """Schranken der Kinder der Wurzel (erstes Bauteil auf Platz j) je Art, dazu die kleinste Fortsetzung (Aufzählung), falls bekannt."""
    n = len(cb[arts[0]])
    fig = go.Figure()
    for a in arts:
        fig.add_trace(go.Bar(x=[f"Platz {j + 1}" for j in range(n)], y=cb[a], name=T.ART_SHORT[a], marker_color=ART_COLORS[a]))
    if cb.get("min_completion") is not None:
        fig.add_trace(go.Scatter(x=[f"Platz {j + 1}" for j in range(n)], y=cb["min_completion"], mode="markers", name="kleinste Fortsetzung", marker=dict(symbol="diamond", size=11, color="#c0504d", line=dict(width=1, color="white"))))
    fig.update_yaxes(title="Kosten")
    fig.update_layout(title="Schranke gegen die kleinste Fortsetzung, je Platz des ersten Bauteils", barmode="group")
    return _base(fig, height=360)


def build_time_bar(v: dict) -> go.Figure:
    """Gemessene Zeit je Knoten und Gesamtzeit je Art (rechnerabhängig; nur für den Vergleich der Arten untereinander)."""
    arts = [a for a in T.ARTS if a in v["trees"]]
    fig = make_subplots(rows=1, cols=2, subplot_titles=("Zeit je Knoten (µs)", "Gesamtzeit (ms)"))
    fig.add_trace(go.Bar(x=[T.ART_SHORT[a] for a in arts], y=[1e6 * v["trees"][a].seconds / max(v["trees"][a].nodes, 1) for a in arts], marker_color=[ART_COLORS[a] for a in arts], showlegend=False), row=1, col=1)
    fig.add_trace(go.Bar(x=[T.ART_SHORT[a] for a in arts], y=[1e3 * v["trees"][a].seconds for a in arts], marker_color=[ART_COLORS[a] for a in arts], showlegend=False), row=1, col=2)
    fig.update_yaxes(type="log")
    return _base(fig, height=320, legend_below=False)


# ----------------------------------------------------------------------------- Vergleiche über feste Instanzen

def build_sweep_bars(n: int, by: dict, median_of) -> go.Figure:
    """Median der Knoten je Familie und Art (logarithmische Achse)."""
    fams = [f for f in C.FAMILIES if by.get(f)]
    fig = go.Figure()
    for a in C.SWEEP_ARTS:
        fig.add_trace(go.Bar(x=[C.FAMILY_NAMES[f] for f in fams], y=[max(median_of(by[f], f"nodes_{a}"), 0.8) for f in fams], name=T.ART_SHORT[a], marker_color=ART_COLORS[a]))
    fig.add_hline(y=T.tree_size(n), line_dash="dot", line_color="rgba(150,150,150,0.8)", annotation_text="voller Baum", annotation_position="top left")
    fig.update_yaxes(type="log", title="bewertete Knoten (Median)")
    fig.update_layout(title=f"Knoten je Schranke und Familie, n = {n}", barmode="group")
    return _base(fig, height=380)


def build_scatter(n: int, by: dict) -> go.Figure:
    """Knoten (Gilmore–Lawler) gegen die Lücke der Wurzelschranke, je Instanz, nach Familie gefärbt."""
    fig = go.Figure()
    for f in C.FAMILIES:
        rows = by.get(f) or []
        if rows:
            fig.add_trace(go.Scatter(x=[100 * r["gap_glb"] for r in rows], y=[max(r["nodes_glb"], 0.8) for r in rows], mode="markers", name=C.FAMILY_NAMES[f], marker=dict(size=9, color=C.COLORS["family"][f]),
                                     hovertemplate="Lücke %{x:.1f} %, %{y} Knoten<extra></extra>"))
    fig.update_xaxes(title="Lücke der Wurzelschranke (Gilmore–Lawler, %)")
    fig.update_yaxes(type="log", title="bewertete Knoten")
    fig.update_layout(title=f"Wurzelschranke und Baumgröße, n = {n}")
    return _base(fig, height=380)


def build_growth(by_n: dict, median_of) -> go.Figure:
    """Median der Knoten (Gilmore–Lawler) gegen n, dazu der volle Baum und die größte Instanz."""
    ns = sorted(by_n)
    rows = {n: [r for f in C.FAMILIES for r in by_n[n].get(f, [])] for n in ns}
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ns, y=[T.tree_size(n) for n in ns], mode="lines+markers", name="voller Baum", line=dict(color="rgba(150,150,150,0.9)", dash="dot")))
    fig.add_trace(go.Scatter(x=ns, y=[max(median_of(rows[n], "nodes"), 0.8) for n in ns], mode="lines+markers", name="Gilmore–Lawler, Median", line=dict(color=ART_COLORS["glb"], width=3)))
    fig.add_trace(go.Scatter(x=ns, y=[max(max(r["nodes"] for r in rows[n]), 0.8) for n in ns], mode="markers", name="Gilmore–Lawler, größte Instanz", marker=dict(symbol="triangle-up", size=11, color="#c0504d")))
    fig.update_xaxes(title="Bauteile n", dtick=1)
    fig.update_yaxes(type="log", title="bewertete Knoten")
    fig.update_layout(title="Wachstum der Knotenzahl")
    return _base(fig, height=360)
