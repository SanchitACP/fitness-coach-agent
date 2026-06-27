# Security & Privacy

This is a **Concierge** (personal) agent — it handles your body stats, goals, and
dietary information. Personal-data safety is a judging criterion for the track and
a design priority here. Everything below is implemented, not aspirational.

## Guarantees

### 1. API keys via environment only
Keys are loaded from `.env` (which is git-ignored) and never hardcoded. The app
**fails fast** at startup if the key is missing rather than running in a broken
state — see `require_api_key()` in [main.py](main.py). [.env.example](.env.example)
is the committed template and contains no real values.

### 2. No PII in logs
Logs carry only a generated session id and plan id — never weight, height, age,
goals, or preferences. See the `logger` calls in [main.py](main.py)
(`"Started session %s"`, `"Saved plan %s"`).

### 3. Local-only storage
Generated plans are written to `./plans/` on the user's machine
([mcp/file_storage.py](mcp/file_storage.py)) and never transmitted to any external
service. `plans/` is git-ignored so personal plans are never committed.

### 4. Input validation / sanitization
- **Path-traversal prevention:** the `plan_id` is run through
  `sanitize_filename()` before being used in a file path, so a malicious id like
  `../../etc/passwd` cannot escape the output directory.
- **Bounded user input:** raw input is trimmed and length-limited via
  `sanitize_user_input()` before reaching the agent.

Both live in [utils/validators.py](utils/validators.py); the traversal guard is
covered by a test in [tests/test_file_storage.py](tests/test_file_storage.py).

### 5. Session lifecycle
In-session scratch state is cleared on exit via an `atexit` handler
(`_clear_session()` in [main.py](main.py)), so nothing persists by accident. The
ADK session itself is in-memory and dies with the process.

## What leaves your machine
Only the conversation text sent to the Claude API for reasoning — the same as any
LLM app. No plans, files, or derived personal data are sent anywhere. There is no
analytics, telemetry, or third-party recipe/nutrition service in the MVP.

## Reporting
This is a student capstone project, not production software. Issues can be raised
on the GitHub repository.
