"""PDF-Export des aktuellen Ergebnisses (fpdf2). Kernschriften sind latin-1: Umlaute gehen, Sonderzeichen werden ersetzt."""

from __future__ import annotations

from fpdf import FPDF

import sib_constants as C
import sib_tree as T
from sib_evaluation import Settings, count, num, pct

_REPLACE = {"→": "->", "–": "-", "—": "-", "−": "-", "≤": "<=", "≥": ">=", "·": "*", "×": "x", "Δ": "Delta", "↔": "<->", "„": '"', "“": '"', "²": "2", "³": "3", "⁻": "-", "¹": "1", "½": "1/2", "⁴": "4", "⌈": "[", "⌉": "]"}


def _s(text) -> str:
    out = str(text).replace("**", "").replace("`", "")
    for old, new in _REPLACE.items():
        out = out.replace(old, new)
    return out.encode("latin-1", "replace").decode("latin-1")


def build_pdf(s: Settings, v: dict) -> bytes:
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 15)
    pdf.cell(0, 9, _s("Branch and Bound: welche Schranke lohnt im Baum?"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    inst = v["inst"]
    how = "alle Anordnungen aufgezählt (Probe)" if v["exact"] else f"nicht aufgezählt, Obergrenze {count(C.NODE_CAP)} Knoten"
    pdf.multi_cell(0, 5, _s(f"Familie {C.FAMILY_NAMES[s.family]}, {s.n} Bauteile, {inst.rows}x{inst.cols}-Raster, Seed {s.seed}; Reihenfolge: {T.ORDER_NAMES[s.order]}; Anfangswert: {C.INCUMBENT_NAMES[s.incumbent]}; {how}. "
                            "Eine Instanz, kein Befund über die Familie. Einfache Fassungen der Knotenschranken. Alles simuliert."), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(70, 6, "Schranke", border=1)
    pdf.cell(40, 6, "Knoten", border=1)
    pdf.cell(35, 6, "Anteil am vollen Baum", border=1)
    pdf.cell(40, 6, "Ergebnis", border=1)
    pdf.ln()
    pdf.set_font("Helvetica", "", 9)
    for a in v["arts"]:
        t = v["trees"][a]
        pdf.cell(70, 5.5, _s(T.ART_NAMES[a]), border=1)
        pdf.cell(40, 5.5, _s(count(t.nodes)), border=1)
        pdf.cell(35, 5.5, _s(pct(t.share, 3)), border=1)
        pdf.cell(40, 5.5, _s(("nicht zu Ende (Kosten " + num(t.best) + ")") if t.capped else f"Optimum {num(t.best)}"), border=1)
        pdf.ln()
    pdf.ln(3)
    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(0, 5, _s(f"Voller Baum ohne Beschneiden: {count(v['size'])} Knoten. Gilmore-Lawler an der Wurzel: {num(v['glb'])}; projizierte Schranke an der Wurzel: {num(v['pb'])}."), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_font("Helvetica", "I", 8)
    pdf.multi_cell(0, 4, _s("Quelle: schranke-im-baum-demo, Sebastian Hanisch."), new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())
