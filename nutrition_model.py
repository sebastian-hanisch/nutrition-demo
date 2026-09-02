"""Modellaufbau: Nährstoffziele aus Körpergewicht/Ziel-Preset, Basis-Ernährung mit
optionaler Zufallsvariation, sowie die Nährstoff-Koeffizientenmatrix für den Solver.
"""

from collections import namedtuple

import numpy as np

from nutrition_constants import FOODS, GOAL_PRESETS

NutrientTargets = namedtuple(
    "NutrientTargets",
    ["kcal", "protein_g", "fat_g", "carbs_g", "kcal_band", "fat_band", "carbs_band"],
)


def nutrient_targets(preset_name, bodyweight_kg):
    """Tagesziele für Kalorien/Makros aus Körpergewicht und Ziel-Preset ableiten.

    Grobe, in der Fitness-Praxis gängige Faustregeln (kcal/Protein/Fett je kg
    Körpergewicht) - Kohlenhydrate füllen den restlichen Kalorienbedarf auf.
    Keine individuelle Ernährungs- oder medizinische Beratung.
    """
    preset = GOAL_PRESETS[preset_name]
    kcal = preset["kcal_per_kg"] * bodyweight_kg
    protein_g = preset["protein_per_kg"] * bodyweight_kg
    fat_g = preset["fat_per_kg"] * bodyweight_kg
    remaining_kcal = max(kcal - protein_g * 4 - fat_g * 9, 0.0)
    carbs_g = remaining_kcal / 4
    return NutrientTargets(
        kcal=kcal,
        protein_g=protein_g,
        fat_g=fat_g,
        carbs_g=carbs_g,
        kcal_band=(kcal * 0.97, kcal * 1.03),
        fat_band=(fat_g * 0.75, fat_g * 1.35),
        carbs_band=(carbs_g * 0.65, carbs_g * 1.35),
    )


def baseline_diet(seed, variation):
    """Beispielhafte 'aktuelle Ernährung' (g/Tag je Lebensmittel).

    Ausgehend von den Basismengen in FOODS wird jede Menge um bis zu
    +/- `variation` (Anteil) zufällig verschoben (Seed-gesteuert), damit sich
    unterschiedliche Ausgangs-Ernährungen durchspielen lassen.
    """
    rng = np.random.default_rng(seed)
    baseline = np.array([f.baseline_g for f in FOODS], dtype=float)
    factors = 1.0 + rng.uniform(-variation, variation, size=len(FOODS))
    varied = baseline * factors
    # Lebensmittel, die in der Basis-Ernährung nicht vorkommen (0 g), bleiben 0 -
    # sonst könnte z.B. plötzlich Whey Protein auftauchen, ohne dass es je Teil
    # der Ausgangsernährung war.
    varied[baseline == 0] = 0.0
    return np.clip(varied, 0.0, [f.max_g for f in FOODS])


def nutrient_matrix():
    """kcal/Protein/Kohlenhydrat/Fett-Koeffizienten je Gramm Lebensmittel (n_foods x 4)."""
    coeffs = np.array([[f.kcal, f.protein, f.carbs, f.fat] for f in FOODS], dtype=float)
    return coeffs / 100.0  # Werte in FOODS sind je 100 g


def food_bounds():
    lower = np.zeros(len(FOODS))
    upper = np.array([f.max_g for f in FOODS], dtype=float)
    return lower, upper
