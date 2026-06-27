"""Root ADK agent — re-export.

The agent is defined in adk_app/fitness_coach/agent.py so the ADK CLI
(`adk web adk_app` / `adk run adk_app/fitness_coach`) discovers exactly one
agent. This module re-exports `root_agent` so the CLI (main.py) and the tests can
keep importing `from agent import root_agent`.
"""

from adk_app.fitness_coach.agent import INSTRUCTION, MODEL, root_agent  # noqa: F401
