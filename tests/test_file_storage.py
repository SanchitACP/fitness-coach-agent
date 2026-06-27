"""Unit tests for the File Storage MCP (Sprint 1b)."""

import csv
import json
import os

from mcp.file_storage import save_plan

SAMPLE_PLAN = {
    "plan_id": "plan_test_001",
    "macro_targets": {"calories": 2880, "protein_g": 180},
    "days": [
        {
            "day": 1,
            "meals": [
                {"slot": "breakfast", "recipe_id": "oats_whey_banana",
                 "name": "Oats + Whey + Banana", "servings": 1.5,
                 "macros": {"protein_g": 54, "carbs_g": 102, "fat_g": 15}, "calories": 759},
                {"slot": "lunch", "recipe_id": "grilled_chicken_rice",
                 "name": "Grilled Chicken & Rice", "servings": 1.5,
                 "macros": {"protein_g": 60, "carbs_g": 75, "fat_g": 12}, "calories": 648},
            ],
            "day_totals": {"calories": 1407, "protein_g": 114, "carbs_g": 177, "fat_g": 27},
            "on_target": False,
        }
    ],
    "shopping_list": [{"item": "oats", "qty": 90, "unit": "g", "category": "grains"}],
}


def test_writes_json_and_csv(tmp_path):
    res = save_plan(SAMPLE_PLAN, out_dir=str(tmp_path))
    assert res["saved"] is True
    assert set(res["paths"]) == {"json", "csv"}
    for p in res["paths"].values():
        assert os.path.exists(p)


def test_json_roundtrips(tmp_path):
    res = save_plan(SAMPLE_PLAN, formats=["json"], out_dir=str(tmp_path))
    with open(res["paths"]["json"], encoding="utf-8") as fp:
        loaded = json.load(fp)
    assert loaded == SAMPLE_PLAN


def test_csv_has_row_per_meal(tmp_path):
    res = save_plan(SAMPLE_PLAN, formats=["csv"], out_dir=str(tmp_path))
    with open(res["paths"]["csv"], newline="", encoding="utf-8") as fp:
        rows = list(csv.DictReader(fp))
    assert len(rows) == 2  # two meals in the sample
    assert rows[0]["Recipe"] == "Oats + Whey + Banana"
    assert rows[0]["Calories"] == "759"
    assert "Servings" in rows[0]


def test_format_subset(tmp_path):
    res = save_plan(SAMPLE_PLAN, formats=["json"], out_dir=str(tmp_path))
    assert set(res["paths"]) == {"json"}


def test_path_traversal_is_neutralized(tmp_path):
    """A malicious plan_id must not escape the output directory."""
    evil = dict(SAMPLE_PLAN, plan_id="../../etc/passwd")
    res = save_plan(evil, formats=["json"], out_dir=str(tmp_path))
    written = res["paths"]["json"]
    # The file must live inside out_dir, and no parent-traversal path exists.
    assert os.path.dirname(os.path.abspath(written)) == os.path.abspath(str(tmp_path))
    assert ".." not in res["plan_id"] and "/" not in res["plan_id"]
    assert not os.path.exists(os.path.join(str(tmp_path), "..", "..", "etc", "passwd"))


def test_missing_plan_id_gets_generated(tmp_path):
    plan = {k: v for k, v in SAMPLE_PLAN.items() if k != "plan_id"}
    res = save_plan(plan, formats=["json"], out_dir=str(tmp_path))
    assert res["plan_id"]  # a timestamped id was created
    assert os.path.exists(res["paths"]["json"])
