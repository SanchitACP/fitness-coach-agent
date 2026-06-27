"""Unit tests for the workout template selector skill (Sprint 1c)."""

import glob
import json
import os

import pytest

from skills.workout_selector import get_workout_template

_TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "templates")
_TEMPLATE_FILES = sorted(glob.glob(os.path.join(_TEMPLATE_DIR, "*.json")))


# --------------------------------------------------------------------------- #
# Auto-selection by days/week
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("days,expected", [
    (3, "fullbody_3day"),
    (4, "upper_lower_4day"),
    (5, "upper_lower_5day"),
    (6, "ppl_6day"),
])
def test_auto_selection_by_days(days, expected):
    t = get_workout_template("intermediate", days)
    assert t["template_id"] == expected
    assert t["days_per_week"] == days


@pytest.mark.parametrize("days,expected", [
    (1, "fullbody_3day"),
    (2, "fullbody_3day"),
    (7, "ppl_6day"),
])
def test_out_of_range_days_clamp(days, expected):
    assert get_workout_template("beginner", days)["template_id"] == expected


# --------------------------------------------------------------------------- #
# split_preference handling
# --------------------------------------------------------------------------- #
def test_split_preference_honored_when_compatible():
    t = get_workout_template("advanced", 6, split_preference="ppl")
    assert t["template_id"] == "ppl_6day"


@pytest.mark.parametrize("days,expected", [
    (4, "upper_lower_4day"),
    (5, "upper_lower_5day"),
])
def test_upper_lower_resolves_to_day_variant(days, expected):
    t = get_workout_template("intermediate", days, split_preference="upper_lower")
    assert t["template_id"] == expected


def test_incompatible_split_falls_back_to_auto():
    # PPL needs 6 days; with 4 days it should fall back to the 4-day template.
    t = get_workout_template("intermediate", 4, split_preference="ppl")
    assert t["template_id"] == "upper_lower_4day"
    assert "auto-selected" in t["selection_note"].lower()


def test_unknown_split_falls_back():
    t = get_workout_template("beginner", 3, split_preference="bro_split")
    assert t["template_id"] == "fullbody_3day"
    assert "unknown split" in t["selection_note"].lower()


def test_annotations_present():
    t = get_workout_template("beginner", 3)
    assert t["selected_for"]["days_per_week"] == 3
    assert t["selection_note"]


# --------------------------------------------------------------------------- #
# Template data integrity
# --------------------------------------------------------------------------- #
def test_all_four_templates_exist():
    ids = {json.load(open(f, encoding="utf-8"))["template_id"] for f in _TEMPLATE_FILES}
    assert ids == {"fullbody_3day", "upper_lower_4day", "upper_lower_5day", "ppl_6day"}


@pytest.mark.parametrize("path", _TEMPLATE_FILES)
def test_template_structure(path):
    t = json.load(open(path, encoding="utf-8"))
    assert t["experience_levels"]
    # one workout per training day
    assert len(t["days"]) == t["days_per_week"]
    for day in t["days"]:
        assert day["name"] and day["exercises"]
        for ex in day["exercises"]:
            assert ex["name"]
            assert isinstance(ex["sets"], int) and ex["sets"] > 0
            assert ex["reps"]
