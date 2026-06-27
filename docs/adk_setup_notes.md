# ADK setup notes (Phase 0 verification)

Scratch notes from verifying the Google ADK 2.0 environment on Windows. Useful
raw material for the writeup's "Implementation & Journey" section.

## Verified working
- `pip install "google-adk[extensions]==2.0.0"` installs cleanly on Windows
  (Python 3.14).
- `from google.adk.agents import Agent` and `from google.adk.tools import
  FunctionTool` import fine.
- An `Agent(...)` instantiates as an `LlmAgent` with `FunctionTool`s registered.

## Gotcha: Claude is not a bare model string
The product spec shows `model="claude-sonnet-4-6"`. That does **not** work — ADK
routes a bare model string to its native **Gemini** backend. Non-Gemini models
go through **LiteLLM**, which is only present with the `[extensions]` extra.

**Correct wiring for Claude:**
```python
from google.adk.models.lite_llm import LiteLlm
agent = Agent(
    name="fitness_coach",
    model=LiteLlm(model="anthropic/claude-sonnet-4-6"),
    ...
)
```
- Requires `google-adk[extensions]` (pulls in `litellm`).
- Reads the **`ANTHROPIC_API_KEY`** env var (not `ADK_API_KEY` as the spec drafts
  imply). `.env.example` and the security layer use `ANTHROPIC_API_KEY`.

## Not yet exercised
- A live LLM round-trip — needs a real `ANTHROPIC_API_KEY`. Framework wiring is
  confirmed; the only unknown left is the API call itself.
