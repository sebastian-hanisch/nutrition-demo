"""Erzeugt einen Ernährungsplan als downloadbares PDF (in-memory).

Umlaute sind unproblematisch (Latin-1, von der FPDF-Kernschrift Helvetica
unterstützt) - vermieden werden nur echte Sonderzeichen wie Halbgeviertstriche
(–), die die Kernschrift nicht darstellen kann (siehe shift_pdf_export.py für
den Bug, der diese Konvention im Portfolio etabliert hat).
"""

import time

from nutrition_constants import FOOD_NAMES
from nutrition_evaluation import nutrient_totals


def generate_diet_plan_pdf(goal_label, bodyweight, targets, baseline, result, coeffs, objective_label):
    from fpdf import FPDF
    from fpdf.enums import XPos, YPos

    totals = nutrient_totals(result.x, coeffs)

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Ernährungsplan (Optimierungs-Demo)", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 6, f"Erstellt: {time.strftime('%d.%m.%Y %H:%M')} Uhr", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "Zusammenfassung", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"Ziel: {goal_label}, Körpergewicht: {bodyweight:.0f} kg", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 6, f"Zielfunktion: {objective_label}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(
        0, 6,
        f"Ziel: {targets.kcal:.0f} kcal, {targets.protein_g:.0f} g Protein, "
        f"{targets.carbs_g:.0f} g Kohlenhydrate, {targets.fat_g:.0f} g Fett",
        new_x=XPos.LMARGIN, new_y=YPos.NEXT,
    )
    pdf.cell(
        0, 6,
        f"Erreicht: {totals['kcal']:.0f} kcal, {totals['protein_g']:.0f} g Protein, "
        f"{totals['carbs_g']:.0f} g Kohlenhydrate, {totals['fat_g']:.0f} g Fett",
        new_x=XPos.LMARGIN, new_y=YPos.NEXT,
    )
    if not result.success:
        pdf.cell(0, 6, "Hinweis: Solver hat keine optimale Lösung bestätigt.", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "Lebensmittel (g/Tag)", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    headers = ["Lebensmittel", "Basis (g)", "Optimiert (g)", "Änderung (g)"]
    widths = [80, 35, 35, 35]
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(235, 235, 235)
    for h, w in zip(headers, widths):
        pdf.cell(w, 7, h, border=1, fill=True, new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.ln(7)

    pdf.set_font("Helvetica", "", 9)
    for name, base_g, opt_g in zip(FOOD_NAMES, baseline, result.x):
        diff = opt_g - base_g
        row = [name, f"{base_g:.0f}", f"{opt_g:.0f}", f"{diff:+.0f}"]
        for val, w in zip(row, widths):
            pdf.cell(w, 6, val, border=1, new_x=XPos.RIGHT, new_y=YPos.TOP)
        pdf.ln(6)

    return bytes(pdf.output())
