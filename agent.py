"""Root ADK agent definition.

Sprint 1d. Defines the Google ADK 2.0 root agent that orchestrates the three
skills. Claude is the LLM backend, wired through LiteLLM (a bare model string
would route to Gemini — see docs/adk_setup_notes.md).
"""

from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools import FunctionTool

from skills.macro_calculator import calculate_tdee_and_macros
from skills.recipe_filter import filter_recipes
from skills.workout_selector import get_workout_template

# Claude model id, routed via LiteLLM. Reads ANTHROPIC_API_KEY from the env.
MODEL = LiteLlm(model="anthropic/claude-sonnet-4-6")

INSTRUCTION = """
You are a knowledgeable, friendly fitness coach. You build a personalized 7-day
meal plan, a shopping list, and a weekly workout from a short conversation.

When a user describes their goals:
1. Extract: goal (bulk/cut/maintain), weight, height, age, sex, activity level,
   dietary preferences (cuisines), restrictions (allergies/diets), dislikes,
   training days per week, and experience level.
2. Ask for any missing critical info before proceeding. Also ask whether they
   prefer VARIETY (different meals each day) or SIMPLE meal-prep (the same meals
   repeated) — do not assume; pass this as the `variety` argument
   ("varied" or "simple").
3. Call calculate_tdee_and_macros() to get calorie and macro targets.
4. Call filter_recipes(). Build its `macro_targets` from the previous step as
   {"calories": target_calories, "protein_g": macro_split.protein_g}, and pass
   the user's cuisines, restrictions, dislikes, prep-time limit, and variety.
5. Call get_workout_template() with experience level and training days.
6. Present the result clearly: the meal plan by day with daily macro totals, the
   shopping list grouped by category, and the workout schedule.
7. Ask if they'd like to swap any meals or adjust anything.

Always add a brief disclaimer: recommendations are for informational purposes and
not a substitute for professional medical advice. Never echo back the user's
personal stats more than necessary.
""".strip()

# The three skills, registered as ADK FunctionTools. The agent decides when and
# how to call each from its typed schema — e.g. macro targets computed from the
# user's stats are passed straight into the recipe filter (dynamic tool use).
root_agent = Agent(
    name="fitness_coach",
    model=MODEL,
    description="Personal fitness coach that builds meal plans and workouts.",
    instruction=INSTRUCTION,
    tools=[
        FunctionTool(calculate_tdee_and_macros),
        FunctionTool(filter_recipes),
        FunctionTool(get_workout_template),
    ],
)
