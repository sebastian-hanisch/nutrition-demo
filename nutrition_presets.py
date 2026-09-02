"""Ein-Klick-Beispielszenarien und Permalink-Logik - dasselbe SETTING_SPECS-Muster
wie in den anderen Demos dieses Workspace (z. B. shift_presets.py)."""

import math
import random
from dataclasses import dataclass
from typing import Callable, Optional

import streamlit as st

from nutrition_constants import GOAL_PRESETS, OBJECTIVE_TYPES

GOAL_PRESET_NAMES = list(GOAL_PRESETS.keys())
OBJECTIVE_LABELS = list(OBJECTIVE_TYPES.keys())


@dataclass(frozen=True)
class SettingSpec:
    url_param: str
    caster: Callable
    default: object
    lo: Optional[float] = None
    hi: Optional[float] = None


def _parse_goal(v):
    return v if v in GOAL_PRESET_NAMES else GOAL_PRESET_NAMES[1]


def _parse_objective(v):
    return v if v in OBJECTIVE_LABELS else OBJECTIVE_LABELS[0]


SETTING_SPECS = {
    "goal_select": SettingSpec("goal", _parse_goal, GOAL_PRESET_NAMES[1]),
    "bodyweight_slider": SettingSpec("kg", float, 80.0, 40.0, 150.0),
    "variation_slider": SettingSpec("var", float, 0.2, 0.0, 0.5),
    "seed_input": SettingSpec("seed", int, 42, 0, 2_000_000_000),
    "objective_select": SettingSpec("obj", _parse_objective, OBJECTIVE_LABELS[0]),
}


def bounds(state_key):
    spec = SETTING_SPECS[state_key]
    return spec.lo, spec.hi


def apply_preset(goal, bodyweight, variation, seed):
    st.session_state["goal_select"] = goal
    st.session_state["bodyweight_slider"] = bodyweight
    st.session_state["variation_slider"] = variation
    st.session_state["seed_input"] = seed


def randomize_seed():
    st.session_state["seed_input"] = random.randint(0, 2_000_000_000)


def load_permalink_settings():
    if "permalink_loaded" in st.session_state:
        return
    qp = st.query_params
    for state_key, spec in SETTING_SPECS.items():
        if spec.url_param in qp:
            try:
                value = spec.caster(qp[spec.url_param])
                if isinstance(value, float) and not math.isfinite(value):
                    continue
                if not isinstance(value, str):
                    if spec.lo is not None:
                        value = max(spec.lo, value)
                    if spec.hi is not None:
                        value = min(spec.hi, value)
                st.session_state[state_key] = value
            except (ValueError, TypeError):
                pass
    st.session_state["permalink_loaded"] = True


def init_session_state_defaults():
    for state_key, spec in SETTING_SPECS.items():
        if state_key not in st.session_state:
            st.session_state[state_key] = spec.default


def sync_query_params(goal, bodyweight, variation, seed, objective):
    try:
        st.query_params["goal"] = goal
        st.query_params["kg"] = str(bodyweight)
        st.query_params["var"] = str(variation)
        st.query_params["seed"] = str(int(seed))
        st.query_params["obj"] = objective
    except Exception:
        pass
