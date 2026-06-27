"""Launch the ADK web UI for the fitness coach (demo / recording).

Opens ADK's built-in chat UI at http://127.0.0.1:8000 with a single agent in the
app list ("fitness_coach"). The API key is read from adk_app/fitness_coach/.env.

    python run_web.py
"""

import os
import subprocess
import sys

# UTF-8 so emoji in responses don't trip the Windows console.
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

sys.exit(subprocess.call(
    [sys.executable, "-m", "google.adk.cli", "web", "adk_app"]
))
