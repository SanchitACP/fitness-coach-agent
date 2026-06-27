"""Sprint 1d wiring tests — everything that doesn't need a live LLM call.

The actual conversation needs ANTHROPIC_API_KEY and is verified manually; these
guard the agent definition, the security key-check, and the CLI helpers.
"""

import pytest

import main
from agent import root_agent
from google.adk.models.lite_llm import LiteLlm
from utils.formatters import format_plan_for_cli


# --------------------------------------------------------------------------- #
# Agent definition
# --------------------------------------------------------------------------- #
def test_agent_has_three_skills():
    assert root_agent.name == "fitness_coach"
    assert isinstance(root_agent.model, LiteLlm)
    assert [t.name for t in root_agent.tools] == [
        "calculate_tdee_and_macros", "filter_recipes", "get_workout_template",
    ]


def test_instruction_mentions_variety_question():
    """The agent must ask about variety rather than assume it (design decision)."""
    assert "variety" in root_agent.instruction.lower()


# --------------------------------------------------------------------------- #
# Security layer
# --------------------------------------------------------------------------- #
def test_require_api_key_raises_when_missing(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr(main, "load_dotenv", lambda *a, **k: None)  # ignore .env
    with pytest.raises(EnvironmentError):
        main.require_api_key()


def test_require_api_key_returns_key(monkeypatch):
    monkeypatch.setattr(main, "load_dotenv", lambda *a, **k: None)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    assert main.require_api_key() == "sk-test"


def test_clear_session_empties_store():
    main._session_store["x"] = 1
    main._clear_session()
    assert main._session_store == {}


# --------------------------------------------------------------------------- #
# CLI helpers
# --------------------------------------------------------------------------- #
class _FakeFnResp:
    def __init__(self, name, response):
        self.name = name
        self.response = response


class _FakeEvent:
    def __init__(self, fn_responses):
        self._fn = fn_responses

    def get_function_responses(self):
        return self._fn


def test_extract_plan_finds_filter_output():
    plan = {"days": [], "shopping_list": []}
    event = _FakeEvent([_FakeFnResp("filter_recipes", plan)])
    assert main._extract_plan(event) is plan


def test_extract_plan_unwraps_result_key():
    plan = {"days": [], "shopping_list": []}
    event = _FakeEvent([_FakeFnResp("filter_recipes", {"result": plan})])
    assert main._extract_plan(event) == plan


def test_extract_plan_ignores_other_tools():
    event = _FakeEvent([_FakeFnResp("calculate_tdee_and_macros", {"tdee": 2000})])
    assert main._extract_plan(event) is None


# --------------------------------------------------------------------------- #
# Formatter
# --------------------------------------------------------------------------- #
def test_format_plan_for_cli_renders_sections():
    plan = {
        "macro_targets": {"calories": 2880, "protein_g": 180},
        "days": [{
            "day": 1,
            "meals": [{"slot": "breakfast", "name": "Oats", "servings": 1.5,
                       "macros": {"protein_g": 54, "carbs_g": 102, "fat_g": 15},
                       "calories": 759}],
            "day_totals": {"calories": 759, "protein_g": 54, "carbs_g": 102, "fat_g": 15},
            "on_target": False,
        }],
        "shopping_list": [{"item": "oats", "qty": 90, "unit": "g", "category": "grains"}],
    }
    out = format_plan_for_cli(plan)
    assert "Daily target" in out
    assert "Day 1" in out and "Oats" in out
    assert "Shopping list" in out and "grains" in out
