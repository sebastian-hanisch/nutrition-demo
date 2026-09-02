# 🥗 Ernährungsoptimierung

Interaktive Demo zur Ernährungsoptimierung: Aus einer Beispiel-Ist-Ernährung werden Lebensmittelmengen so angepasst, dass Kalorien- und Makronährstoffziele erreicht werden — mit möglichst geringer Abweichung von den gewohnten Mengen.

**[→ Demo live ausprobieren](https://sebastianhanisch-nutrition-demo.streamlit.app/)**

## Worum geht's?

Angeregt durch Schäfer et al. (2025, PLOS ONE), *"A methodological framework for deriving the German food-based dietary guidelines 2024"* — die Methodik hinter dem Update der offiziellen deutschen Ernährungsempfehlungen. Dort wird Diätoptimierung (Zielprogrammierung / Goal Programming) genutzt: Lebensmittelgruppen als Entscheidungsvariablen, Minimierung der Abweichung von der beobachteten Ist-Ernährung unter Nährstoff- und Mengen-Nebenbedingungen, verglichen über vier Zielfunktionstypen (linear/quadratisch × absolut/relativ).

Kernthema der Demo: **wie stark verändert allein die Form der Zielfunktion die Lösung**, obwohl alle Nebenbedingungen identisch bleiben? Linear (L1-artig) liefert dünnbesetzte Lösungen — wenige, aber größere Änderungen, die meisten Lebensmittel bleiben unverändert. Quadratisch (L2-artig) verteilt die Anpassung auf fast alle Lebensmittel. Strukturell identisch mit der Sparsamkeits-Eigenschaft von LASSO gegenüber Ridge Regression — und exakt der Effekt, den das Originalpaper empirisch beobachtet hat (linear-relative Modelle ließen 206–218 von 255 Lebensmittelgruppen unverändert, quadratisch-absolute nur 7–8).

## Methodik

- Vier Zielfunktionstypen im direkten Vergleich: linear/quadratisch × absolut/relativ, alle unter identischen Nährstoff- und Mengen-Nebenbedingungen
- Reale Einzel-Lebensmittel (25 Stück) statt aggregierter FoodEx2-Gruppen — didaktisch näher an Ernährungs-/Fitness-Alltagsfragen
- Ziel-Presets (Abnehmen/Erhaltung/Muskelaufbau) leiten Kalorien-/Makroziele aus Körpergewicht ab (grobe Fitness-Faustregeln, keine medizinische Beratung)
- Lineare Varianten: SciPy `linprog` (HiGHS). Quadratische Varianten: SciPy `minimize` (SLSQP, trust-constr als Fallback)
- Vergleichskennzahlen wie im Originalpaper: Summe absoluter/relativer Änderung, Anzahl unverändert/gestiegen/gesunken/verschwunden
- PDF-Export, Permalink
- Mathematische Herleitung (inkl. Bezug zu L1/L2-Regularisierung) im Expander „Mathematische Formulierung“

## Lokal ausführen

```bash
pip install -r requirements-dev.txt
streamlit run app.py
```

Tests: `pytest tests/ -v`

---

Teil des [Operations-Research-Demo-Portfolios](https://sebastianhanisch.net/demos.html) von [Sebastian Hanisch](https://sebastianhanisch.net) — Operations Research und Machine Learning. Interesse an einer maßgeschneiderten Lösung? [Kontakt aufnehmen](https://sebastianhanisch.net/kontakt.html).
