"""Löst die Ernährungsoptimierung für die vier Zielfunktionstypen
(linear/quadratisch x absolut/relativ) - gleiche Nebenbedingungen, unterschiedliche
Bewertung der Abweichung von der Basis-Ernährung je Lebensmittel.
"""

from collections import namedtuple

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, linprog, minimize

SolveResult = namedtuple("SolveResult", ["x", "objective", "status", "success"])

# Referenzmenge (g) für die relative Gewichtung bei Lebensmitteln, die in der
# Basis-Ernährung mit 0 g auftreten - eine echte relative Abweichung (x/0) ist
# dort nicht definiert, 20 g dient als plausibler unterer Referenzwert.
MIN_REFERENCE_G = 20.0


def _reference(baseline):
    return np.maximum(baseline, MIN_REFERENCE_G)


def _nutrient_constraints(coeffs, targets):
    """Baut die (identischen) Nährstoff-Nebenbedingungen als A_ub x <= b_ub."""
    kcal, protein, carbs, fat = coeffs[:, 0], coeffs[:, 1], coeffs[:, 2], coeffs[:, 3]
    kcal_lo, kcal_hi = targets.kcal_band
    fat_lo, fat_hi = targets.fat_band
    carbs_lo, carbs_hi = targets.carbs_band

    rows = [
        (kcal, kcal_hi),
        (-kcal, -kcal_lo),
        (-protein, -targets.protein_g),
        (fat, fat_hi),
        (-fat, -fat_lo),
        (carbs, carbs_hi),
        (-carbs, -carbs_lo),
    ]
    A = np.array([r[0] for r in rows])
    b = np.array([r[1] for r in rows])
    return A, b


def solve_linear(baseline, coeffs, lower, upper, targets, relative):
    """Minimiert die Summe der (relativen oder absoluten) Abweichungen |x-baseline|
    über Hilfsvariablen d_i >= |x_i - baseline_i| (Standard-Linearisierung)."""
    n = len(baseline)
    ref = _reference(baseline) if relative else np.ones(n)
    weights = 1.0 / ref

    # Variablenvektor: [x_0..x_{n-1}, d_0..d_{n-1}]
    c = np.concatenate([np.zeros(n), weights])

    A_nut, b_nut = _nutrient_constraints(coeffs, targets)
    A_nut_full = np.hstack([A_nut, np.zeros((A_nut.shape[0], n))])

    # d_i >= x_i - baseline_i  <=>  x_i - d_i <= baseline_i
    A1 = np.hstack([np.eye(n), -np.eye(n)])
    b1 = baseline
    # d_i >= baseline_i - x_i  <=>  -x_i - d_i <= -baseline_i
    A2 = np.hstack([-np.eye(n), -np.eye(n)])
    b2 = -baseline

    A_ub = np.vstack([A_nut_full, A1, A2])
    b_ub = np.concatenate([b_nut, b1, b2])

    bounds = [(lower[i], upper[i]) for i in range(n)] + [(0, None)] * n

    res = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method="highs")
    x = res.x[:n] if res.success else baseline.copy()
    objective = float(np.sum(weights * np.abs(x - baseline)))
    return SolveResult(x=x, objective=objective, status=res.message, success=res.success)


def solve_quadratic(baseline, coeffs, lower, upper, targets, relative):
    """Minimiert die Summe der quadrierten (relativen oder absoluten) Abweichungen."""
    n = len(baseline)
    ref = _reference(baseline) if relative else np.ones(n)

    def objective(x):
        d = (x - baseline) / ref
        return float(np.sum(d ** 2))

    def gradient(x):
        return 2.0 * (x - baseline) / (ref ** 2)

    A_nut, b_nut = _nutrient_constraints(coeffs, targets)
    constraint = LinearConstraint(A_nut, -np.inf, b_nut)
    bounds = Bounds(lower, upper)

    x0 = np.clip(baseline, lower, upper)
    res = minimize(
        objective, x0, jac=gradient, method="SLSQP",
        bounds=bounds, constraints=[constraint], options={"maxiter": 1000, "ftol": 1e-12},
    )
    if not res.success:
        # SLSQP kann bei sehr unterschiedlich skalierten Variablen (große
        # Mengenänderungen bei quadratisch-absolut) hängen bleiben - trust-constr
        # ist für diese Fälle robuster, wenn auch etwas langsamer.
        res = minimize(
            objective, x0, jac=gradient, method="trust-constr",
            bounds=bounds, constraints=[constraint],
            options={"maxiter": 2000, "gtol": 1e-10, "xtol": 1e-12},
        )
    x = res.x if res.success else baseline.copy()
    return SolveResult(x=x, objective=float(objective(x)), status=res.message, success=bool(res.success))


def solve(objective_type, baseline, coeffs, lower, upper, targets):
    shape = objective_type["shape"]
    relative = objective_type["scale"] == "relativ"
    if shape == "linear":
        return solve_linear(baseline, coeffs, lower, upper, targets, relative)
    return solve_quadratic(baseline, coeffs, lower, upper, targets, relative)


def solve_all(baseline, coeffs, lower, upper, targets, objective_types):
    return {label: solve(obj, baseline, coeffs, lower, upper, targets) for label, obj in objective_types.items()}
