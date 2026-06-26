"""Unit tests for the macro calculator skill (Sprint 1a).

Expected TDEE ranges are derived from the actual Mifflin-St Jeor output (verified
by hand), not the product spec's approximate prose figures.
"""

from skills.macro_calculator import calculate_tdee_and_macros


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


def test_macro_protein_pct_bulk():
    """Bulk split should put ~30% of calories into protein (+/-3% for rounding)."""
    result = calculate_tdee_and_macros(180, 70, 25, "M", "moderate", "bulk")
    s = result["macro_split"]
    total_cals = s["protein_g"] * 4 + s["carbs_g"] * 4 + s["fat_g"] * 9
    protein_pct = (s["protein_g"] * 4) / total_cals
    assert 0.27 < protein_pct < 0.33


def test_sex_difference():
    """All else equal, the male constant yields a higher BMR/TDEE than female."""
    male = calculate_tdee_and_macros(160, 68, 30, "M", "moderate", "maintain")
    female = calculate_tdee_and_macros(160, 68, 30, "F", "moderate", "maintain")
    assert male["tdee"] > female["tdee"]


def test_goal_adjustments():
    """Bulk adds 300, cut subtracts 300, maintain matches TDEE exactly."""
    args = (170, 69, 27, "M", "active")
    bulk = calculate_tdee_and_macros(*args, "bulk")
    cut = calculate_tdee_and_macros(*args, "cut")
    maintain = calculate_tdee_and_macros(*args, "maintain")
    assert bulk["target_calories"] == bulk["tdee"] + 300
    assert cut["target_calories"] == cut["tdee"] - 300
    assert maintain["target_calories"] == maintain["tdee"]
