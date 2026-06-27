"""Entry point — ADK agent CLI session.

Sprint 1d. Wires the root agent into a read -> sanitize -> agent -> print loop,
auto-saves any plan the agent generates, and applies the security layer:
  * API key loaded from .env (never hardcoded); startup fails fast if missing.
  * Logs carry only a session id — never personal stats.
  * In-session data is cleared on exit.
"""

import asyncio
import atexit
import logging
import os
import uuid
from datetime import datetime

from dotenv import load_dotenv

APP_NAME = "fitness_coach"
USER_ID = "local_user"

logger = logging.getLogger(APP_NAME)

# In-session scratch state; cleared on exit so nothing persists accidentally.
_session_store = {}


def require_api_key() -> str:
    """Load .env and return ANTHROPIC_API_KEY, failing fast if it's absent."""
    load_dotenv()
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        raise EnvironmentError(
            "ANTHROPIC_API_KEY not found. Copy .env.example to .env and add your "
            "key (get one at console.anthropic.com)."
        )
    return key


def _configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")


def _clear_session() -> None:
    """Wipe in-session state on exit (no PII left behind)."""
    _session_store.clear()
    logger.info("Session data cleared.")


def build_runner():
    """Create an ADK Runner with an in-memory session, plus the session id."""
    # Imported lazily so importing this module (e.g. in tests) doesn't require
    # the heavier ADK runtime until a live session is actually started.
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService

    from agent import root_agent

    session_service = InMemorySessionService()
    session_id = uuid.uuid4().hex
    # create_session is async; run it once at startup.
    asyncio.run(session_service.create_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=session_id))
    runner = Runner(app_name=APP_NAME, agent=root_agent, session_service=session_service)
    return runner, session_id


def _extract_plan(event):
    """Return a meal-plan dict from a filter_recipes tool response, if present."""
    for fr in event.get_function_responses() or []:
        if fr.name != "filter_recipes":
            continue
        resp = fr.response
        if isinstance(resp, dict):
            if "days" in resp:
                return resp
            inner = resp.get("result")
            if isinstance(inner, dict) and "days" in inner:
                return inner
    return None


def _handle_turn(runner, session_id, text):
    """Send one user message; print the agent's reply; return any plan produced."""
    from google.genai import types

    from utils.validators import sanitize_user_input

    message = types.Content(role="user",
                            parts=[types.Part(text=sanitize_user_input(text))])
    plan = None
    for event in runner.run(user_id=USER_ID, session_id=session_id, new_message=message):
        found = _extract_plan(event)
        if found:
            plan = found
        if event.is_final_response() and event.content:
            reply = "".join(p.text or "" for p in event.content.parts)
            print(f"\nCoach: {reply}\n")
    return plan


def _auto_save(plan):
    """Persist a generated plan locally and tell the user where it went."""
    from mcp.file_storage import save_plan

    plan.setdefault("plan_id", f"plan_{datetime.now():%Y%m%d_%H%M%S}")
    result = save_plan(plan)
    logger.info("Saved plan %s", result["plan_id"])
    paths = ", ".join(result["paths"].values())
    print(f"[Saved your plan to: {paths}]\n")


def main() -> None:
    _configure_logging()
    require_api_key()
    atexit.register(_clear_session)

    runner, session_id = build_runner()
    logger.info("Started session %s", session_id)

    print("Tell me about your fitness goals and I'll build your plan. "
          "(type 'quit' to exit)\n")
    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if user_input.lower() in {"quit", "exit"}:
            break
        if not user_input:
            continue
        plan = _handle_turn(runner, session_id, user_input)
        if plan:
            _auto_save(plan)

    print("\nTake care! Your data stays on your machine.")


if __name__ == "__main__":
    main()
