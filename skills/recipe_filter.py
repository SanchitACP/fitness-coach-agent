"""Recipe Filter skill (ADK FunctionTool).

Sprint 1b. Selects recipes from the curated database that match macro targets and
user preferences, enforces allergy/diet hard-blocks, ensures variety, and builds
a shopping list.

Two rules (see data/README.md):
  1. Never silently violate a hard restriction. Allergen/diet blocks are absolute.
  2. Graceful degradation. If a slot can't be filled or a day can't hit the macro
     tolerance, surface a warning instead of crashing or breaking a restriction.
"""

import json
import os

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "recipes.json")

# Daily macro tolerance for marking a day "on target" (product spec Section 7).
CALORIE_TOLERANCE = 150
PROTEIN_TOLERANCE_G = 20

# A recipe may appear at most this many times across the week (variety rule).
MAX_REPEATS = 2

# Diet labels expand into sets of `restrictions_contains` tags to hard-block.
DIET_BLOCKS = {
    "vegetarian": {"meat", "fish", "shellfish"},
    "vegan": {"meat", "fish", "shellfish", "dairy", "eggs"},
}

# "gluten_free" style restrictions map to the tag actually stored on recipes.
RESTRICTION_ALIASES = {
    "gluten_free": "gluten",
    "dairy_free": "dairy",
    "no_gluten": "gluten",
    "no_dairy": "dairy",
    "nut_free": "tree_nuts",
}

# How daily calories are split across 4 meal slots. The snack acts as the
# balancer (chosen last to close the remaining gap), so its share is a starting
# hint, not a hard target.
SLOT_PLANS = {
    4: [("breakfast", 0.25), ("lunch", 0.30), ("dinner", 0.30), ("snack", 0.15)],
    3: [("breakfast", 0.30), ("lunch", 0.35), ("dinner", 0.35)],
}


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _load_recipes(path: str = _DATA_PATH) -> list:
    with open(path, "r", encoding="utf-8") as fp:
        return json.load(fp)


def _build_block_set(restrictions: list) -> set:
    """Expand user restrictions into a set of recipe tags to hard-block."""
    blocks = set()
    for raw in restrictions or []:
        r = raw.strip().lower()
        if r in DIET_BLOCKS:
            blocks |= DIET_BLOCKS[r]
        else:
            blocks.add(RESTRICTION_ALIASES.get(r, r))
    return blocks


def _is_allowed(recipe: dict, block_set: set) -> bool:
    """True if the recipe violates no hard restriction (allergy/diet safety)."""
    return not (set(recipe.get("restrictions_contains", [])) & block_set)


def _is_disliked(recipe: dict, dislikes: list) -> bool:
    """Soft match: dislike hits the recipe name or any ingredient item."""
    if not dislikes:
        return False
    hay = recipe["name"].lower() + " " + " ".join(
        i["item"].lower() for i in recipe.get("ingredients", [])
    )
    return any(d.strip().lower() in hay for d in dislikes)


def _prefers_cuisine(recipe: dict, cuisines: list) -> bool:
    if not cuisines:
        return False
    want = {c.strip().lower() for c in cuisines}
    return bool({c.lower() for c in recipe.get("cuisines", [])} & want)


def _slot_plan(meals_per_day: int) -> list:
    if meals_per_day in SLOT_PLANS:
        return SLOT_PLANS[meals_per_day]
    # Fallback: even split across the first N standard slots.
    slots = ["breakfast", "lunch", "dinner", "snack"][:meals_per_day]
    frac = 1.0 / max(len(slots), 1)
    return [(s, frac) for s in slots]


def _pick(pool, target_ratio, usage, cuisines, exclude_ids):
    """Pick the best recipe for a slot.

    Calories are corrected later by per-day portion scaling, so selection targets
    the right *protein density* (protein per calorie) instead of a raw calorie
    number — matching each meal's density to the day's target ratio means the day
    lands near both its calorie and protein goals after scaling.

    Preference order (lower score = better):
      1. recipes not already used today, and not yet at the weekly repeat cap,
      2. preferred-cuisine matches,
      3. protein density closest to the target ratio,
      4. least-used so far (spreads variety across the week).
    Returns None if the pool is empty.
    """
    if not pool:
        return None
    # Prefer recipes not used today and under the weekly cap; relax if forced.
    fresh = [
        r for r in pool
        if r["recipe_id"] not in exclude_ids
        and usage.get(r["recipe_id"], 0) < MAX_REPEATS
    ]
    candidates = fresh or [r for r in pool if r["recipe_id"] not in exclude_ids] or pool

    def score(r):
        density = r["calories"] and r["macros"]["protein_g"] / r["calories"]
        density_gap = abs(density - target_ratio) if target_ratio else 0
        return (
            0 if _prefers_cuisine(r, cuisines) else 1,
            density_gap,
            usage.get(r["recipe_id"], 0),
        )

    return min(candidates, key=score)


# Sane bounds for the per-day serving multiplier (avoid absurd portions).
MIN_SCALE, MAX_SCALE = 0.5, 3.0


def _scale_factor(raw_cal: float, target_cal: float) -> float:
    """Serving multiplier to bring a day's raw calories to the target."""
    if not raw_cal or not target_cal:
        return 1.0
    return round(min(max(target_cal / raw_cal, MIN_SCALE), MAX_SCALE), 2)


# --------------------------------------------------------------------------- #
# Shopping list
# --------------------------------------------------------------------------- #
_CATEGORY_RULES = [
    ("pantry", ["oil", "sauce", "honey", "maple", "salsa", "marinara", "hummus",
                "tahini", "seeds", "spice", "dressing", "mayonnaise", "mustard",
                "nutritional yeast", "turmeric", "basil", "cilantro", "garlic",
                "broth", "pesto", "teriyaki", "chili", "almond butter",
                "peanut butter", "soy", "vinegar", "salt", "tzatziki"]),
    ("fruit", ["banana", "berries", "blueberr", "raspberr", "apple", "orange",
               "pineapple", "lime", "lemon", "raisin"]),
    ("dairy", ["milk", "yogurt", "cheese", "mozzarella", "parmesan", "cottage",
               "feta", "cream", "paneer", "butter"]),
    ("grains", ["rice", "oat", "quinoa", "pasta", "bread", "tortilla", "noodle",
                "pita", "crumb", "flour", "rice cakes", "falafel"]),
    ("vegetables", ["broccoli", "spinach", "pepper", "vegetable", "carrot",
                    "cucumber", "lettuce", "tomato", "asparagus", "pea",
                    "onion", "celery", "cabbage", "greens", "mushroom",
                    "potato", "bean", "avocado", "romaine"]),
    ("protein", ["chicken", "beef", "pork", "steak", "turkey", "salmon", "tuna",
                 "shrimp", "cod", "sardine", "tofu", "egg", "ham", "jerky",
                 "whey", "protein", "lentil", "chickpea", "edamame"]),
]


def _categorize(item: str) -> str:
    name = item.lower()
    # Plant milks and nut butters must beat the generic 'milk'/'butter' rules.
    if "soy milk" in name or "coconut milk" in name:
        return "pantry"
    for category, keywords in _CATEGORY_RULES:
        if any(k in name for k in keywords):
            return category
    return "pantry"


def _build_shopping_list(selected: list) -> list:
    """Aggregate ingredients across all selected meals, grouped by category.

    `selected` is a list of (recipe, servings) so ingredient quantities reflect
    the portion scaling applied to each day.
    """
    agg = {}  # (item, unit) -> qty
    for recipe, servings in selected:
        for ing in recipe.get("ingredients", []):
            key = (ing["item"], ing["unit"])
            agg[key] = agg.get(key, 0) + ing["qty"] * servings
    items = [
        {"item": item, "qty": round(qty, 2), "unit": unit, "category": _categorize(item)}
        for (item, unit), qty in agg.items()
    ]
    # Stable, readable order: by category then item.
    items.sort(key=lambda x: (x["category"], x["item"]))
    return items


# --------------------------------------------------------------------------- #
# Public skill
# --------------------------------------------------------------------------- #
def filter_recipes(
    macro_targets: dict,
    cuisines: list,
    restrictions: list,
    dislikes: list,
    prep_time_max: int,
    days: int = 7,
    meals_per_day: int = 4,
    variety: str = "varied",
    recipes: list = None,
) -> dict:
    """Select recipes matching macro targets and preferences.

    Args:
        macro_targets: dict with at least 'calories' and 'protein_g'.
        cuisines: preferred cuisines (soft preference).
        restrictions: hard blocks — allergens ('peanuts') and/or diets
            ('vegetarian', 'vegan', 'gluten_free'). Never violated.
        dislikes: soft avoidances matched against name/ingredients.
        prep_time_max: max prep minutes per recipe.
        days: number of days to plan (default 7).
        meals_per_day: meals per day (default 4: breakfast/lunch/dinner/snack).
        variety: 'varied' (default) rotates meals and avoids repeating a recipe on
            back-to-back days; 'simple' is meal-prep style — one recipe per slot
            reused every day. This is a user preference, so the agent should ask.
        recipes: optional pre-loaded recipe list (mainly for tests).

    Returns:
        Dict with 'macro_targets', 'days' (each with meals + day_totals +
        on_target), 'shopping_list', and 'warnings' (graceful-degradation notes).
    """
    if recipes is None:
        recipes = _load_recipes()

    target_cal = macro_targets.get("calories", 0)
    target_protein = macro_targets.get("protein_g", 0)

    block_set = _build_block_set(restrictions)

    # Hard filter (safety) + prep time. This pool can never violate a restriction.
    safe = [
        r for r in recipes
        if _is_allowed(r, block_set) and r.get("prep_time_min", 0) <= prep_time_max
    ]
    # Soft filter (dislikes), applied per-slot below so we can relax it if a slot
    # would otherwise starve.
    plan = _slot_plan(meals_per_day)
    warnings = []

    # Target protein-per-calorie ratio drives selection (see _pick).
    target_ratio = (target_protein / target_cal) if target_cal else 0

    # Pre-compute per-slot candidate pools (safe set, split by meal slot).
    def slot_pool(slot, drop_dislikes):
        pool = [r for r in safe if slot in r.get("meal_types", [])]
        if drop_dislikes:
            kept = [r for r in pool if not _is_disliked(r, dislikes)]
            return kept if kept else pool  # relax dislikes rather than starve
        return pool

    usage = {}
    selected = []  # list of (recipe, servings) for the shopping list
    out_days = []
    prev_ids = set()  # recipes used on the previous day (varied mode)
    simple = (variety or "varied").strip().lower() == "simple"

    # Meal-prep mode: choose one recipe per slot once, then reuse it every day.
    fixed_picks = None
    if simple:
        fixed_picks = []
        day_used = set()
        for slot, _frac in plan:
            pool = slot_pool(slot, drop_dislikes=True)
            choice = _pick(pool, target_ratio, usage, cuisines, day_used)
            if choice is None:
                warnings.append(f"No recipe available for '{slot}' within the "
                                f"given constraints.")
                continue
            day_used.add(choice["recipe_id"])
            fixed_picks.append((slot, choice))

    for day in range(1, days + 1):
        if simple:
            picks = list(fixed_picks)  # same meals every day, by design
        else:
            picks = []  # (slot, recipe) chosen this day, before scaling
            day_used = set()
            for slot, _frac in plan:
                pool = slot_pool(slot, drop_dislikes=True)
                # Avoid repeating a recipe within the day and (softly) on
                # back-to-back days, so the week rotates instead of pairing up.
                choice = _pick(pool, target_ratio, usage, cuisines,
                               day_used | prev_ids)
                if choice is None:
                    warnings.append(f"Day {day}: no recipe available for "
                                    f"'{slot}' within the given constraints.")
                    continue
                usage[choice["recipe_id"]] = usage.get(choice["recipe_id"], 0) + 1
                day_used.add(choice["recipe_id"])
                picks.append((slot, choice))
            prev_ids = day_used

        # Portion-scale the whole day to hit the calorie target.
        raw_cal = sum(r["calories"] for _, r in picks)
        servings = _scale_factor(raw_cal, target_cal)

        meals = []
        for slot, r in picks:
            sm = {k: round(v * servings) for k, v in r["macros"].items()}
            meals.append({
                "slot": slot,
                "recipe_id": r["recipe_id"],
                "name": r["name"],
                "servings": servings,
                "macros": sm,
                "calories": round(r["calories"] * servings),
            })
            selected.append((r, servings))

        totals = {
            "calories": sum(m["calories"] for m in meals),
            "protein_g": sum(m["macros"]["protein_g"] for m in meals),
            "carbs_g": sum(m["macros"]["carbs_g"] for m in meals),
            "fat_g": sum(m["macros"]["fat_g"] for m in meals),
        }
        on_target = (
            abs(totals["calories"] - target_cal) <= CALORIE_TOLERANCE
            and abs(totals["protein_g"] - target_protein) <= PROTEIN_TOLERANCE_G
        )
        if not on_target and meals:
            warnings.append(
                f"Day {day}: totals {totals['calories']} cal / "
                f"{totals['protein_g']}g protein outside tolerance of "
                f"{target_cal} cal / {target_protein}g."
            )
        out_days.append({
            "day": day,
            "meals": meals,
            "day_totals": totals,
            "on_target": on_target,
        })

    return {
        "macro_targets": macro_targets,
        "days": out_days,
        "shopping_list": _build_shopping_list(selected),
        "warnings": warnings,
    }
