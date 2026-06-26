"""Google Calendar MCP (Phase 2, optional).

Syncs the workout schedule to Google Calendar via the Calendar MCP server.
Stub in Phase 1; implemented in Sprint 2b if time permits. Falls back to an
.ics file export if the MCP call fails.
"""


def sync_workouts_to_calendar(
    workout_plan: dict,
    start_date: str,
    workout_time: str = "06:00",
) -> dict:
    """Create Google Calendar events for each training day (rest days skipped).

    Requires OAuth pre-configured. On failure, exports an .ics file instead.
    """
    raise NotImplementedError("Implemented in Sprint 2b (Phase 2, optional)")
