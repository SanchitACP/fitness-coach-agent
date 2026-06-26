"""Input validation and sanitization helpers (Security layer).

Sprint 1d. Used to prevent path traversal in saved filenames and to bound/clean
raw user input before it reaches the agent.
"""

import re


def sanitize_filename(raw: str) -> str:
    """Strip characters that could cause path traversal."""
    return re.sub(r"[^a-zA-Z0-9_\-]", "", raw)


def sanitize_user_input(raw: str, max_length: int = 2000) -> str:
    """Trim and length-limit raw user input."""
    return raw.strip()[:max_length]
