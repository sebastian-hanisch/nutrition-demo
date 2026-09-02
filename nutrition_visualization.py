"""Plotly-Visualisierungen für die Ernährungsoptimierung-Demo."""

import plotly.graph_objects as go

from nutrition_constants import FOOD_NAMES


def diet_comparison_figure(baseline, optimized, title):
    order = sorted(range(len(FOOD_NAMES)), key=lambda i: -max(baseline[i], optimized[i]))
    names = [FOOD_NAMES[i] for i in order]
    base_sorted = [baseline[i] for i in order]
    opt_sorted = [optimized[i] for i in order]

    fig = go.Figure()
    fig.add_bar(name="Basis-Ernährung", x=names, y=base_sorted, marker_color="#94a3b8")
    fig.add_bar(name="Optimiert", x=names, y=opt_sorted, marker_color="#2563eb")
    fig.update_layout(
        title=title, barmode="group", yaxis_title="g/Tag",
        xaxis_tickangle=-45, legend=dict(orientation="h", y=1.1), height=450,
        margin=dict(t=80),
    )
    return fig


def macro_figure(targets, totals_by_label):
    labels = list(totals_by_label.keys())
    fig = go.Figure()
    for macro, target_value in [("Protein (g)", targets.protein_g), ("Kohlenhydrate (g)", targets.carbs_g), ("Fett (g)", targets.fat_g)]:
        key = {"Protein (g)": "protein_g", "Kohlenhydrate (g)": "carbs_g", "Fett (g)": "fat_g"}[macro]
        fig.add_bar(name=macro, x=labels, y=[totals_by_label[l][key] for l in labels])
    fig.add_hline(y=targets.protein_g, line_dash="dot", line_color="gray", annotation_text="Protein-Ziel")
    fig.update_layout(
        title="Makronährstoffe je Zielfunktion (g/Tag)", barmode="group",
        yaxis_title="g/Tag", legend=dict(orientation="h", y=1.15), height=400,
    )
    return fig


def sparsity_figure(comparison_rows):
    labels = [r["Zielfunktion"] for r in comparison_rows]
    unchanged = [r["Unverändert"] for r in comparison_rows]
    n_foods = len(FOOD_NAMES)
    fig = go.Figure()
    fig.add_bar(
        x=labels, y=unchanged, marker_color=["#2563eb", "#2563eb", "#dc2626", "#dc2626"],
        text=[f"{u}/{n_foods}" for u in unchanged], textposition="outside",
    )
    fig.update_layout(
        title="Unveränderte Lebensmittel je Zielfunktionstyp", yaxis_title="Anzahl unverändert",
        yaxis_range=[0, n_foods * 1.15], height=380,
    )
    return fig
