"""
Unit-Tests der reinen Modell-/Solver-/Bewertungslogik (kein Streamlit-UI-Code).

Ausführen mit: pytest tests/ -v
"""

import os
import sys

import numpy as np
import pytest

APP_DIR = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.abspath(APP_DIR))

from nutrition_constants import FOODS, GOAL_PRESETS, OBJECTIVE_TYPES
from nutrition_evaluation import change_counts, nutrient_totals, sum_absolute_change
from nutrition_model import baseline_diet, food_bounds, nutrient_matrix, nutrient_targets
from nutrition_pdf_export import generate_diet_plan_pdf
from nutrition_solver import solve, solve_all


@pytest.fixture
def coeffs():
    return nutrient_matrix()


@pytest.fixture
def bounds_():
    return food_bounds()


# ==========================================================================
# Nährstoffziele
# ==========================================================================

def test_nutrient_targets_scale_with_bodyweight():
    t60 = nutrient_targets("Erhaltung", 60.0)
    t90 = nutrient_targets("Erhaltung", 90.0)
    assert t90.kcal > t60.kcal
    assert t90.protein_g > t60.protein_g


def test_cutting_has_lower_calories_than_bulking_for_same_weight():
    cut = nutrient_targets("Abnehmen (Kaloriendefizit)", 80.0)
    bulk = nutrient_targets("Muskelaufbau (Kalorienüberschuss)", 80.0)
    assert cut.kcal < bulk.kcal


def test_carbs_never_negative():
    for preset in GOAL_PRESETS:
        t = nutrient_targets(preset, 40.0)
        assert t.carbs_g >= 0.0


# ==========================================================================
# Basis-Ernährung
# ==========================================================================

def test_baseline_diet_deterministic():
    b1 = baseline_diet(seed=42, variation=0.2)
    b2 = baseline_diet(seed=42, variation=0.2)
    assert (b1 == b2).all()


def test_baseline_diet_different_seed_differs():
    b1 = baseline_diet(seed=42, variation=0.2)
    b2 = baseline_diet(seed=43, variation=0.2)
    assert not (b1 == b2).all()


def test_baseline_diet_zero_stays_zero():
    """Lebensmittel, die in der Basis-Ernährung mit 0 g geführt werden,
    dürfen durch die Zufallsvariation nicht plötzlich auftauchen."""
    baseline = baseline_diet(seed=1, variation=0.5)
    zero_indices = [i for i, f in enumerate(FOODS) if f.baseline_g == 0]
    assert all(baseline[i] == 0.0 for i in zero_indices)


def test_baseline_diet_within_bounds():
    lower, upper = food_bounds()
    baseline = baseline_diet(seed=7, variation=0.3)
    assert (baseline >= lower - 1e-9).all()
    assert (baseline <= upper + 1e-9).all()


# ==========================================================================
# Solver: Machbarkeit und Nebenbedingungen
# ==========================================================================

@pytest.mark.parametrize("preset", list(GOAL_PRESETS.keys()))
@pytest.mark.parametrize("objective_label", list(OBJECTIVE_TYPES.keys()))
def test_all_objective_types_feasible_across_presets(preset, objective_label, coeffs, bounds_):
    lower, upper = bounds_
    targets = nutrient_targets(preset, 80.0)
    baseline = baseline_diet(seed=42, variation=0.2)
    result = solve(OBJECTIVE_TYPES[objective_label], baseline, coeffs, lower, upper, targets)
    assert result.success, f"{objective_label}/{preset} sollte lösbar sein"


def test_solution_respects_nutrient_bands(coeffs, bounds_):
    lower, upper = bounds_
    targets = nutrient_targets("Erhaltung", 80.0)
    baseline = baseline_diet(seed=42, variation=0.2)
    result = solve(OBJECTIVE_TYPES["linear-relativ"], baseline, coeffs, lower, upper, targets)
    totals = nutrient_totals(result.x, coeffs)

    kcal_lo, kcal_hi = targets.kcal_band
    fat_lo, fat_hi = targets.fat_band
    carbs_lo, carbs_hi = targets.carbs_band
    assert kcal_lo - 1e-3 <= totals["kcal"] <= kcal_hi + 1e-3
    assert totals["protein_g"] >= targets.protein_g - 1e-3
    assert fat_lo - 1e-3 <= totals["fat_g"] <= fat_hi + 1e-3
    assert carbs_lo - 1e-3 <= totals["carbs_g"] <= carbs_hi + 1e-3


def test_solution_respects_food_bounds(coeffs, bounds_):
    lower, upper = bounds_
    targets = nutrient_targets("Muskelaufbau (Kalorienüberschuss)", 100.0)
    baseline = baseline_diet(seed=3, variation=0.2)
    result = solve(OBJECTIVE_TYPES["quadratisch-absolut"], baseline, coeffs, lower, upper, targets)
    assert (result.x >= lower - 1e-6).all()
    assert (result.x <= upper + 1e-6).all()


def test_zero_target_deviation_gives_zero_objective_when_baseline_already_feasible(coeffs, bounds_):
    """Erfüllt die Basis-Ernährung die Nährstoffziele bereits exakt, darf
    keine der vier Zielfunktionen eine Änderung vorschlagen."""
    lower, upper = bounds_
    baseline = baseline_diet(seed=42, variation=0.2)
    totals = nutrient_totals(baseline, coeffs)
    targets = nutrient_targets("Erhaltung", 80.0)._replace(
        kcal_band=(totals["kcal"] - 1, totals["kcal"] + 1),
        protein_g=totals["protein_g"] - 1,
        fat_band=(totals["fat_g"] - 1, totals["fat_g"] + 1),
        carbs_band=(totals["carbs_g"] - 1, totals["carbs_g"] + 1),
    )
    for label, obj in OBJECTIVE_TYPES.items():
        result = solve(obj, baseline, coeffs, lower, upper, targets)
        assert result.objective == pytest.approx(0.0, abs=1e-3), label


# ==========================================================================
# Kernthema: linear vs. quadratisch -> Sparsamkeit vs. Verteilung
# ==========================================================================

def test_linear_leaves_more_foods_unchanged_than_quadratic(coeffs, bounds_):
    """Zentraler didaktischer Befund der Demo (und von Schäfer et al. 2025
    empirisch beobachtet): lineare Zielfunktionen liefern dünnbesetzte
    Lösungen (viele unveränderte Lebensmittel), quadratische verteilen die
    Anpassung auf fast alle Lebensmittel."""
    lower, upper = bounds_
    targets = nutrient_targets("Muskelaufbau (Kalorienüberschuss)", 100.0)
    baseline = baseline_diet(seed=42, variation=0.2)
    results = solve_all(baseline, coeffs, lower, upper, targets, OBJECTIVE_TYPES)

    unchanged_linear = change_counts(baseline, results["linear-relativ"].x)["unverändert"]
    unchanged_quadratic = change_counts(baseline, results["quadratisch-relativ"].x)["unverändert"]
    assert unchanged_linear > unchanged_quadratic


def test_relative_objective_uses_reference_for_zero_baseline_foods(coeffs, bounds_):
    """Lebensmittel mit Basismenge 0 dürfen bei der relativen Zielfunktion
    nicht zu einer Division durch 0 führen."""
    lower, upper = bounds_
    targets = nutrient_targets("Erhaltung", 80.0)
    baseline = baseline_diet(seed=42, variation=0.2)
    assert (baseline == 0).any(), "Testvoraussetzung: mind. ein Lebensmittel mit Basismenge 0"
    result = solve(OBJECTIVE_TYPES["linear-relativ"], baseline, coeffs, lower, upper, targets)
    assert np.isfinite(result.objective)


# ==========================================================================
# Kennzahlen
# ==========================================================================

def test_sum_absolute_change_zero_when_unchanged():
    baseline = np.array([100.0, 50.0, 0.0])
    assert sum_absolute_change(baseline, baseline) == 0.0


def test_change_counts_basic():
    baseline = np.array([100.0, 50.0, 0.0, 30.0])
    x = np.array([150.0, 0.0, 0.0, 30.0])
    counts = change_counts(baseline, x)
    assert counts["gestiegen"] == 1
    assert counts["verschwunden"] == 1
    assert counts["unverändert"] == 2
    assert counts["gesunken"] == 0


def test_nutrient_totals_matches_manual_calculation(coeffs):
    x = np.zeros(len(FOODS))
    x[0] = 100.0  # 100 g des ersten Lebensmittels
    totals = nutrient_totals(x, coeffs)
    assert totals["kcal"] == pytest.approx(FOODS[0].kcal)
    assert totals["protein_g"] == pytest.approx(FOODS[0].protein)


# ==========================================================================
# PDF-Export
# ==========================================================================

def test_pdf_export_returns_bytes(coeffs, bounds_):
    lower, upper = bounds_
    targets = nutrient_targets("Erhaltung", 80.0)
    baseline = baseline_diet(seed=42, variation=0.2)
    result = solve(OBJECTIVE_TYPES["linear-relativ"], baseline, coeffs, lower, upper, targets)
    pdf_bytes = generate_diet_plan_pdf("Erhaltung", 80.0, targets, baseline, result, coeffs, "linear-relativ")
    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes[:4] == b"%PDF"
