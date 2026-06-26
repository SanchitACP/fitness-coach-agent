"""Macro Calculator skill (ADK FunctionTool).

Sprint 1a. Computes TDEE and daily macro targets using the Mifflin-St Jeor
equation. Registered with the ADK agent so it can be called dynamically on the
body stats the agent extracts from conversation.
"""


def calculate_tdee_and_macros(
    weight_lbs: float,
    height_inches: float,
    age: int,
    sex: str,
    activity_level: str,
    goal: str,
) -> dict:
    """Calculate TDEE and daily macro targets using Mifflin-St Jeor.

    Args:
        weight_lbs: Body weight in pounds.
        height_inches: Height in inches.
        age: Age in years.
        sex: 'M' or 'F'.
        activity_level: 'sedentary' | 'light' | 'moderate' | 'active' | 'very_active'.
        goal: 'bulk' | 'cut' | 'maintain'.

    Returns:
        Dict with tdee, target_calories, and macro_split (protein_g, carbs_g, fat_g).
    """
    raise NotImplementedError("Implemented in Sprint 1a")
