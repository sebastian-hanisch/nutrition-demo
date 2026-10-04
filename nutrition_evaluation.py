"""Kennzahlen zum Vergleich der optimierten Ernährungen - angelehnt an die
Vergleichsmetriken aus Schäfer et al. (2025, PLOS ONE) für die deutschen
Ernährungsempfehlungen: Summe absoluter und mittlere relative Änderung sowie
Anzahl gestiegener/gesunkener/verschwundener/unveränderter Lebensmittel.
"""

import numpy as np

from nutrition_constants import MIN_REFERENCE_G

UNCHANGED_TOLERANCE_G = 1.0
DISAPPEARED_TOLERANCE_G = 1.0


def sum_absolute_change(baseline, x):
    return float(np.sum(np.abs(x - baseline)))


def mean_relative_change_pct(baseline, x):
    """Mittlere relative Änderung über alle Lebensmittel in Prozent. Referenz ist
    wie in den relativen Zielfunktionen max(Basismenge, MIN_REFERENCE_G): bei
    Lebensmitteln mit 0 g in der Basis (hier 9 von 25) würde eine Referenz von
    1 g schon 5 g Zunahme als 500 % werten und den Mittelwert dominieren."""
    ref = np.maximum(baseline, MIN_REFERENCE_G)
    return float(np.mean(np.abs(x - baseline) / ref) * 100)


def change_counts(baseline, x):
    diff = x - baseline
    increased = int(np.sum(diff > UNCHANGED_TOLERANCE_G))
    decreased_mask = diff < -UNCHANGED_TOLERANCE_G
    disappeared = int(np.sum(decreased_mask & (x < DISAPPEARED_TOLERANCE_G) & (baseline >= DISAPPEARED_TOLERANCE_G)))
    decreased = int(np.sum(decreased_mask)) - disappeared
    unchanged = int(len(baseline) - increased - decreased - disappeared)
    return {"gestiegen": increased, "gesunken": decreased, "verschwunden": disappeared, "unverändert": unchanged}


def nutrient_totals(x, coeffs):
    totals = coeffs.T @ x
    return {"kcal": float(totals[0]), "protein_g": float(totals[1]), "carbs_g": float(totals[2]), "fat_g": float(totals[3])}


def comparison_row(label, baseline, coeffs, result):
    counts = change_counts(baseline, result.x)
    totals = nutrient_totals(result.x, coeffs)
    return {
        "Zielfunktion": label,
        "Summe abs. Änderung (g)": round(sum_absolute_change(baseline, result.x), 0),
        "Mittl. rel. Änderung (%)": round(mean_relative_change_pct(baseline, result.x), 1),
        "Unverändert": counts["unverändert"],
        "Gestiegen": counts["gestiegen"],
        "Gesunken": counts["gesunken"],
        "Verschwunden": counts["verschwunden"],
        "kcal": round(totals["kcal"]),
        "Protein (g)": round(totals["protein_g"], 1),
        "Konvergiert?": "Ja" if result.success else "Nein",
    }
