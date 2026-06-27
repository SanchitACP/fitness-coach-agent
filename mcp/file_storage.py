"""File Storage MCP (core, Phase 1).

Sprint 1b. Saves generated plans locally as JSON and CSV. Never sends data to
external services — the user owns their data (Concierge-track privacy).
"""

import json
import os
from datetime import datetime

import pandas as pd

from utils.validators import sanitize_filename

DEFAULT_DIR = "plans"


def save_plan(plan: dict, formats: list = ["json", "csv"], out_dir: str = DEFAULT_DIR) -> dict:
    """Save a meal plan to the local plans/ directory.

    The plan_id is sanitized before use in a file path to prevent path traversal
    (security requirement). Writes JSON (full plan) and/or CSV (flat meal table).

    Args:
        plan: a plan dict (as produced by the recipe filter, optionally with a
            'plan_id'). If no plan_id is present, a timestamped one is generated.
        formats: any of "json", "csv".
        out_dir: directory to write into (default "plans"; never a remote target).

    Returns:
        {"saved": bool, "plan_id": str, "paths": {format: path}}.
    """
    raw_id = plan.get("plan_id") or f"plan_{datetime.now():%Y%m%d_%H%M%S}"
    plan_id = sanitize_filename(raw_id) or "plan"  # never empty after sanitizing

    os.makedirs(out_dir, exist_ok=True)
    paths = {}

    if "json" in formats:
        path = os.path.join(out_dir, f"{plan_id}.json")
        with open(path, "w", encoding="utf-8") as fp:
            json.dump(plan, fp, indent=2)
        paths["json"] = path

    if "csv" in formats:
        rows = _flatten_meals(plan)
        path = os.path.join(out_dir, f"{plan_id}.csv")
        # pandas keeps the CSV spreadsheet-friendly and matches the documented
        # tech stack; an empty plan still writes a header-only file.
        pd.DataFrame(rows, columns=_CSV_COLUMNS).to_csv(path, index=False)
        paths["csv"] = path

    return {"saved": bool(paths), "plan_id": plan_id, "paths": paths}


_CSV_COLUMNS = ["Day", "Slot", "Recipe", "Servings",
                "Protein (g)", "Carbs (g)", "Fat (g)", "Calories"]


def _flatten_meals(plan: dict) -> list:
    """Flatten the plan's nested days/meals into one row per meal for CSV."""
    rows = []
    for day in plan.get("days", []):
        for meal in day.get("meals", []):
            macros = meal.get("macros", {})
            rows.append({
                "Day": day.get("day"),
                "Slot": meal.get("slot"),
                "Recipe": meal.get("name"),
                "Servings": meal.get("servings", 1),
                "Protein (g)": macros.get("protein_g"),
                "Carbs (g)": macros.get("carbs_g"),
                "Fat (g)": macros.get("fat_g"),
                "Calories": meal.get("calories"),
            })
    return rows
