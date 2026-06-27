"""Workout Template Selector skill (ADK FunctionTool).

Sprint 1c. Returns a pre-built workout template matching the user's experience
level and weekly availability, loading from data/templates/.
"""

import json
import os

_TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "templates")

# Maps a training-days count to the default template id (auto selection).
_AUTO_BY_DAYS = {
    3: "fullbody_3day",
    4: "upper_lower_4day",
    5: "upper_lower_5day",
    6: "ppl_6day",
}

# Maps a split_preference keyword to the template id it should resolve to.
_SPLIT_ALIASES = {
    "full_body": "fullbody_3day",
    "fullbody": "fullbody_3day",
    "upper_lower": "upper_lower_5day",  # refined to the day-correct variant below
    "ul": "upper_lower_5day",
    "ppl": "ppl_6day",
    "push_pull_legs": "ppl_6day",
}


def _load_template(template_id: str) -> dict:
    path = os.path.join(_TEMPLATE_DIR, f"{template_id}.json")
    with open(path, "r", encoding="utf-8") as fp:
        return json.load(fp)


def _auto_template_id(days_per_week: int) -> str:
    """Pick the best default template id for a given number of training days."""
    if days_per_week <= 3:
        return "fullbody_3day"
    if days_per_week >= 6:
        return "ppl_6day"
    return _AUTO_BY_DAYS[days_per_week]  # 4 or 5


def get_workout_template(
    experience_level: str,
    days_per_week: int,
    split_preference: str = "auto",
) -> dict:
    """Return a workout template matching experience and availability.

    Auto-selection by days_per_week: 3 -> Full Body, 4 -> Upper/Lower (4-day),
    5 -> Upper/Lower (5-day), 6 -> PPL. Counts below 3 / above 6 clamp to the
    nearest sensible template.

    If split_preference names a split (e.g. 'upper_lower', 'ppl'), it is honored
    when compatible with days_per_week; otherwise the function falls back to
    auto-selection and records why in 'selection_note'.

    Returns:
        The full template dict, annotated with 'selected_for' (the inputs) and
        'selection_note'.
    """
    pref = (split_preference or "auto").strip().lower()
    note = None

    if pref in ("auto", ""):
        template_id = _auto_template_id(days_per_week)
        note = f"Auto-selected for {days_per_week} training days/week."
    else:
        requested = _SPLIT_ALIASES.get(pref)
        if requested is None:
            template_id = _auto_template_id(days_per_week)
            note = (f"Unknown split '{split_preference}'; auto-selected for "
                    f"{days_per_week} days/week instead.")
        else:
            # Resolve upper/lower to the variant that matches the day count.
            if requested.startswith("upper_lower"):
                requested = "upper_lower_4day" if days_per_week <= 4 else "upper_lower_5day"
            candidate = _load_template(requested)
            if candidate["days_per_week"] == days_per_week:
                template = candidate
                template["selected_for"] = {
                    "experience_level": experience_level,
                    "days_per_week": days_per_week,
                    "split_preference": split_preference,
                }
                template["selection_note"] = f"Using requested split '{pref}'."
                return template
            template_id = _auto_template_id(days_per_week)
            note = (f"Requested split '{pref}' needs "
                    f"{candidate['days_per_week']} days/week but you have "
                    f"{days_per_week}; auto-selected a compatible template.")

    template = _load_template(template_id)
    template["selected_for"] = {
        "experience_level": experience_level,
        "days_per_week": days_per_week,
        "split_preference": split_preference,
    }
    template["selection_note"] = note
    return template
