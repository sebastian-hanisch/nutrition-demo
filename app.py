"""
Ernährungsoptimierung – interaktive Demo
Sebastian Hanisch - Operations Research und Machine Learning

Angeregt durch Schäfer et al. (2025, PLOS ONE, "A methodological framework
for deriving the German food-based dietary guidelines 2024"): Die Autor:innen
optimieren dort eine Ernährung, indem sie die Abweichung von der beobachteten
Ist-Ernährung minimieren, unter Nährstoff- und Mengen-Nebenbedingungen - und
vergleichen dabei vier Zielfunktionstypen (linear/quadratisch, absolut/
relativ). Ihr zentraler empirischer Befund: linear-relative Modelle ließen
die meisten Lebensmittel unverändert (Sparsamkeit), quadratisch-absolute
Modelle veränderten fast alle Lebensmittel geringfügig.

Diese Demo baut dieselbe Modellstruktur nach - mit realen Einzel-Lebensmitteln
statt aggregierten FoodEx2-Gruppen, damit für Fitness-/Ernährungsinteressierte
sofort greifbar - und macht den Effekt der Zielfunktionsform live erlebbar.
Mathematisch ist das exakt die Sparsamkeits-Eigenschaft von L1- gegenüber
L2-Abweichungsstrafen (vgl. LASSO vs. Ridge Regression).

Wichtiger Hinweis: Dies ist eine Operations-Research-Demo, keine individuelle
Ernährungs- oder medizinische Beratung. Nährwerte sind gerundete Richtwerte,
Kalorien-/Makroziele grobe Fitness-Faustregeln.

Selbe Struktur wie bei den anderen Demos in diesem Workspace: Ergebnis zuerst,
vollständiger Methodenvergleich sekundär im Expander, dazu "Wie funktioniert
diese Demo?" und "Mathematische Formulierung" als eigene Expander.

Code-Struktur: Modell, Solver, Kennzahlen, PDF-Export und Visualisierung
liegen in den Modulen nutrition_*.py neben dieser Datei.
"""

import pandas as pd
import streamlit as st

from nutrition_constants import GOAL_PRESETS, OBJECTIVE_TYPES
from nutrition_evaluation import comparison_row, nutrient_totals
from nutrition_model import baseline_diet, food_bounds, nutrient_matrix, nutrient_targets
from nutrition_pdf_export import generate_diet_plan_pdf
from nutrition_presets import (
    apply_preset,
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sync_query_params,
)
from nutrition_solver import solve_all
from nutrition_visualization import diet_comparison_figure, macro_figure, sparsity_figure


@st.cache_data(show_spinner=False)
def _compute(goal, bodyweight, variation, seed, cache_key):
    baseline = baseline_diet(seed, variation)
    coeffs = nutrient_matrix()
    lower, upper = food_bounds()
    targets = nutrient_targets(goal, bodyweight)
    results = solve_all(baseline, coeffs, lower, upper, targets, OBJECTIVE_TYPES)
    return baseline, coeffs, targets, results


st.set_page_config(page_title="Ernährungsoptimierung – Sebastian Hanisch", layout="wide")

st.title("🥗 Ernährungsoptimierung")
st.markdown(
    """
Interaktive Demo zur **Ernährungsoptimierung**: Ausgehend von einer Beispiel-Ist-Ernährung
werden Lebensmittelmengen so angepasst, dass Kalorien- und Makronährstoffziele erreicht werden -
bei **möglichst geringer Abweichung** von der Ausgangsernährung. Kernthema ist, wie stark die
**Form der Zielfunktion** (linear vs. quadratisch, absolut vs. relativ) die Lösung verändert,
obwohl die Nebenbedingungen exakt gleich bleiben. Hintergrund im Expander "Wie funktioniert diese
Demo?" unten sowie formal hergeleitet im Expander "📐 Mathematische Formulierung".
"""
)
st.caption(
    "Keine individuelle Ernährungs- oder medizinische Beratung - Nährwerte sind gerundete "
    "Richtwerte, Kalorien-/Makroziele grobe Fitness-Faustregeln."
)

st.caption("🎯 Schnellstart – ein Beispielszenario laden:")
preset_col1, preset_col2, preset_col3 = st.columns(3)
with preset_col1:
    st.button(
        "🥗 Abnehmen (70 kg)", width="stretch",
        on_click=apply_preset, args=("Abnehmen (Kaloriendefizit)", 70.0, 0.2, 42),
        help="Kaloriendefizit, hoher Proteinanteil.",
    )
with preset_col2:
    st.button(
        "⚖️ Erhaltung (75 kg)", width="stretch",
        on_click=apply_preset, args=("Erhaltung", 75.0, 0.15, 7),
        help="Kalorien und Makros auf Erhaltungsniveau.",
    )
with preset_col3:
    st.button(
        "🏋️ Muskelaufbau (85 kg)", width="stretch",
        on_click=apply_preset, args=("Muskelaufbau (Kalorienüberschuss)", 85.0, 0.25, 3),
        help="Kalorienüberschuss, hoher Proteinanteil - stärkere Abweichung von der Ist-Ernährung.",
    )

st.caption(
    "🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, "
    "um ein Szenario zu teilen."
)

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    st.header("⚙️ Einstellungen")
    goal = st.selectbox("Ziel", options=list(GOAL_PRESETS.keys()), key="goal_select")
    bodyweight = st.slider("Körpergewicht (kg)", *bounds("bodyweight_slider"), step=1.0, key="bodyweight_slider")
    variation = st.slider(
        "Variation der Ist-Ernährung", *bounds("variation_slider"), step=0.05, key="variation_slider",
        help="Wie stark die Beispiel-Ist-Ernährung zufällig von den Standardmengen abweicht.",
    )
    seed_lo, seed_hi = bounds("seed_input")
    seed = st.number_input("Zufalls-Seed", min_value=seed_lo, max_value=seed_hi, step=1, key="seed_input")
    st.button(
        "🎲 Neue Beispiel-Ernährung generieren", width="stretch", on_click=randomize_seed,
        help="Würfelt einen neuen Zufalls-Seed für die Ist-Ernährung.",
    )

    st.markdown("**Zielfunktion für Hauptergebnis**")
    objective_label = st.selectbox(
        "Zielfunktionstyp", options=list(OBJECTIVE_TYPES.keys()), key="objective_select",
        help="linear-relativ entspricht am ehesten dem im Paper favorisierten Kompromiss: "
             "wenige, aber dafür prozentual größere Änderungen.",
    )

sync_query_params(goal, bodyweight, variation, int(seed), objective_label)

cache_key = (goal, bodyweight, variation, int(seed))
baseline, coeffs, targets, results = _compute(goal, bodyweight, variation, int(seed), cache_key)
main_result = results[objective_label]

st.markdown("## 🎯 Ihr optimierter Ernährungsplan")

totals = nutrient_totals(main_result.x, coeffs)
m1, m2, m3, m4 = st.columns(4)
m1.metric("Kalorien", f"{totals['kcal']:.0f} kcal", delta=f"Ziel {targets.kcal:.0f}")
m2.metric("Protein", f"{totals['protein_g']:.0f} g", delta=f"Ziel {targets.protein_g:.0f}")
m3.metric("Kohlenhydrate", f"{totals['carbs_g']:.0f} g", delta=f"Ziel {targets.carbs_g:.0f}")
m4.metric("Fett", f"{totals['fat_g']:.0f} g", delta=f"Ziel {targets.fat_g:.0f}")

if not main_result.success:
    st.warning("Der Solver hat für diese Konfiguration keine optimale Lösung bestätigt.")

st.plotly_chart(
    diet_comparison_figure(baseline, main_result.x, f"Basis- vs. optimierte Ernährung ({objective_label})"),
    width="stretch", key="diet_comparison_main",
)

pdf_bytes = generate_diet_plan_pdf(goal, bodyweight, targets, baseline, main_result, coeffs, objective_label)
st.download_button(
    "📄 Ernährungsplan als PDF herunterladen", data=pdf_bytes,
    file_name="ernaehrungsplan.pdf", mime="application/pdf",
)

st.markdown("---")
st.subheader("📐 Wie stark verändert die Form der Zielfunktion die Lösung?")
st.markdown(
    """
Kernthema dieser Demo: Alle vier Varianten unten lösen **exakt dieselben Nebenbedingungen**
(gleiche Kalorien-/Makroziele, gleiche Mengenobergrenzen je Lebensmittel) - sie unterscheiden sich
nur darin, wie die Abweichung von der Ist-Ernährung bestraft wird. **Linear** (Summe der Beträge,
vergleichbar mit einer L1-Strafe wie bei LASSO) bevorzugt **wenige, dafür größere** Änderungen
und lässt die meisten Lebensmittel unverändert. **Quadratisch** (Summe der Quadrate, vergleichbar
mit einer L2-Strafe wie bei Ridge Regression) verteilt die Anpassung stattdessen auf **viele kleine**
Änderungen. Genau dieser Effekt wurde von Schäfer et al. (2025) beim deutschen
Ernährungsguidelines-Update empirisch beobachtet (siehe Expander "Wie funktioniert diese Demo?").
"""
)

comparison_rows = [comparison_row(label, baseline, coeffs, results[label]) for label in OBJECTIVE_TYPES]
st.plotly_chart(sparsity_figure(comparison_rows), width="stretch", key="sparsity")

with st.expander("🔧 Vollständiger Vergleich aller vier Zielfunktionstypen", expanded=False):
    st.dataframe(pd.DataFrame(comparison_rows), width="stretch", hide_index=True)
    st.plotly_chart(
        macro_figure(targets, {label: nutrient_totals(results[label].x, coeffs) for label in OBJECTIVE_TYPES}),
        width="stretch", key="macro_comparison",
    )

    tabs = st.tabs(list(OBJECTIVE_TYPES.keys()))
    for tab, label in zip(tabs, OBJECTIVE_TYPES.keys()):
        with tab:
            r = results[label]
            st.plotly_chart(diet_comparison_figure(baseline, r.x, label), width="stretch", key=f"diet_comparison_{label}")

st.markdown("---")

with st.expander("Wie funktioniert diese Demo?"):
    st.markdown(
        """
**Die Problemstellung:** Aus einer Ist-Ernährung (Basismengen je Lebensmittel, g/Tag) soll eine
Ernährung abgeleitet werden, die Kalorien- und Makronährstoffziele erfüllt - mit **möglichst
geringer Abweichung** von den gewohnten Mengen. Das ist der klassische **"Diet Problem"**-Ansatz
der Operations Research (Stigler 1945), hier als **Zielprogrammierung** (Goal Programming)
formuliert: statt reiner Kostenminimierung wird die Abweichung von einem Referenzpunkt minimiert.

**Herkunft der Modellstruktur:** Diese Demo ist an die Methodik von Schäfer et al. (2025, PLOS
ONE), *"A methodological framework for deriving the German food-based dietary guidelines 2024"*,
angelehnt. Für die Aktualisierung der offiziellen deutschen Ernährungsempfehlungen (Deutsche
Gesellschaft für Ernährung) wurde dort exakt dieses Prinzip verwendet: Lebensmittelgruppen als
Entscheidungsvariablen, Minimierung der Abweichung von der beobachteten Ist-Ernährung (Deutsche
Nationale Verzehrsstudie II), Nährstoff-Zielwerte als Nebenbedingungen, Mengenobergrenzen aus
beobachteten Verzehrsperzentilen. Diese Demo verwendet statt aggregierter FoodEx2-Lebensmittelgruppen
reale Einzel-Lebensmittel und vereinfachte Fitness-Kalorien-/Makroziele - didaktisch näher an
Ernährungs-/Fitness-Alltagsfragen, mathematisch dieselbe Struktur.

**Ist-Ernährung:** Wird aus Basismengen je Lebensmittel synthetisch erzeugt: jede Menge wird
Seed-gesteuert um bis zu +/- der eingestellten Variation zufällig verschoben. Lebensmittel, die in
der Basis-Ernährung mit 0 g geführt werden, bleiben auch nach der Variation bei 0 g.

**Nährstoffziele:** Kalorien-, Protein- und Fettziele werden aus Körpergewicht und Ziel-Preset
(Abnehmen/Erhaltung/Muskelaufbau) über gängige Fitness-Faustregeln abgeleitet (kcal/Protein/Fett
je kg Körpergewicht), Kohlenhydrate füllen den verbleibenden Kalorienbedarf. Kalorien, Fett und
Kohlenhydrate werden als **Band** (z. B. Ziel +/- 3-35%) vorgegeben, Protein nur als **Mindestwert**
- mehr Protein ist im Modell nie ein Problem.

**Vier Zielfunktionstypen (der eigentliche Kern der Demo):** Für jedes Lebensmittel $i$ wird die
Abweichung $x_i - \\text{baseline}_i$ entweder **linear** (Betrag) oder **quadratisch** bestraft, und
entweder in **absoluten Gramm** oder **relativ** zur Basismenge gemessen - macht **vier Varianten**.
Linear entspricht mathematisch einer **L1-Strafe**: Ecken-Lösungen mit vielen exakt unveränderten
Variablen sind optimal (wie bei LASSO-Regression, wo L1-Regularisierung dünn besetzte Lösungen
erzeugt). Quadratisch entspricht einer **L2-Strafe**: der Grenznutzen einer kleinen Änderung ist bei
$x_i = \\text{baseline}_i$ null, sodass sich die Anpassung über viele Lebensmittel verteilt (wie bei
Ridge-Regression). Schäfer et al. (2025) fanden empirisch genau dieses Muster: In ihren
linear-relativen Modellen blieben 206-218 von 255 Lebensmittelgruppen unverändert, in den
quadratisch-absoluten Modellen nur 7-8.

**Mengenobergrenzen:** Jedes Lebensmittel hat eine realistische Tagesobergrenze (z. B. Olivenöl
max. 40 g, Kartoffeln max. 500 g) - vergleichbar mit den **Akzeptanzgrenzen** (5./95. Perzentil
beobachteter Verzehrsmengen) im Originalpaper, hier vereinfacht als feste Richtwerte statt aus
echten Verzehrsdaten berechnet.

**Lösungsverfahren:** Die linearen Varianten werden über Standard-Linearisierung des Betrags
(Hilfsvariablen $d_i \\geq |x_i - \\text{baseline}_i|$) als lineares Programm gelöst (SciPy/HiGHS),
die quadratischen Varianten als quadratisches Optimierungsproblem mit linearen Nebenbedingungen
(SciPy SLSQP, bei Konvergenzproblemen trust-constr) - im Originalpaper wurden dieselben vier
Varianten mit lpSolve (linear) bzw. quadprog (quadratisch) in R gelöst.

**In echten Ernährungsempfehlungen** kämen weitere Nährstoffe (Vitamine, Spurenelemente,
Ballaststoffe), Nachhaltigkeitsziele und deutlich mehr Lebensmittel dazu - das Grundprinzip aus
Abweichungsminimierung unter Nährstoff- und Mengen-Nebenbedingungen bleibt aber dasselbe.
"""
    )

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
Gegeben eine Ist-Ernährung $\text{baseline}_i \geq 0$ für $n$ Lebensmittel $i \in \{1, \ldots,
n\}$, Nährwertkoeffizienten $\text{kcal}_i, \text{prot}_i, \text{carb}_i, \text{fat}_i$ (je Gramm)
sowie Mengengrenzen $0 \leq x_i \leq \bar{x}_i$. Gesucht sind Mengen $x_i$ (g/Tag), die die
Abweichung von der Ist-Ernährung minimieren, unter Einhaltung der Nährstoffziele:
"""
    )
    st.latex(r"\text{kcal}_{\min} \leq \sum_i \text{kcal}_i\, x_i \leq \text{kcal}_{\max}")
    st.latex(r"\sum_i \text{prot}_i\, x_i \geq \text{prot}_{\min}")
    st.latex(r"\text{fat}_{\min} \leq \sum_i \text{fat}_i\, x_i \leq \text{fat}_{\max}, \qquad \text{carb}_{\min} \leq \sum_i \text{carb}_i\, x_i \leq \text{carb}_{\max}")
    st.latex(r"0 \leq x_i \leq \bar{x}_i \quad \forall i")
    st.markdown(
        r"""
Die vier Zielfunktionstypen unterscheiden sich nur in der Bewertung der Abweichung $x_i -
\text{baseline}_i$, mit Referenzwert $r_i = \max(\text{baseline}_i,\, 20\text{g})$ zur Vermeidung
einer Division durch 0 bei Lebensmitteln, die in der Ist-Ernährung nicht vorkommen:
"""
    )
    st.latex(r"\textbf{linear-absolut:} \quad \min \sum_i |x_i - \text{baseline}_i|")
    st.latex(r"\textbf{linear-relativ:} \quad \min \sum_i \frac{|x_i - \text{baseline}_i|}{r_i}")
    st.latex(r"\textbf{quadratisch-absolut:} \quad \min \sum_i (x_i - \text{baseline}_i)^2")
    st.latex(r"\textbf{quadratisch-relativ:} \quad \min \sum_i \left(\frac{x_i - \text{baseline}_i}{r_i}\right)^2")
    st.markdown(
        r"""
**Linearisierung des Betrags** (für die linearen Varianten): Mit Hilfsvariablen $d_i \geq 0$ und
den zwei linearen Nebenbedingungen $d_i \geq x_i - \text{baseline}_i$ sowie $d_i \geq
\text{baseline}_i - x_i$ gilt im Optimum stets $d_i = |x_i - \text{baseline}_i|$ (da die
Zielfunktion $d_i$ minimiert und $d_i$ sonst beliebig groß gewählt werden könnte) - damit wird
aus dem nicht-linearen Betrag ein Standard-lineares Programm (siehe `solve_linear()` in
`nutrition_solver.py`).

**Warum linear dünnbesetzte Lösungen erzeugt:** Am Optimum eines LP liegt die Lösung an einer
Ecke des zulässigen Polyeders. Für die absolute-Betrags-Zielfunktion bedeutet das: Lebensmittel,
die keine bindende Nebenbedingung berühren, bleiben exakt bei $x_i = \text{baseline}_i$ (Grenznutzen
einer Änderung ist konstant $\pm 1/r_i$, es gibt keinen Anreiz, mehr als nötig zu ändern) - nur so
viele Lebensmittel wie für die Erfüllung der Nährstoffziele nötig werden überhaupt angefasst.
Das ist strukturell identisch mit der Sparsamkeits-Eigenschaft von **L1-Regularisierung** (LASSO).

**Warum quadratisch alles ein bisschen ändert:** Die quadratische Zielfunktion hat am Punkt $x_i =
\text{baseline}_i$ einen Gradienten von $0$ - jede noch so kleine Änderung ist "billig", während
große Änderungen überproportional teuer werden. Es lohnt sich daher, die nötige Gesamtanpassung
auf **viele** Lebensmittel mit **kleinen** Änderungen zu verteilen, statt wenige stark zu ändern -
strukturell identisch mit **L2-Regularisierung** (Ridge Regression), die ebenfalls dichte statt
dünnbesetzte Lösungen erzeugt.

**Bezug zum Code:** `nutrition_model.py` baut Nährstoffziele, Ist-Ernährung und
Nährwertkoeffizienten auf. `nutrition_solver.py` setzt die Formulierungen oben 1:1 um:
`solve_linear()` (SciPy `linprog`, HiGHS) für die linearen Varianten, `solve_quadratic()` (SciPy
`minimize`, SLSQP mit trust-constr als Fallback) für die quadratischen. `nutrition_evaluation.py`
berechnet die Vergleichskennzahlen (Summe absoluter/relativer Änderung, Anzahl unverändert/
gestiegen/gesunken/verschwunden) - dieselben Kennzahlen, die Schäfer et al. (2025) zum Vergleich
ihrer zwölf Modellvarianten verwendet haben.

**Quelle:** Schäfer AC, Boeing H, Gazan R, et al. (2025) *A methodological framework for deriving
the German food-based dietary guidelines 2024: Food groups, nutrient goals, and objective
functions.* PLoS ONE 20(3): e0313347. https://doi.org/10.1371/journal.pone.0313347
"""
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning. Interesse an einer maßgeschneiderten Lösung für "
    "Ihr Unternehmen? [Kontakt aufnehmen](https://sebastianhanisch.net/kontakt.html)"
)
