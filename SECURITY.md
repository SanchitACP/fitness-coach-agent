# Security & Privacy

This project is built for the **Concierge Agents** track, where personal-data
safety is a judging criterion. Security decisions are documented here.

> Placeholder scaffolded in Phase 0. Fully written in Sprint 2c once the code it
> references is in place.

## Planned guarantees

- **API key management** — all keys via environment variables (`.env`, gitignored).
  `.env.example` is the template; no real values ever committed. App raises on
  startup if `ADK_API_KEY` is missing.
- **No PII in logs** — only session ID and plan ID are logged; never body stats,
  goals, or preferences.
- **Local-only storage** — plans are written to `./plans/` on the user's machine
  and never sent to external services.
- **Input validation** — `utils/validators.py` sanitizes filenames (path-traversal
  prevention) and bounds raw user input.
- **Session lifecycle** — in-session data is cleared on exit (`atexit`).
