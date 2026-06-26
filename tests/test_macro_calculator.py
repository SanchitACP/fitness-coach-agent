"""Unit tests for the macro calculator skill (Sprint 1a).

Expected TDEE ranges are derived from the actual Mifflin-St Jeor output (verified
by hand), not the product spec's approximate prose figures.
"""

import pytest

from skills.macro_calculator import (
    ACTIVITY_MULTIPLIERS,
    GOAL_CALORIE_ADJUSTMENTS,
    GOAL_MACRO_SPLITS,
    calculate_tdee_and_macros,
)

# A fixed baseline profile reused across parametrized cases so that only the
# variable under test (activity level / goal) changes between assertions.
BASE = dict(weight_lbs=180, height_inches=70, age=25, sex="M")


# --------------------------------------------------------------------------- #
# Core sanity checks
# --------------------------------------------------------------------------- #
def test_tdee_bulk_male():
    """180 lb, 5'10", 25M, moderate -> ~2802 TDEE, target = TDEE + 300."""
    result = calculate_tdee_and_macros(180, 70, 25, "M", "moderate", "bulk")
    assert 2700 < result["tdee"] < 2900
    assert result["target_calories"] == result["tdee"] + 300
    assert result["macro_split"]["protein_g"] > 0


def test_tdee_cut_female():
    """135 lb, 5'5", 28F, light -> ~1847 TDEE, target = TDEE - 300."""
    result = calculate_tdee_and_macros(135, 65, 28, "F", "light", "cut")
    assert 1750 < result["tdee"] < 1950
    assert result["target_calories"] == result["tdee"] - 300


def test_sex_difference():
    """All else equal, the male constant yields a higher BMR/TDEE than female."""
    male = calculate_tdee_and_macros(160, 68, 30, "M", "moderate", "maintain")
    female = calculate_tdee_and_macros(160, 68, 30, "F", "moderate", "maintain")
    assert male["tdee"] > female["tdee"]


# --------------------------------------------------------------------------- #
# Activity level
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("level", list(ACTIVITY_MULTIPLIERS))
def test_each_activity_level_scales_correctly(level):
    """maintain TDEE for each level == sedentary BMR scaled by that multiplier.

    On 'maintain' there is no calorie adjustment, so target_calories == TDEE ==
    BMR * multiplier. Comparing each level back to sedentary isolates the
    multiplier and proves the right factor is applied for every level.
    """
    sedentary = calculate_tdee_and_macros(**BASE, activity_level="sedentary", goal="maintain")
    bmr = sedentary["tdee"] / ACTIVITY_MULTIPLIERS["sedentary"]
    result = calculate_tdee_and_macros(**BASE, activity_level=level, goal="maintain")
    expected_tdee = round(bmr * ACTIVITY_MULTIPLIERS[level])
    # Allow 1 cal of slack: the baseline BMR is recovered from a rounded TDEE.
    assert abs(result["tdee"] - expected_tdee) <= 1


def test_activity_levels_strictly_increasing():
    """More activity must never lower TDEE; the ordering must be strict."""
    order = ["sedentary", "light", "moderate", "active", "very_active"]
    tdees = [
        calculate_tdee_and_macros(**BASE, activity_level=lvl, goal="maintain")["tdee"]
        for lvl in order
    ]
    assert tdees == sorted(tdees)
    assert len(set(tdees)) == len(tdees)  # all distinct


def test_unknown_activity_defaults_to_moderate():
    """An unrecognized activity level falls back to the 'moderate' multiplier."""
    unknown = calculate_tdee_and_macros(**BASE, activity_level="couch_potato", goal="maintain")
    moderate = calculate_tdee_and_macros(**BASE, activity_level="moderate", goal="maintain")
    assert unknown["tdee"] == moderate["tdee"]


def test_activity_level_case_insensitive():
    """Activity level is normalized, so casing must not change the result."""
    upper = calculate_tdee_and_macros(**BASE, activity_level="MODERATE", goal="bulk")
    lower = calculate_tdee_and_macros(**BASE, activity_level="moderate", goal="bulk")
    assert upper == lower


# --------------------------------------------------------------------------- #
# Goal
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("goal,adjustment", GOAL_CALORIE_ADJUSTMENTS.items())
def test_goal_calorie_adjustment(goal, adjustment):
    """Each goal shifts target_calories off TDEE by exactly its adjustment."""
    result = calculate_tdee_and_macros(**BASE, activity_level="moderate", goal=goal)
    assert result["target_calories"] == result["tdee"] + adjustment


@pytest.mark.parametrize("goal", list(GOAL_MACRO_SPLITS))
def test_goal_macro_split_percentages(goal):
    """Grams returned for each goal reconstruct that goal's intended cal split."""
    result = calculate_tdee_and_macros(**BASE, activity_level="moderate", goal=goal)
    s = result["macro_split"]
    cals = {
        "protein": s["protein_g"] * 4,
        "carbs": s["carbs_g"] * 4,
        "fat": s["fat_g"] * 9,
    }
    total = sum(cals.values())
    for macro, expected_fraction in GOAL_MACRO_SPLITS[goal].items():
        assert cals[macro] / total == pytest.approx(expected_fraction, abs=0.02)


def test_unknown_goal_defaults_to_maintain():
    """An unrecognized goal uses maintain's adjustment (0) and maintain's split."""
    unknown = calculate_tdee_and_macros(**BASE, activity_level="moderate", goal="recomp")
    maintain = calculate_tdee_and_macros(**BASE, activity_level="moderate", goal="maintain")
    assert unknown["target_calories"] == unknown["tdee"]  # no adjustment
    assert unknown["macro_split"] == maintain["macro_split"]


def test_goal_case_insensitive():
    """Goal is normalized, so casing must not change the result."""
    upper = calculate_tdee_and_macros(**BASE, activity_level="moderate", goal="BULK")
    lower = calculate_tdee_and_macros(**BASE, activity_level="moderate", goal="bulk")
    assert upper == lower


# --------------------------------------------------------------------------- #
# Macro gram math
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("goal", list(GOAL_MACRO_SPLITS))
def test_macro_grams_reconstruct_target_calories(goal):
    """protein*4 + carbs*4 + fat*9 should sum back to ~target_calories.

    Each macro is rounded to whole grams, so allow a small rounding window.
    """
    result = calculate_tdee_and_macros(**BASE, activity_level="moderate", goal=goal)
    s = result["macro_split"]
    reconstructed = s["protein_g"] * 4 + s["carbs_g"] * 4 + s["fat_g"] * 9
    assert reconstructed == pytest.approx(result["target_calories"], abs=12)


def test_sex_case_insensitive():
    """Sex 'm'/'M' must be treated identically."""
    upper = calculate_tdee_and_macros(180, 70, 25, "M", "moderate", "bulk")
    lower = calculate_tdee_and_macros(180, 70, 25, "m", "moderate", "bulk")
    assert upper == lower
