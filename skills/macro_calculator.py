"""Macro Calculator skill (ADK FunctionTool).

Sprint 1a. Computes Total Daily Energy Expenditure (TDEE) and daily macro
targets using the Mifflin-St Jeor equation -- the most accurate of the common
BMR estimators for the general population. Registered with the ADK agent so it
can be called dynamically on the body stats the agent extracts from conversation.

Formula source: Mifflin MD, St Jeor ST, et al. "A new predictive equation for
resting energy expenditure in healthy individuals." Am J Clin Nutr, 1990.
Activity multipliers follow the standard Harris-Benedict/ACSM activity factors.
"""

# Standard activity multipliers applied to BMR to estimate TDEE.
ACTIVITY_MULTIPLIERS = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "active": 1.725,
    "very_active": 1.9,
}

# Daily calorie adjustment applied to TDEE based on the user's goal.
GOAL_CALORIE_ADJUSTMENTS = {"bulk": 300, "cut": -300, "maintain": 0}

# Macro distribution (protein / carbs / fat as fractions of total calories) by goal.
GOAL_MACRO_SPLITS = {
    "bulk": {"protein": 0.30, "carbs": 0.45, "fat": 0.25},
    "cut": {"protein": 0.35, "carbs": 0.40, "fat": 0.25},
    "maintain": {"protein": 0.30, "carbs": 0.40, "fat": 0.30},
}

# Calories per gram of each macronutrient.
CALORIES_PER_GRAM = {"protein": 4, "carbs": 4, "fat": 9}


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
        Dict with tdee, target_calories, macro_split (protein_g, carbs_g, fat_g),
        a confidence note, and the formula name.
    """
    # Mifflin-St Jeor is defined in metric units, so convert first.
    # Unit conversion is the usual source of bugs here -- keep it explicit.
    weight_kg = weight_lbs * 0.453592
    height_cm = height_inches * 2.54

    # Basal Metabolic Rate -- the male and female variants differ only by the constant.
    if sex.upper() == "M":
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + 5
    else:
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 161

    # Scale BMR by activity level to get TDEE (default to moderate if unknown).
    tdee = bmr * ACTIVITY_MULTIPLIERS.get(activity_level.lower(), 1.55)

    # Apply the goal-based calorie surplus/deficit.
    target_calories = tdee + GOAL_CALORIE_ADJUSTMENTS.get(goal.lower(), 0)

    # Split target calories into macros, then convert calories -> grams per macro.
    split = GOAL_MACRO_SPLITS.get(goal.lower(), GOAL_MACRO_SPLITS["maintain"])
    macro_split = {
        f"{macro}_g": round((target_calories * fraction) / CALORIES_PER_GRAM[macro])
        for macro, fraction in split.items()
    }

    return {
        "tdee": round(tdee),
        "target_calories": round(target_calories),
        "macro_split": macro_split,
        # Estimates carry inherent variance; surface that to the user.
        "confidence_note": "+/-100 cal; individual metabolism varies",
        "formula": "Mifflin-St Jeor",
    }
