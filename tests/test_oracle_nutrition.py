"""Orakel-Tests: Solver und Kennzahlen gegen unabhängige Rechenwege.

* Lineare Varianten: LP in anderer Formulierung (x = b + p - m, p, m >= 0, ohne
  Hilfsvariablen-Ungleichungen) mit dem Innere-Punkte-Löser von HiGHS.
* Quadratische Varianten: Dualproblem (x_i(lambda) = auf die Grenzen beschnittener
  Punkt b_i - r_i^2 (A^T lambda)_i / 2, Maximierung über lambda >= 0) statt SLSQP.
* Kennzahlen: Schleifen-Nachrechnung von Zählern, Summen und Nährstoffsummen.
"""

import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from nutrition_constants import FOODS, GOAL_PRESETS, MIN_REFERENCE_G, OBJECTIVE_TYPES
from nutrition_evaluation import change_counts, mean_relative_change_pct, nutrient_totals
from nutrition_model import baseline_diet, food_bounds, nutrient_matrix, nutrient_targets
from nutrition_solver import solve

linprog = pytest.importorskip("scipy.optimize").linprog
minimize = pytest.importorskip("scipy.optimize").minimize

N = len(FOODS)
COEFFS = nutrient_matrix()
LOWER, UPPER = food_bounds()

CASES = [
    ("Abnehmen (Kaloriendefizit)", 70.0, 0.2, 42),
    ("Erhaltung", 75.0, 0.15, 7),
    ("Muskelaufbau (Kalorienüberschuss)", 85.0, 0.25, 3),
    ("Erhaltung", 110.0, 0.4, 991),
    ("Abnehmen (Kaloriendefizit)", 55.0, 0.05, 12345),
]


def _rows(t):
    """(Koeffizienten, untere, obere Schranke) je Nährstoff - unabhängig vom Solver aufgebaut."""
    return [
        (COEFFS[:, 0], t.kcal_band[0], t.kcal_band[1]),
        (COEFFS[:, 1], t.protein_g, np.inf),
        (COEFFS[:, 3], t.fat_band[0], t.fat_band[1]),
        (COEFFS[:, 2], t.carbs_band[0], t.carbs_band[1]),
    ]


def _ref(b, relative):
    return np.maximum(b, MIN_REFERENCE_G) if relative else np.ones(N)


def _lp_value(b, t, relative):
    ref = _ref(b, relative)
    c = np.concatenate([1 / ref, 1 / ref])
    a_ub, b_ub = [], []
    for a, lo, hi in _rows(t):
        row = np.concatenate([a, -a])
        if np.isfinite(hi):
            a_ub.append(row)
            b_ub.append(hi - a @ b)
        if np.isfinite(lo):
            a_ub.append(-row)
            b_ub.append(a @ b - lo)
    bounds = [(0, UPPER[i] - b[i]) for i in range(N)] + [(0, b[i] - LOWER[i]) for i in range(N)]
    res = linprog(c, A_ub=np.array(a_ub), b_ub=np.array(b_ub), bounds=bounds, method="highs-ipm")
    assert res.success
    return res.fun


def _qp_dual_value(b, t, relative):
    w = _ref(b, relative) ** 2
    rows = []
    for a, lo, hi in _rows(t):
        if np.isfinite(hi):
            rows.append((a, hi))
        if np.isfinite(lo):
            rows.append((-a, -lo))
    A = np.array([r[0] for r in rows])
    rhs = np.array([r[1] for r in rows])

    def neg_dual(lam):
        x = np.clip(b - w * (A.T @ lam) / 2.0, LOWER, UPPER)
        g = A @ x - rhs
        return -(np.sum((x - b) ** 2 / w) + lam @ g), -g

    res = minimize(neg_dual, np.zeros(len(rows)), jac=True, method="L-BFGS-B",
                   bounds=[(0, None)] * len(rows), options={"maxiter": 5000, "ftol": 1e-15, "gtol": 1e-12})
    return -res.fun


def _feasible(x, t, tol=1e-4):
    if (x < LOWER - tol).any() or (x > UPPER + tol).any():
        return False
    return all(lo - tol * max(1, abs(lo)) <= a @ x <= hi + tol * max(1, abs(hi)) for a, lo, hi in _rows(t))


@pytest.mark.parametrize("case", CASES)
@pytest.mark.parametrize("label", list(OBJECTIVE_TYPES))
def test_solver_value_matches_independent_formulation(case, label):
    preset, bw, var, seed = case
    b = baseline_diet(seed, var)
    t = nutrient_targets(preset, bw)
    obj = OBJECTIVE_TYPES[label]
    relative = obj["scale"] == "relativ"
    r = solve(obj, b, COEFFS, LOWER, UPPER, t)
    assert r.success
    assert _feasible(r.x, t)
    ref = _ref(b, relative)
    if obj["shape"] == "linear":
        mine = float(np.sum(np.abs(r.x - b) / ref))
        oracle = _lp_value(b, t, relative)
    else:
        mine = float(np.sum(((r.x - b) / ref) ** 2))
        oracle = _qp_dual_value(b, t, relative)
    assert mine == pytest.approx(oracle, rel=1e-5, abs=1e-6)
    assert r.objective == pytest.approx(oracle, rel=1e-5, abs=1e-6)


def test_metrics_match_loop_recomputation():
    rng = np.random.default_rng(5)
    for _ in range(20):
        b = baseline_diet(int(rng.integers(0, 10**6)), 0.3)
        x = np.clip(b + rng.normal(0, 40, N) * (rng.random(N) < 0.5), LOWER, UPPER)
        x[:3] = np.clip(b[:3] + np.array([1.0, -1.0, 0.99]), LOWER[:3], UPPER[:3])  # Rand der 1-g-Toleranz
        inc = dec = dis = unc = 0
        for i in range(N):
            d = x[i] - b[i]
            if d > 1.0:
                inc += 1
            elif d < -1.0:
                if x[i] < 1.0 and b[i] >= 1.0:
                    dis += 1
                else:
                    dec += 1
            else:
                unc += 1
        c = change_counts(b, x)
        assert (c["gestiegen"], c["gesunken"], c["verschwunden"], c["unverändert"]) == (inc, dec, dis, unc)
        rel = np.mean([abs(x[i] - b[i]) / max(b[i], 20.0) for i in range(N)]) * 100
        assert mean_relative_change_pct(b, x) == pytest.approx(rel, abs=1e-9)
        tot = nutrient_totals(x, COEFFS)
        fields = {"kcal": "kcal", "protein_g": "protein", "carbs_g": "carbs", "fat_g": "fat"}
        for key, attr in fields.items():
            assert tot[key] == pytest.approx(sum(x[i] * getattr(FOODS[i], attr) for i in range(N)) / 100.0, abs=1e-9)


def test_linear_changes_at_most_binding_constraints_plus_bound_foods():
    """README/Herleitung: bei linearen Varianten werden höchstens so viele Lebensmittel (nicht an
    einer Mengengrenze) verändert, wie Nährstoffbedingungen bindend sind (Ecken-Lösung)."""
    for preset, bw, var, seed in CASES:
        b = baseline_diet(seed, var)
        t = nutrient_targets(preset, bw)
        for label in ("linear-relativ", "linear-absolut"):
            x = solve(OBJECTIVE_TYPES[label], b, COEFFS, LOWER, UPPER, t).x
            free = sum(1 for i in range(N) if abs(x[i] - b[i]) > 1e-6 and LOWER[i] + 1e-6 < x[i] < UPPER[i] - 1e-6)
            binding = 0
            for a, lo, hi in _rows(t):
                v = a @ x
                binding += int(np.isfinite(lo) and abs(v - lo) < 1e-6 * max(1, abs(lo)))
                binding += int(np.isfinite(hi) and abs(v - hi) < 1e-6 * max(1, abs(hi)))
            assert free <= binding
