# Branch and Bound mit Schranke – Streamlit-Demo

<!-- TODO nach dem Deploy: direkt hierher den Live-Link setzen (Leerzeile davor und danach):
**[→ Demo live ausprobieren](https://sebastianhanisch-schranke-im-baum-demo.streamlit.app/)** -->

Stück 8 von 15 der **Konzepte-Reihe „Anordnen: relaxieren und runden“** für die Website „Sebastian Hanisch – Operations Research und Machine Learning“ (die Konzepte-Seite der Reihe gibt es noch nicht). Die Stücke 3 bis 6 haben Schranken gebaut: [Gilmore–Lawler](https://github.com/sebastian-hanisch/gilmore-lawler-demo), [Eigenwert und Projektion](https://github.com/sebastian-hanisch/eigenwert-schranke-demo), [Linearisierung und Dual Ascent](https://github.com/sebastian-hanisch/linearisierung-schranke-demo) und die [doppeltstochastische Relaxation](https://github.com/sebastian-hanisch/birkhoff-relaxation-demo). Dieses Stück setzt sie **im Suchbaum** ein (Kante der Reihe: *Zusammenfluss*) und fragt, welche sich lohnt: Schärfe spart Knoten, kostet aber Arbeit je Knoten.

## Warum dieses Problem

Eine Schranke an der Wurzel sagt, wie weit unter dem Optimum man beweisen kann; **beweisen**, dass eine Anordnung die beste ist, braucht einen Suchbaum: Bauteil für Bauteil auf einen Platz setzen (ein **Knoten** ist eine Teilzuordnung) und jeden Ast **beschneiden**, dessen Schranke schon nicht mehr unter der besten bekannten Anordnung liegt. Die Kernfrage: **Welche Schranke lohnt im Baum, wenn man Knoten und Rechenarbeit je Knoten zusammen betrachtet?**

Die Antwort dieser Messung: Die **Gilmore–Lawler-Schranke mit linearem Term** ist unter den Arten ohne Schranke, linear und Gilmore–Lawler an Knoten und an Zeit die beste; zwei Runden Dual Ascent und das Maximum aus Gilmore–Lawler und projizierter Schranke sparen noch Knoten (bei n = 8 Median 212 bzw. 260 gegen 276), kosten aber je Knoten ein Vielfaches an Zeit. Die projizierte Schranke, die an der Wurzel nur in 24 von 120 (n = 6) bzw. 19 von 60 (n = 8) Instanzen stärker ist, braucht im Baum fast immer **mehr** Knoten als Gilmore–Lawler (einfache Summenfassung); zwei Runden Dual Ascent sparen rund ein Fünftel der Knoten und kosten je Knoten ein Vielfaches; die Baumgröße hängt **an beidem**: bei n = 6 steigt sie stärker mit der Lücke der Wurzelschranke (Rangkorrelation 0,68) als mit der Dichte des Flusses (0,42), bei n = 8 über alle Familien stärker mit der Dichte (0,64 gegen 0,19); innerhalb einer Familie bleibt die Lücke der bessere Anzeiger. Mit dieser Fassung und der Obergrenze von 100 000 Knoten endet der Beweis bei n = 12 bis 16. Das sind **Befunde an sechs erfundenen Familien und an einfachen Eigenfassungen der Knotenschranken**, keine Sätze.

## Modell

- **Aufgabe** (wie in Stück 1 bis 7): `n` Bauteile auf `n` Plätze, `cost(p) = Σ_{i<k} F[i,k] · D[p_i, p_k]` (jedes Paar einmal). Kern (Kosten, Aufzählung, Zufall, sechs Familien der Flussmatrix, Gilmore–Lawler-Schranke, beste gefundene Lösung, projizierte Schranke, Ungarische Methode samt Dualvariablen) als Kopie aus Stück 3 bis 6 (`sib_cost.py`, `sib_landscape.py`, `sib_rng.py`, `sib_instance.py`, `sib_bound.py`, `sib_spectral.py`, `sib_assignment.py`; Tests vergleichen die Instanzen mit den Schwester-Repos, wenn sie nebenan liegen). Die Familien sind **eigene, einfache Erfindungen**, keine echten Platinen und keine QAPLIB-Instanzen; Plätze liegen auf einem Raster (Manhattan-Abstand).
- **Knoten** (`sib_tree.py`): die Bauteile `A` stehen auf den Plätzen `p_a`, frei bleiben die Bauteile `R` und die Plätze `S`. Jede Fortsetzung kostet **feste Kosten** (Paare unter den gesetzten) + **lineare Kosten** `c[i,j] = Σ_{a∈A} F[i,a] · D[j,p_a]` + **quadratische Kosten** unter den freien Paaren.
- **Schranken des Knotens** (alle gültig; jede wird im Test an jeder Fortsetzung kleiner Instanzen gegen die Aufzählung geprüft): **ohne** (nur die festen Kosten), **linear** (feste Kosten + kleinste Zuordnung über `c`), **Gilmore–Lawler** (kleinste Zuordnung über `c[i,j] + ½ · L[i,j]` mit dem kleinsten Skalarprodukt `L[i,j]` der übrigen freien Flüsse und Abstände), **projiziert** (projizierte Schranke der freien Teilmatrizen + lineare Zuordnung; **einfache Summe**, nicht die Originalform), **Maximum** aus Gilmore–Lawler und projiziert, **Dual Ascent** mit zwei Runden (Stück 5; Runde 1 ist genau Gilmore–Lawler).
- **Suche:** Tiefensuche; je Knoten alle Kinder bewerten (jedes bewertete Kind zählt als **ein Knoten**), nach Schranke aufsteigend besuchen; beschnitten wird, sobald die aufgerundete Schranke nicht unter dem besten bekannten Wert liegt. Reihenfolge der Bauteile: nach Gesamtfluss absteigend (wählbar). Anfangswert: die beste von 200 steilsten Abstiegen (Stück 3; wählbar). Der volle Baum ohne Beschneiden hat `Σ n!/(n−k)!` Knoten (n = 6: 1 956; n = 8: 109 600; n = 9: 986 409; n = 12: 1 302 061 344).
- **Experimente:** (1) der Baum: Knoten je Tiefe, die beste Anordnung, die Schranken der Kinder der Wurzel gegen die kleinste Fortsetzung, Handbeispiel; (2) welche Schranke lohnt (Knoten, gemessene Zeit, Dual Ascent auf Knopfdruck, Vergleich über feste Instanzen); (3) Wurzelschärfe gegen Baumgröße; (4) Anfangswert und Reihenfolge; (5) Wachstum und Grenze. Formeln im 📐-Expander der App.

## Methodik

Experiment 1, 2 und 4 rechnen **eine** Instanz (n = 6 oder 8 sofort mit allen fünf Arten und Aufzählung als Probe; n = 9 auf Knopfdruck; n = 12 und 16 nur mit Gilmore–Lawler, auf Knopfdruck und höchstens 100 000 Knoten). Der Vergleich über feste Instanzen rechnet auf Knopfdruck je Familie 20 Instanzen bei n = 6 (Seeds 100000 bis 100019) und zehn bei n = 8 (Seeds 100000 bis 100009) mit vier Arten (ohne, linear, Gilmore–Lawler, projiziert); Experiment 5 rechnet Gilmore–Lawler für n = 6 (20), 8 (10), 9 (5) und 12 (5 je Familie). Alle Aussagen laufen über feste Seeds, nie über einen einzelnen. **Zeiten** hängen vom Rechner ab; die App misst sie für die gewählte Instanz, aber sie stehen nirgends als Zahl in Tests oder in dieser README. Die Knotenzahlen der ganzzahligen Arten (ohne, linear, Gilmore–Lawler) sind exakt und auf jedem Rechner gleich; bei projiziert, Maximum und Dual Ascent (Gleitkomma) rechnet der Vergleich mit einer Toleranz von 1e-7.

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen stehen in `tests/test_claims.py` (Knotenzahlen exakt, Prozentwerte auf die genannte Rundung). Reihenfolge der Familien: Netzliste, gleichverteilt, dünn besetzt, zwei Cluster, Stern, wenige starke Flüsse. „Knoten“ sind bewertete Teilzuordnungen.

| Frage | Befund |
|---|---|
| Handbeispiel | Drei Bauteile auf einer Zeile (Abstände 1 und 1, Fluss A–B 5, B–C 1), Reihenfolge B, A, C: das erste Bauteil B auf Platz 1, 2, 3: Schranke ohne 0 / 0 / 0, **linear 7 / 6 / 7, Gilmore–Lawler 7 / 6 / 7**, kleinste Fortsetzung 7 / 6 / 7. Ohne Anfangswert bewertet der Baum **6** Knoten (je Tiefe 3, 2, 1), mit dem Anfangswert 6 nur **3** |
| Gültigkeit | In 72 zufälligen Knoten (n = 6, sechs Familien) liegt keine Schranke über der kleinsten Fortsetzung; alle 180 Läufe der Vergleiche beweisen das aufgezählte Optimum (der Anfangswert war in allen schon optimal) |
| Standardinstanz (Netzliste, n = 8, Seed 35) | voller Baum 109 600 Knoten; **ohne** 17 024, **linear** 3 404, **Gilmore–Lawler 64** (0,06 %), projiziert 560, Maximum 64; Wurzelschranke 27 (Lücke 12,9 %), projizierte Schranke 13,7, Optimum 31 (der Anfangswert); 266-mal weniger Knoten als ohne Schranke, 53,2-mal weniger als linear. Die 64 Knoten sind die 8 Kinder der Wurzel und 56 weitere in Tiefe 2, alle beschnitten |
| Knoten, Median über alle Instanzen (n = 6: 120, n = 8: 60) | n = 6: ohne **1 240**, linear **212**, Gilmore–Lawler **38**, projiziert **68**; n = 8: ohne **40 566**, linear **2 204**, Gilmore–Lawler **276**, projiziert **604**. Anteil am vollen Baum: n = 6 63 / 11 / 1,9 / 3,5 %, n = 8 37 / 2,0 / 0,25 / 0,55 % |
| Knoten je Familie, n = 6 (Median, 20 Instanzen) | ohne 1 374 / 1 724 / 500 / 1 830 / 952 / 732; linear 248 / 376 / 60 / 456 / 88 / 170; Gilmore–Lawler 48 / 52 / 16 / 156 / 16 / 39; projiziert 70 / 76 / 36 / 196 / 20 / 68 |
| Knoten je Familie, n = 8 (Median, 10 Instanzen) | ohne 40 566 / 89 948 / 12 152 / 73 852 / 36 540 / 11 080; linear 2 636 / 8 134 / 570 / 6 326 / 1 100 / 1 062; Gilmore–Lawler 210 / 560 / 126 / 416 / 184 / 212; projiziert 544 / 900 / 418 / 762 / 240 / 538 |
| Stärkere Wurzelschranke einer anderen Art heißt nicht weniger Knoten; innerhalb einer Art steigt die Knotenzahl mit der Lücke der Wurzelschranke | die **projizierte Schranke ist an der Wurzel besser** als Gilmore–Lawler in 24 von 120 (n = 6) und 19 von 60 Instanzen (n = 8; gleichverteilt, Cluster, Stern), **braucht im Baum aber mehr Knoten** in 94 von 120 und **60 von 60** Instanzen (weniger: in 1 und 0). Ursache vermutlich die getrennte Abschätzung von linearem und quadratischem Teil (nicht untersucht) |
| Womit die Baumgröße zusammenhängt | Rangkorrelation der Knoten (Gilmore–Lawler) mit der **Lücke der Wurzelschranke** 0,68 (n = 6) und 0,19 (n = 8), mit der **Dichte des Flusses** 0,42 und 0,64 (Unsicherheit grob ±0,19 bzw. ±0,28); innerhalb der Familien (n = 8, je 10 Instanzen) ist die Korrelation mit der Lücke in allen sechs Familien positiv (0,18 bis 0,80), die mit der Dichte in drei Familien negativ (−0,30 bis −0,56), die gepoolte Dichte-Korrelation spiegelt also auch die Familienmischung; eine Korrelation ist keine Ursache. Lücke der Wurzelschranke je Familie (Median in %): n = 6: 7,3 / 5,2 / 10,3 / 17,0 / 7,7 / 3,4; n = 8: 10,5 / 8,0 / 6,1 / 9,8 / 14,1 / 6,4 |
| Anfangswert und Reihenfolge (Standardinstanz, Gilmore–Lawler) | starke Flüsse zuerst: 64 (200 Abstiege), 177 (ein Abstieg), 187 (keiner); nach Nummer: 64 / 96 / 106; schwache Flüsse zuerst: 644 / 1 115 / 1 157. **Eine Instanz, kein Befund über die Familie** |
| Stärkere Schranke: zwei Runden Dual Ascent | n = 8, je Familie die ersten vier Instanzen (24): Knoten im Median 302 gegen **232** (Gilmore–Lawler gegen Dual Ascent), weniger in 18, gleich in 6, mehr in 0; insgesamt **21 %** weniger Knoten. Je Knoten kostet der Dual Ascent ein Vielfaches (je Runde n² statt einer Zuordnung); die Gesamtzeit steigt auf ein Mehrfaches (Messung, rechnerabhängig, keine Zahl). Bei der Standardinstanz keine Ersparnis (64 gegen 64) |
| Wachstum und Grenze (Gilmore–Lawler, Median über alle Instanzen) | n = 6: **38** Knoten von 1 956 (höchstens 268); n = 8: **276** von 109 600 (höchstens 924); n = 9: **691** von 986 409 (höchstens 11 749; je Familie 685 / 1 813 / 365 / 5 565 / 157 / 585); n = 12 (5 Instanzen je Familie, Obergrenze 100 000): Median **7 990**, je Familie 3 196 / 100 000 / 2 164 / 85 868 / 3 648 / 9 110; **5 von 30 Instanzen erreichen die Obergrenze** (4 gleichverteilte, 1 Cluster), also nicht zu Ende gerechnet; der volle Baum hat über eine Milliarde Knoten. n = 16 (Vormessung, nicht im Test): in 28 von 30 Instanzen nicht zu Ende |
| Orakel | Zuordnung in jedem Knoten gleich `scipy.optimize.linear_sum_assignment` (auch auf den Matrizen von Gilmore–Lawler); Dualvariablen zulässig und komplementär; jede Art liefert das aufgezählte Optimum; eine zweite, unabhängig geschriebene Probe der Knotenschranke (Aufzählung der Fortsetzungen) |

**Was die Zahlen nicht sagen:** Die Familien sind erfunden; andere Parameter können die Rangfolge ändern. Die projizierte Schranke im Knoten ist eine **einfache Summe**, nicht die Originalform von Hadley, Rendl und Wolkowicz mit linearem Term: „im Baum schlechter als Gilmore–Lawler“ gilt für diese Fassung. Der Dual Ascent ist die einfache Fassung aus Stück 5. Die konvexe Schranke (Stück 6) und das LP (Stück 5) wurden **nicht** im Baum gemessen (zu teuer je Knoten). Bei n = 8 und größer sind es zehn Instanzen oder weniger je Familie.

## Ehrliche Grenzen

- **Einfache Knotenschranken:** eigene Herleitungen; die Literatur kennt stärkere Fassungen (nicht nachgelesen).
- **Keine Symmetrie:** das Raster hat Spiegelungen, der Baum zählt gleichwertige Äste mehrfach (Stück 13).
- **Feste Reihenfolge:** das nächste Bauteil wird nicht dynamisch gewählt; die Reihenfolge „schwache Flüsse zuerst“ vervielfacht die Knotenzahl (Standardinstanz: rund das Zehnfache); „nach Nummer“ änderte dort nichts.
- **Der Beweis endet bei n = 12 bis 16:** bei n = 12 sind einzelne Bäume über 100 000 Knoten groß (Obergrenze der App), bei n = 16 reicht sie meist nicht; die Literatur nennt mit viel Rechenzeit etwa n = 30 (Angabe aus zweiter Hand, nicht nachgelesen).
- **Erfundene Familien:** keine echten Platinen, keine QAPLIB-Instanzen.
- **Wenige Instanzen:** n = 6: 20 je Familie, n = 8: 10, n = 9: 5, n = 12: 5.
- **Zeiten:** nur gemessen auf Knopfdruck und rechnerabhängig, nie als Zahl in Tests oder README.
- **Quellen:** Gilmore, Lawler (Schranke und Branch and Bound), Burkard u. a. und Loiola u. a. (Überblicke), Hahn und Grant (Dual Ascent), Anstreicher (Branch and Bound mit QP-Schranke) sind aus der Fachliteratur übernommen und **nicht nachgelesen**; die Knotenschranken (Zerlegung der Kosten, Gültigkeit) sind eigene Herleitungen und werden durch Tests (Aufzählung, Handrechnung, `scipy`) geprüft.

## Verifikation

- **Tests** (`pytest tests/`): **245 Tests**, rund elf Minuten (Windows, Python 3.14). Handwerte (Handbeispiel von Hand, Zuordnung, Dual Ascent), Eigenschaften (jede Schranke liegt unter der kleinsten Fortsetzung jedes Knotens; ohne ≤ linear ≤ Gilmore–Lawler ≤ Maximum knotenweise, daher bei festem Anfangswert ineinander enthaltene Bäume; Wurzel gleich Stück 3 und 4; Runde 1 des Dual Ascent gleich Gilmore–Lawler; die Suche liefert das aufgezählte Optimum für jede Art und Reihenfolge; Zählung der Knoten je Tiefe), Orakel (Aufzählung für die Gültigkeit; `scipy` für die Zuordnung; nur mit `requirements-dev.txt`), Randfälle (zwei Bauteile, Nullfluss, gleiche Flüsse, Obergrenze, ungültige Eingaben), Verdikte an handgesetzten Werten, Abbildungen, PDF, Rauchtest und Pfade der App (jede Familie, n = 9 und n = 12 auf Knopfdruck, Dual Ascent, beide Vergleiche, Wachstum), Layout, Footer und Laufzeit-Importe. `test_claims.py` rechnet jede Zahl dieser README nach (einige Minuten).
- **Kopie:** Tests vergleichen die Familien mit denen von Stück 1 bis 6, sofern die Schwester-Repos nebenan liegen.
- **Nicht getestet:** Zeiten; kein Mutationstest; Linux-CI: noch nicht gelaufen (Repo noch nicht veröffentlicht).

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App: fünf Experimente, Vergleich über feste Instanzen, Grenzen, Formulierung |
| `sib_rng.py` | SplitMix64 (Kopie aus Stück 1) |
| `sib_instance.py` | Instanzen: sechs Familien der Flussmatrix, Raster, Handbeispiele |
| `sib_cost.py` | Kosten, Tausch-`Δ` (Kopie aus Stück 2) |
| `sib_landscape.py` | Aufzählung für das Optimum (Kopie aus Stück 2) |
| `sib_assignment.py` | Ungarische Methode, auch mit Dualvariablen |
| `sib_bound.py` | Gilmore–Lawler-Schranke, Abstiege und beste gefundene Lösung (Kopie aus Stück 3) |
| `sib_spectral.py` | Eigenwerte, projizierte Schranke (Kopie aus Stück 4) |
| `sib_tree.py` | Knotenschranken, Tiefensuche, Dual Ascent im Knoten |
| `sib_evaluation.py` | Zeilen für die Vergleiche, Zusammenfassungen, Verdikte |
| `sib_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `sib_pdf_export.py` | PDF-Export des Ergebnisses |
| `sib_constants.py` | Größen, Familien, feste Reihen, Farben, Presets |
| `sib_presets.py` | Permalink (Begrenzen), Presets (Schnellstart in der Seitenleiste, aktives Preset hervorgehoben), Zufalls-Button |
| `sib_layout.py` | Fester Kopf (Stylesheet) |
| `requirements-dev.txt` | Laufzeit plus pytest und scipy |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt; kein `scipy` zur Laufzeit) |
| `tests/` | Knoten und Suche, Zuordnung, Kosten, Instanzen, Landschaft, Auswertung, Verdikte, Abbildungen, Presets, Layout, AppTest, Orakel, Zahlen der README, Footer, Laufzeit-Importe |

## Bewusst nicht umgesetzt

- **Symmetrie (Stück 13):** gespiegelte Äste werden nicht zusammengelegt.
- **Dynamische Wahl des nächsten Bauteils, Schnittebenen, parallele Suche.**
- **Die konvexe Schranke (Stück 6), das LP (Stück 5) und die semidefinite Schranke (gelbes Stück 7) im Baum:** zu teuer je Knoten.
- **Die Originalform der projizierten Schranke mit linearem Term:** Primärlektüre fehlt; die einfache Summe steht für sich.
- **n ≥ 16 bis zum Ende:** nur mit Obergrenze als Grenze der Demo.
- **Asymmetrische Flüsse und Abstände.**

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

Streamlit Cloud: Python-Version in den App-Einstellungen prüfen (lokal Python 3.14, CI Python 3.12); der Code verwendet nur Merkmale, die in Python 3.12 laufen. <!-- lint-ok: dezimalpunkt -->

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly, NumPy, pandas und fpdf2.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html).
