# Running the demo (ADK web UI)

For the video demo, run the agent through **ADK's built-in web UI** — a clean
browser chat that shows the conversation and the tool calls. This is the native
ADK interface (no extra dependencies).

## Steps

1. Make sure your key is set: `adk_app/fitness_coach/.env` must contain
   `ANTHROPIC_API_KEY=...` (copy it from the repo-root `.env`).
2. From the repo root:

   ```bash
   python run_web.py
   ```

   (equivalently: `python -m google.adk.cli web adk_app`)

3. Open **http://127.0.0.1:8000** in a browser.
4. In the app dropdown, select **fitness_coach** (it's the only entry).
5. Chat, e.g.:

   > I want to bulk. 180 lbs, 5'10", 25, male, moderate activity. I like Italian
   > and Asian food. No peanuts. I train 5 days a week, intermediate. I like
   > variety.

   The agent asks for prep time and dislikes, then calls the three tools and
   returns the full plan. The UI shows each tool call — good to capture on video.

## Notes

- The plain CLI (`python main.py`) is the simpler fallback if you'd rather record
  a terminal demo; it also auto-saves the plan to `plans/`.
- `adk run adk_app/fitness_coach "..."` does a single-step run in the terminal
  (set `PYTHONIOENCODING=utf-8` first so emoji in replies don't error on Windows).
