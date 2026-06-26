"""Workout Template Selector skill (ADK FunctionTool).

Sprint 1c. Returns a pre-built workout template matching the user's experience
level and weekly availability.
"""


def get_workout_template(
    experience_level: str,
    days_per_week: int,
    split_preference: str = "auto",
) -> dict:
    """Return a workout template matching experience and availability.

    If split_preference is 'auto', selects by days_per_week:
        3 -> Full Body, 4 -> Upper/Lower, 5 -> Upper/Lower (A/B), 6 -> PPL.

    Returns:
        Full workout template dict with all exercise days.
    """
    raise NotImplementedError("Implemented in Sprint 1c")
