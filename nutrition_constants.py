"""Stammdaten: Lebensmittel-Nährwerte, Basis-Ernährung, Akzeptanzgrenzen, Ziel-Presets.

Nährwerte pro 100 g (kcal, Protein/Kohlenhydrate/Fett in g) sind gerundete
Richtwerte aus gängigen Nährwerttabellen (z. B. USDA FoodData Central,
Bundeslebensmittelschlüssel) - für eine Demo hinreichend genau, aber keine
medizinische oder ernährungswissenschaftliche Beratung.
"""

from collections import namedtuple

Food = namedtuple("Food", ["name", "category", "kcal", "protein", "carbs", "fat", "baseline_g", "max_g"])

# name, category, kcal/100g, protein/100g, carbs/100g, fat/100g, Basismenge (g/Tag), Akzeptanzobergrenze (g/Tag)
FOODS = [
    Food("Hähnchenbrust", "Protein", 110, 23.0, 0.0, 1.2, 120, 400),
    Food("Rindfleisch (mager)", "Protein", 137, 21.0, 0.0, 5.0, 0, 300),
    Food("Lachs", "Protein", 208, 20.0, 0.0, 13.0, 0, 250),
    Food("Tofu", "Protein", 76, 8.0, 1.9, 4.8, 0, 300),
    Food("Eier", "Protein", 155, 13.0, 1.1, 11.0, 100, 240),
    Food("Magerquark", "Milchprodukte", 67, 12.0, 4.0, 0.2, 150, 500),
    Food("Griechischer Joghurt", "Milchprodukte", 59, 10.0, 3.6, 0.4, 150, 500),
    Food("Milch 1,5%", "Milchprodukte", 47, 3.4, 4.8, 1.5, 200, 600),
    Food("Whey Protein", "Protein", 380, 80.0, 8.0, 6.0, 0, 90),
    Food("Haferflocken", "Getreide", 372, 13.0, 60.0, 7.0, 60, 150),
    Food("Reis (gekocht)", "Getreide", 130, 2.7, 28.0, 0.3, 150, 500),
    Food("Vollkornnudeln (gekocht)", "Getreide", 124, 5.0, 25.0, 1.0, 0, 500),
    Food("Vollkornbrot", "Getreide", 247, 9.0, 41.0, 3.3, 80, 300),
    Food("Kartoffeln (gekocht)", "Gemüse", 87, 1.9, 20.0, 0.1, 200, 500),
    Food("Linsen (gekocht)", "Hülsenfrüchte", 116, 9.0, 20.0, 0.4, 0, 300),
    Food("Kichererbsen (gekocht)", "Hülsenfrüchte", 164, 8.9, 27.0, 2.6, 0, 300),
    Food("Brokkoli", "Gemüse", 34, 2.8, 7.0, 0.4, 100, 400),
    Food("Spinat", "Gemüse", 23, 2.9, 3.6, 0.4, 0, 300),
    Food("Tomaten", "Gemüse", 18, 0.9, 3.9, 0.2, 100, 400),
    Food("Banane", "Obst", 89, 1.1, 23.0, 0.3, 120, 350),
    Food("Apfel", "Obst", 52, 0.3, 14.0, 0.2, 150, 400),
    Food("Mandeln", "Fette", 579, 21.0, 22.0, 50.0, 20, 60),
    Food("Walnüsse", "Fette", 654, 15.0, 14.0, 65.0, 0, 50),
    Food("Olivenöl", "Fette", 884, 0.0, 0.0, 100.0, 15, 40),
    Food("Butter", "Fette", 717, 0.9, 0.1, 81.0, 10, 30),
]

FOOD_NAMES = [f.name for f in FOODS]
CATEGORIES = sorted({f.category for f in FOODS})

# g Protein/Fett je kg Körpergewicht, kcal je kg Körpergewicht - grobe, in der
# Fitness-Praxis gängige Faustregeln, keine individuelle Ernährungsberatung.
GOAL_PRESETS = {
    "Abnehmen (Kaloriendefizit)": {"kcal_per_kg": 28.0, "protein_per_kg": 2.2, "fat_per_kg": 0.8},
    "Erhaltung": {"kcal_per_kg": 33.0, "protein_per_kg": 1.8, "fat_per_kg": 1.0},
    "Muskelaufbau (Kalorienüberschuss)": {"kcal_per_kg": 38.0, "protein_per_kg": 1.8, "fat_per_kg": 1.0},
}

OBJECTIVE_TYPES = {
    "linear-relativ": {"shape": "linear", "scale": "relativ"},
    "linear-absolut": {"shape": "linear", "scale": "absolut"},
    "quadratisch-relativ": {"shape": "quadratisch", "scale": "relativ"},
    "quadratisch-absolut": {"shape": "quadratisch", "scale": "absolut"},
}
