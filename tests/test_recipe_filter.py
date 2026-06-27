"""Unit tests for the recipe filter skill (Sprint 1b).

These run against the real data/recipes.json so they also guard the database's
coverage (e.g. that a vegan plan can actually be built).
"""

import json
import os
from collections import Counter

import pytest

from skills.recipe_filter import filter_recipes

_RECIPES = {
    r["recipe_id"]: r
    for r in json.load(open(
        os.path.join(os.path.dirname(__file__), "..", "data", "recipes.json"),
        encoding="utf-8",
    ))
}


def _all_meals(result):
    return [m for d in result["days"] for m in d["meals"]]


def _contains(meal, tags):
    return set(_RECIPES[meal["recipe_id"]]["restrictions_contains"]) & set(tags)


# --------------------------------------------------------------------------- #
# Structure
# --------------------------------------------------------------------------- #
def test_returns_seven_days_four_meals():
    res = filter_recipes(
        macro_targets={"calories": 2200, "protein_g": 150},
        cuisines=[], restrictions=[], dislikes=[], prep_time_max=60,
    )
    assert len(res["days"]) == 7
    for day in res["days"]:
        assert len(day["meals"]) == 4
        assert {m["slot"] for m in day["meals"]} == {"breakfast", "lunch", "dinner", "snack"}


def test_custom_days_and_meals():
    res = filter_recipes(
        macro_targets={"calories": 1800, "protein_g": 120},
        cuisines=[], restrictions=[], dislikes=[], prep_time_max=60,
        days=3, meals_per_day=3,
    )
    assert len(res["days"]) == 3
    assert all(len(d["meals"]) == 3 for d in res["days"])


# --------------------------------------------------------------------------- #
# Hard restrictions (safety) — these must NEVER be violated
# --------------------------------------------------------------------------- #
def test_respects_peanut_restriction():
    """Spec test: no peanut-containing recipe when peanuts are restricted."""
    res = filter_recipes(
        macro_targets={"calories": 2800, "protein_g": 180},
        cuisines=["Italian", "Asian"], restrictions=["peanuts"],
        dislikes=[], prep_time_max=60,
    )
    assert all(not _contains(m, ["peanuts"]) for m in _all_meals(res))


def test_vegetarian_has_no_meat():
    res = filter_recipes(
        macro_targets={"calories": 2000, "protein_g": 120},
        cuisines=[], restrictions=["vegetarian"], dislikes=[], prep_time_max=60,
    )
    assert all(not _contains(m, ["meat", "fish", "shellfish"]) for m in _all_meals(res))


def test_vegan_has_no_animal_products():
    res = filter_recipes(
        macro_targets={"calories": 2000, "protein_g": 110},
        cuisines=[], restrictions=["vegan"], dislikes=[], prep_time_max=60,
    )
    meals = _all_meals(res)
    assert meals  # a vegan plan is actually buildable from the DB
    assert all(not _contains(m, ["meat", "fish", "shellfish", "dairy", "eggs"]) for m in meals)


def test_gluten_free_alias():
    res = filter_recipes(
        macro_targets={"calories": 2000, "protein_g": 130},
        cuisines=[], restrictions=["gluten_free"], dislikes=[], prep_time_max=60,
    )
    assert all(not _contains(m, ["gluten"]) for m in _all_meals(res))


def test_prep_time_respected():
    res = filter_recipes(
        macro_targets={"calories": 2000, "protein_g": 120},
        cuisines=[], restrictions=[], dislikes=[], prep_time_max=20,
    )
    assert all(_RECIPES[m["recipe_id"]]["prep_time_min"] <= 20 for m in _all_meals(res))


# --------------------------------------------------------------------------- #
# Variety
# --------------------------------------------------------------------------- #
def test_no_recipe_repeats_more_than_twice():
    res = filter_recipes(
        macro_targets={"calories": 2800, "protein_g": 180},
        cuisines=[], restrictions=[], dislikes=[], prep_time_max=60,
    )
    counts = Counter(m["recipe_id"] for m in _all_meals(res))
    assert all(c <= 2 for c in counts.values()), counts


def test_no_same_day_repeats():
    res = filter_recipes(
        macro_targets={"calories": 2200, "protein_g": 150},
        cuisines=[], restrictions=[], dislikes=[], prep_time_max=60,
    )
    for day in res["days"]:
        ids = [m["recipe_id"] for m in day["meals"]]
        assert len(ids) == len(set(ids)), f"day {day['day']} has a repeat"


def test_varied_mode_avoids_back_to_back_identical_days():
    """Default 'varied' must not repeat the same recipe on consecutive days."""
    res = filter_recipes(
        macro_targets={"calories": 2880, "protein_g": 180},
        cuisines=[], restrictions=[], dislikes=[], prep_time_max=60,
    )
    sigs = [tuple(m["recipe_id"] for m in d["meals"]) for d in res["days"]]
    for i in range(len(sigs) - 1):
        # no recipe shared between adjacent days (true rotation)
        assert not (set(sigs[i]) & set(sigs[i + 1])), f"days {i+1}/{i+2} overlap"


def test_simple_mode_repeats_same_recipe_per_slot():
    """Meal-prep 'simple' reuses one recipe per slot every day."""
    res = filter_recipes(
        macro_targets={"calories": 2880, "protein_g": 180},
        cuisines=[], restrictions=[], dislikes=[], prep_time_max=60,
        variety="simple",
    )
    by_slot = {}
    for day in res["days"]:
        for meal in day["meals"]:
            by_slot.setdefault(meal["slot"], set()).add(meal["recipe_id"])
    assert all(len(ids) == 1 for ids in by_slot.values()), by_slot


# --------------------------------------------------------------------------- #
# Macro targeting (portion scaling)
# --------------------------------------------------------------------------- #
def test_achievable_target_hits_calories_and_protein():
    """A realistic bulk target should land within tolerance on every day."""
    res = filter_recipes(
        macro_targets={"calories": 2880, "protein_g": 180},
        cuisines=["Italian", "Asian"], restrictions=["peanuts"],
        dislikes=["mushrooms"], prep_time_max=35,
    )
    for day in res["days"]:
        t = day["day_totals"]
        assert abs(t["calories"] - 2880) <= 150, t
        assert abs(t["protein_g"] - 180) <= 20, t
        assert day["on_target"]
    assert res["warnings"] == []


# --------------------------------------------------------------------------- #
# Dislikes (soft preference)
# --------------------------------------------------------------------------- #
def test_dislikes_avoided_when_pool_allows():
    res = filter_recipes(
        macro_targets={"calories": 2400, "protein_g": 160},
        cuisines=[], restrictions=[], dislikes=["chicken"], prep_time_max=60,
    )
    assert all("chicken" not in m["name"].lower() for m in _all_meals(res))


# --------------------------------------------------------------------------- #
# Shopping list
# --------------------------------------------------------------------------- #
def test_shopping_list_well_formed():
    res = filter_recipes(
        macro_targets={"calories": 2400, "protein_g": 160},
        cuisines=[], restrictions=[], dislikes=[], prep_time_max=60,
    )
    sl = res["shopping_list"]
    assert sl
    valid = {"protein", "grains", "vegetables", "fruit", "dairy", "pantry"}
    for item in sl:
        assert set(item) >= {"item", "qty", "unit", "category"}
        assert item["qty"] > 0
        assert item["category"] in valid


# --------------------------------------------------------------------------- #
# Graceful degradation
# --------------------------------------------------------------------------- #
def test_impossible_target_degrades_without_crashing_or_violating():
    """Absurd target on a tight diet: no crash, warnings raised, diet intact."""
    res = filter_recipes(
        macro_targets={"calories": 1200, "protein_g": 200},  # not achievable
        cuisines=[], restrictions=["vegan"], dislikes=[], prep_time_max=60,
    )
    assert isinstance(res["days"], list) and len(res["days"]) == 7
    assert res["warnings"]  # it tells the user it couldn't hit the target
    # Safety still absolute despite degradation:
    assert all(
        not _contains(m, ["meat", "fish", "shellfish", "dairy", "eggs"])
        for m in _all_meals(res)
    )
