"""Kennzahlen, Vergleiche über Instanzen und Verdikte. Jedes Verdikt ist eine reine Funktion (Art, Text); die App ruft st.<Art>(Text).

Alle Aussagen gelten für die gerechneten Instanzen, die sechs erfundenen Familien (siehe README) und die **einfachen** Fassungen dieser Demo (Knotenschranken nach eigener Herleitung); Zeiten stehen nie in Verdikten.
Die Zahl der Knoten ist die Zahl der bewerteten Teilzuordnungen (Kinder) im Suchbaum; der volle Baum ohne Beschneiden hat Σ n!/(n−k)! Knoten. Die Lücke der Wurzelschranke ist (Optimum − Schranke) / Optimum."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

import sib_bound as B
import sib_constants as C
import sib_landscape as L
import sib_spectral as S
import sib_tree as T
from sib_instance import hand_instance, make_instance


@dataclass(frozen=True)
class Settings:
    family: str = C.DEFAULT_FAMILY
    n: int = C.DEFAULT_N
    seed: int = C.DEFAULT_SEED
    order: str = C.DEFAULT_ORDER
    incumbent: str = C.DEFAULT_INCUMBENT


# ----------------------------------------------------------------------------- Formatierung

def de(x: float, digits: int = 2) -> str:
    """Zahl mit deutschem Dezimalkomma und typografischem Minuszeichen."""
    return f"{x:.{digits}f}".replace(".", ",").replace("-", "−")


def pct(x: float, digits: int = 0) -> str:
    return de(100.0 * x, digits) + " %"


def fam(name: str) -> str:
    return C.FAMILY_NAMES.get(name, name)


def num(x: float) -> str:
    """Ganze Zahl ohne Nachkommastelle, sonst eine Stelle: 27 / 27,5 / −12,1."""
    return str(int(round(x))) if abs(x - round(x)) < 1e-9 else de(x, 1)


def count(x: float) -> str:
    """Anzahl mit Leerzeichen als Tausendertrenner: 109600 → „109 600“."""
    return C.n_text(int(round(x)))


def median_of(rows: list, key: str) -> float:
    return float(np.median([r[key] for r in rows]))


def rank(x) -> np.ndarray:
    """Ränge (1-basiert, bei Gleichstand der Mittelwert)."""
    x = np.asarray(x, dtype=float)
    order = np.argsort(x, kind="stable")
    r = np.empty(len(x))
    i = 0
    while i < len(x):
        j = i
        while j + 1 < len(x) and x[order[j + 1]] == x[order[i]]:
            j += 1
        r[order[i:j + 1]] = (i + j) / 2 + 1
        i = j + 1
    return r


def spearman(a, b) -> float:
    """Rangkorrelation nach Spearman (NaN, wenn eine Reihe konstant ist)."""
    ra, rb = rank(a), rank(b)
    if ra.std() == 0 or rb.std() == 0:
        return float("nan")
    return float(np.corrcoef(ra, rb)[0, 1])


def density(F) -> float:
    n = len(F)
    return float((np.asarray(F) > 0).sum() / (n * (n - 1)))


# ----------------------------------------------------------------------------- Anfangswert und Instanz

def incumbent_value(inst, seed: int, kind: str):
    """Kosten der Anordnung, mit der die Suche beginnt: None (keine), ein Abstieg oder die beste von 200 Abstiegen."""
    if kind == "none":
        return None
    if kind == "descent1":
        return B.best_found(inst.F, inst.D, seed, 1)[0]
    if kind == "descents200":
        return B.best_found(inst.F, inst.D, seed, C.STARTS)[0]
    raise ValueError(f"unbekannter Anfangswert {kind!r}")


def landscape_of(s: Settings) -> L.Landscape:
    return L.landscape(make_instance(s.family, s.n, s.seed))


def arts_for(n: int) -> tuple:
    return C.LIVE_ARTS if n in C.EXACT_SIZES else ("glb",)


def cap_for(n: int):
    return None if n in C.EXACT_SIZES else C.NODE_CAP


def instance_data(s: Settings, ls: L.Landscape | None = None) -> dict:
    """Die gewählte Instanz: Anfangswert, Suche mit jeder Art (bis n = 9 fünf, ab n = 12 nur Gilmore–Lawler mit Obergrenze), Wurzelschranken, Optimum (aufgezählt, wenn möglich)."""
    inst = make_instance(s.family, s.n, s.seed)
    exact = s.n in C.EXACT_SIZES
    if exact and ls is None:
        ls = L.landscape(inst)
    inc = incumbent_value(inst, s.seed, s.incumbent)
    arts = arts_for(s.n)
    trees = {a: T.solve(inst.F, inst.D, a, inc, s.order, cap_for(s.n)) for a in arts}
    glb = B.gilmore_lawler(inst.F, inst.D).glb
    pb = S.spectral_bounds(inst.F, inst.D).pb
    opt = int(ls.opt) if exact else None
    perm = next((t.perm for t in trees.values() if t.perm is not None), None)
    if perm is None and ls is not None:
        perm = [int(x) for x in ls.optima[0]]                 # der Anfangswert war schon das Optimum: eine optimale Anordnung aus der Aufzählung
    best = min(t.best for t in trees.values())
    ref = opt if opt is not None else int(best)
    return {"inst": inst, "exact": exact, "opt": opt, "ref": ref, "inc": inc, "perm": perm, "arts": arts, "trees": trees, "glb": glb, "pb": pb, "size": T.tree_size(s.n), "density": density(inst.F), "cap": cap_for(s.n),
            "gap_glb": (opt - glb) / opt if opt else float("nan"), "gap_pb": (opt - pb) / opt if opt else float("nan"), "all_optimal": all(t.optimal and t.best == opt for t in trees.values()) if exact else None}


def da_tree(s: Settings, v: dict) -> T.Tree:
    """Der Baum mit zwei Runden Dual Ascent als Schranke (nur n ≤ 8)."""
    inst = v["inst"]
    return T.solve(inst.F, inst.D, "da2", v["inc"], s.order, None)


def grid_data(s: Settings, v: dict) -> dict:
    """Knoten (Gilmore–Lawler) für jede Reihenfolge und jeden Anfangswert, gleiche Instanz: {(order, incumbent): Tree}."""
    inst = v["inst"]
    out = {}
    for order in C.ORDERS:
        for kind in C.INCUMBENTS:
            out[(order, kind)] = T.solve(inst.F, inst.D, "glb", incumbent_value(inst, s.seed, kind), order, cap_for(s.n))
    return out


# ----------------------------------------------------------------------------- Zeilen für die Vergleiche

def row_of(family: str, n: int, seed: int, arts=C.SWEEP_ARTS) -> dict:
    """Eine Instanz mit aufgezähltem Optimum: Suche mit jeder Art (Anfangswert: beste von 200 Abstiegen, Reihenfolge nach Fluss), Wurzelschranken, Dichte."""
    inst = make_instance(family, n, seed)
    opt = int(L.landscape(inst).opt)
    inc = B.best_found(inst.F, inst.D, seed, C.STARTS)[0]
    trees = {a: T.solve(inst.F, inst.D, a, inc, "flow", None) for a in arts}
    glb = B.gilmore_lawler(inst.F, inst.D).glb
    pb = S.spectral_bounds(inst.F, inst.D).pb
    row = {"family": family, "n": n, "seed": seed, "opt": opt, "inc": int(inc), "inc_hit": int(inc) == opt, "glb": glb, "pb": pb, "gap_glb": (opt - glb) / opt if opt else float("nan"), "gap_pb": (opt - pb) / opt if opt else float("nan"),
           "density": density(inst.F), "valid": all(t.optimal and t.best == opt for t in trees.values()), "depth_glb": trees["glb"].depth if "glb" in trees else None}
    for a in arts:
        row[f"nodes_{a}"] = trees[a].nodes
    return row


def growth_row(family: str, n: int, seed: int) -> dict:
    """Eine Instanz für das Wachstum: nur die Gilmore–Lawler-Schranke; Anfangswert: beste von 200 Abstiegen; bei n ≥ 12 mit Obergrenze."""
    inst = make_instance(family, n, seed)
    inc = B.best_found(inst.F, inst.D, seed, C.STARTS)[0]
    t = T.solve(inst.F, inst.D, "glb", inc, "flow", cap_for(n))
    return {"family": family, "n": n, "seed": seed, "nodes": t.nodes, "capped": t.capped, "share": t.share, "density": density(inst.F)}


def sweep(family: str, n: int, seeds=None) -> list:
    """Die festen Instanzen einer Familie für den Vergleich der Arten (n = 6, 8)."""
    return [row_of(family, n, s) for s in (seeds if seeds is not None else C.SWEEP_SEEDS_N[n])]


def growth(family: str, n: int, seeds=None) -> list:
    return [growth_row(family, n, s) for s in (seeds if seeds is not None else C.GROWTH_SEEDS_N[n])]


def pooled(by_family: dict) -> list:
    return [r for f in C.FAMILIES if f in by_family for r in by_family[f]]


def family_summary(rows: list) -> dict:
    """Median je Art und Zählungen für die Zeilen einer Familie."""
    out = {"count": len(rows), "valid": all(r["valid"] for r in rows), "gap_glb": median_of(rows, "gap_glb"), "gap_pb": median_of(rows, "gap_pb"), "density": median_of(rows, "density"), "inc_hit": sum(r["inc_hit"] for r in rows)}
    for a in C.SWEEP_ARTS:
        out[a] = median_of(rows, f"nodes_{a}")
    out["pb_more"] = sum(r["nodes_pb"] > r["nodes_glb"] for r in rows)
    out["pb_root_better"] = sum(r["pb"] > r["glb"] for r in rows)
    return out


# ----------------------------------------------------------------------------- Verdikte

def _head(s: Settings, v: dict) -> str:
    inst = v["inst"]
    return f"Familie **{fam(s.family)}**, {s.n} Bauteile, Raster {inst.rows}×{inst.cols}, Seed {s.seed}"


def verdict_tree(s: Settings, v: dict):
    """Die Suche mit Gilmore–Lawler: Knotenzahl gegen den vollen Baum, Ergebnis."""
    t = v["trees"]["glb"]
    full = f"Der volle Baum hat {count(v['size'])} Knoten. "
    if t.capped:
        return "warning", (f"{_head(s, v)}: {full}Mit der Gilmore–Lawler-Schranke wurden {count(t.nodes)} Knoten bewertet, dann stoppte die Obergrenze ({count(C.NODE_CAP)}): **nicht zu Ende gerechnet**. Beste gefundene Anordnung: Kosten {num(t.best)}, "
                           f"Schranke der Wurzel {num(t.root)}; ob sie optimal ist, ist offen.")
    res = f"Optimum **{num(t.best)}** bewiesen"
    if v["exact"]:
        res += " (gleich dem aufgezählten)" if t.best == v["opt"] else f" (**ACHTUNG: aufgezählt {v['opt']}**)"
    return "success", (f"{_head(s, v)}: {full}Mit der Gilmore–Lawler-Schranke bewertet der Suchbaum **{count(t.nodes)}** Knoten ({pct(t.share, 2 if t.share < 0.01 else 1)} davon); {res}. "
                       f"Die Wurzelschranke ist {num(t.root)}" + (f" (Lücke {pct(v['gap_glb'], 1)})" if v["exact"] else "") + f", der Anfangswert {('keiner' if v['inc'] is None else num(v['inc']))}.")


def verdict_arts(s: Settings, v: dict):
    """Knoten je Art für die gewählte Instanz."""
    tr = v["trees"]
    if set(tr) == {"glb"}:
        return "info", f"{_head(s, v)}: ab n = 12 wird nur mit der Gilmore–Lawler-Schranke gerechnet (die übrigen Arten brauchen zu viele Knoten oder zu viel Zeit je Knoten)."
    parts = "; ".join(f"{T.ART_SHORT[a]} {count(tr[a].nodes)}" for a in v["arts"])
    glb, lin, none = tr["glb"].nodes, tr["lin"].nodes, tr["none"].nodes
    kind = "success" if glb <= lin <= none else "warning"
    pb_txt = ("; die projizierte Schranke braucht **mehr** Knoten als Gilmore–Lawler" if tr["pb"].nodes > glb else ("; die projizierte Schranke braucht **gleich viele** Knoten wie Gilmore–Lawler" if tr["pb"].nodes == glb
                                                                                                                  else "; die projizierte Schranke braucht **weniger** Knoten als Gilmore–Lawler"))
    return kind, (f"{_head(s, v)}, Knoten je Art: {parts}. Gilmore–Lawler bewertet {de(none / max(glb, 1), 0)}-mal weniger Knoten als der Baum ohne Schranke und {de(lin / max(glb, 1), 1)}-mal weniger als die lineare Zuordnung{pb_txt}. "
                  f"Je Knoten kostet die stärkere Schranke mehr Rechenarbeit; die gemessene Zeit steht unten.")


def verdict_inspect(cb: dict, arts) -> tuple:
    """Schranken der Kinder der Wurzel gegen die kleinste Fortsetzung."""
    mc = cb["min_completion"]
    if mc is None:
        return "info", "Die kleinste Fortsetzung wird nur bis n = 9 aufgezählt."
    sharp = {a: sum(abs(cb[a][j] - mc[j]) < 1e-6 for j in range(len(mc))) for a in arts}
    valid = all(cb[a][j] <= mc[j] + 1e-6 for a in arts for j in range(len(mc)))
    txt = "; ".join(f"{T.ART_SHORT[a]} scharf in {sharp[a]} von {len(mc)}" for a in arts)
    return ("success" if valid else "error"), (("Jede Schranke liegt unter der kleinsten Fortsetzung (gültig)" if valid else "**ACHTUNG: eine Schranke liegt über der kleinsten Fortsetzung**") + f"; {txt}. Kleinste Fortsetzung insgesamt: {min(mc)}.")


def verdict_da(s: Settings, glb_t: T.Tree, da_t: T.Tree):
    """Zwei Runden Dual Ascent gegen Gilmore–Lawler (Knoten)."""
    saved = 1 - da_t.nodes / glb_t.nodes if glb_t.nodes else 0.0
    return "info", (f"Zwei Runden Dual Ascent bewerten **{count(da_t.nodes)}** Knoten, Gilmore–Lawler {count(glb_t.nodes)} ({'spart ' + pct(saved) if saved > 0 else 'keine Ersparnis'}); "
                    f"jeder Knoten kostet aber ein Vielfaches an Rechenarbeit (je Runde n² Zuordnungen statt einer): die gemessene Zeit steht oben.")


def _sweep_text(n: int, by: dict) -> tuple:
    rows = pooled(by)
    med = {a: median_of(rows, f"nodes_{a}") for a in C.SWEEP_ARTS}
    return rows, med


def verdict_sweep(n: int, by_family: dict):
    """Vergleich der Arten über feste Instanzen: Median der Knoten, Gültigkeit, pb gegen glb."""
    rows, med = _sweep_text(n, by_family)
    valid = all(r["valid"] for r in rows)
    pb_more = sum(r["nodes_pb"] > r["nodes_glb"] for r in rows)
    root_better = sum(r["pb"] > r["glb"] for r in rows)
    pb_fewer = sum(r["nodes_pb"] < r["nodes_glb"] for r in rows)
    txt = (f"Bei n = {n}, Median über {len(rows)} Instanzen: " + "; ".join(f"{T.ART_SHORT[a]} {count(med[a])}" for a in C.SWEEP_ARTS) + f" Knoten (voller Baum {count(T.tree_size(n))}). "
           f"Die projizierte Schranke ist an der Wurzel in {root_better} von {len(rows)} Instanzen besser als Gilmore–Lawler, braucht im Baum aber in {pb_more} mehr Knoten (weniger in {pb_fewer}). "
           f"Alle Läufe fanden das aufgezählte Optimum ({'gültig' if valid else 'ACHTUNG: nicht in allen'}).")
    return ("success" if valid else "error"), txt


def verdict_corr(n: int, by_family: dict):
    """Knoten (glb) gegen die Lücke der Wurzelschranke und gegen die Dichte des Flusses."""
    rows = pooled(by_family)
    nodes = [r["nodes_glb"] for r in rows]
    c_gap, c_den = spearman(nodes, [r["gap_glb"] for r in rows]), spearman(nodes, [r["density"] for r in rows])
    se = 1.06 / math.sqrt(max(len(rows) - 3, 1))
    fams = "; ".join(f"{fam(f)} {count(median_of(by_family[f], 'nodes_glb'))}" for f in C.FAMILIES if f in by_family)
    return "info", (f"Bei n = {n} ({len(rows)} Instanzen): Rangkorrelation der Knotenzahl (Gilmore–Lawler) mit der **Lücke der Wurzelschranke** {de(c_gap, 2)}, mit der **Dichte des Flusses** {de(c_den, 2)} (Unsicherheit grob ±{de(1.96 * se, 2)}). "
                    f"Median der Knoten je Familie: {fams}.")


def verdict_start(s: Settings, grid: dict):
    """Reihenfolge und Anfangswert (Gilmore–Lawler, gleiche Instanz)."""
    base = grid[(C.DEFAULT_ORDER, C.DEFAULT_INCUMBENT)].nodes
    worst = max(grid.items(), key=lambda kv: kv[1].nodes)
    none_flow = grid[("flow", "none")].nodes
    index, light = grid[("index", "descents200")].nodes, grid[("light", "descents200")].nodes
    if any(t.capped for t in grid.values()):
        return "warning", "Mindestens ein Lauf erreichte die Obergrenze der Knoten: kein Vergleich möglich."
    return "info", (f"Gilmore–Lawler, {fam(s.family)}, n = {s.n}, Seed {s.seed}: {count(base)} Knoten mit starken Flüssen zuerst und der besten von {C.STARTS} Abstiegen als Anfangswert; ohne Anfangswert {count(none_flow)} ({pct(none_flow / base - 1) if base else '–'} mehr); "
                    f"nach Nummer {count(index)}, schwache Flüsse zuerst {count(light)}. Am meisten Knoten: {count(worst[1].nodes)} ({T.ORDER_NAMES[worst[0][0]]}, Anfangswert {C.INCUMBENT_NAMES[worst[0][1]]}).")


def verdict_growth(by_n: dict):
    """Wachstum der Knotenzahl mit n (Gilmore–Lawler)."""
    parts = []
    for n in sorted(by_n):
        rows = pooled(by_n[n])
        capped = sum(r["capped"] for r in rows)
        parts.append(f"n = {n}: Median {count(median_of(rows, 'nodes'))} Knoten von {count(T.tree_size(n))} im vollen Baum ({pct(float(np.median([r['share'] for r in rows])), 4)}), höchstens {count(max(r['nodes'] for r in rows))}"
                     + (f", {capped} von {len(rows)} an der Obergrenze" if capped else ""))
    return "info", "Gilmore–Lawler, Median über alle Instanzen: " + "; ".join(parts) + ". Der volle Baum wächst viel schneller; ab n = 16 reicht die Obergrenze meist nicht mehr."


def verdict_core(s: Settings, v: dict):
    t = v["trees"]["glb"]
    return "info", (f"Im Suchbaum bewertet die Gilmore–Lawler-Schranke bei {_head(s, v)} {count(t.nodes)} von {count(v['size'])} möglichen Knoten"
                    + ("" if len(v["arts"]) == 1 else f"; ohne Schranke wären es {count(v['trees']['none'].nodes)}, mit der linearen Zuordnung {count(v['trees']['lin'].nodes)}, mit der projizierten Schranke {count(v['trees']['pb'].nodes)}")
                    + ". Welche Schranke lohnt, entscheiden Knoten **und** Rechenarbeit je Knoten: Experiment 2 bis 5.")


# ----------------------------------------------------------------------------- Handbeispiel

def hand_data() -> dict:
    """Das Handbeispiel (drei Bauteile auf einer Zeile): Knotenschranken der Kinder der Wurzel von Hand nachzurechnen und der volle Lauf."""
    inst = hand_instance()
    cb = T.child_bounds(inst.F, inst.D, ("none", "lin", "glb"))
    full = T.solve(inst.F, inst.D, "glb", None)
    with_inc = T.solve(inst.F, inst.D, "glb", 6)
    return {"inst": inst, "child": cb, "full": full, "with_inc": with_inc}
