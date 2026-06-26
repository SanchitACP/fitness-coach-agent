"""File Storage MCP (core, Phase 1).

Sprint 1b. Saves generated plans locally as JSON and CSV. Never sends data to
external services — the user owns their data.
"""


def save_plan(plan: dict, formats: list = ["json", "csv"]) -> dict:
    """Save a meal plan to the local plans/ directory.

    The plan_id is sanitized before use in a file path (path-traversal
    prevention). Returns the file paths written.
    """
    raise NotImplementedError("Implemented in Sprint 1b")
