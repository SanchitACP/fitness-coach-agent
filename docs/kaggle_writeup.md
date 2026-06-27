# Accessible Fitness & Macro Coach

**Track: Concierge Agents**

## 1. The Problem

Getting fitness nutrition right is deceptively hard. To eat for a goal you have to
know your TDEE (total daily energy expenditure), translate that into a macro split
of protein, carbs, and fat, then find meals that hit those numbers *while*
respecting your allergies, your dietary restrictions, the cuisines you actually
enjoy, and how much time you have to cook — and then line all of that up with a
training program that matches your experience and schedule. Most people solve this
in one of three unsatisfying ways: they pay for a coach, they use a rigid app that
hands back a fixed template, or they guess.

The apps are the most common path and the most frustrating. They ask you to fill
in a form and return the same plan they'd give anyone with similar stats. They
don't reason about the *intersection* of your constraints — that you bulk, eat
mostly Italian and Asian food, can't have peanuts, and only have 30 minutes to
cook. A vegetarian who wants 130g of protein gets the same rigid output as someone
with no restrictions at all.

This project targets the individual struggling with exactly that: a beginner who
wants structure but doesn't know where to start, or an intermediate lifter who
finds macro planning tedious. It replaces the form with a conversation, and the
template with reasoning.

## 2. Why Agents?

The key word is **reason**. A traditional fitness app runs a database query. This
agent does something a static app cannot: it extracts your goal, your body stats,
and your preferences simultaneously from natural language, then chains specialized
tools to build a coherent plan.

When you say *"I want to bulk, I'm 180 pounds, I like Italian and Asian food, and
I can't eat peanuts,"* the agent extracts all of that at once, calls a macro
calculator to derive your exact calorie and protein targets, passes those targets
into a recipe filter that searches a curated database against every constraint
together — macros, allergens, cuisine, prep time, variety — and selects a workout
template for your availability. It synthesizes a 7-day plan, a shopping list, and a
training week in a single reasoning loop.

It also handles the things a form can't. If critical information is missing, it
asks a clarifying question instead of guessing. If you express a preference it
can't infer — do you want variety, or do you meal-prep the same thing every day? —
it asks rather than assuming. And if you say *"skip beef this week,"* it re-runs
the filter with the updated constraint instead of rebuilding from scratch. That is
mid-conversation adaptation over the intersection of many constraints at once.
This is not a template engine. This is an agent.

## 3. Architecture

The system is built on **Google ADK 2.0**, with **Claude** (`claude-sonnet-4-6`)
as the reasoning backend, running locally as a CLI.

At the center is a single ADK **root agent** (`fitness_coach`). It owns the
conversation: parsing intent, asking for missing information, deciding which tools
to call and in what order, and synthesizing the final plan from their outputs.
Claude does not run as a raw SDK call — it is wired *into* ADK through LiteLLM, so
ADK manages the agent loop, the tool schemas, and the orchestration.

The agent's capabilities are three **skills**, each registered as an ADK
`FunctionTool` with a typed schema the model reads to decide when and how to call
it:

- **Macro Calculator** computes TDEE via the Mifflin-St Jeor equation and a
  goal-based macro split.
- **Recipe Filter** selects meals from a 70-recipe database, hard-blocking
  allergens and diets, respecting prep time and dislikes, enforcing variety, and
  scaling portions to hit calorie targets.
- **Workout Selector** picks one of four training templates based on experience
  and weekly availability.

Below the skills sits an **MCP layer**. A local File Storage MCP saves each
generated plan to disk as JSON (a complete record) and CSV (a spreadsheet-friendly
meal table). A Google Calendar MCP is stubbed for Phase 2 workout sync.

At the bottom is a **local data layer**: `recipes.json` (70 curated recipes with
macros), `templates/` (four workout splits), `plans/` (the user's saved plans,
never committed), and `.env` (API keys, never committed).

The flow is linear and legible: **User → Root Agent → Skills → MCP → Data**, with
the agent dynamically deciding the path. The most important interaction is that the
macro calculator's *output becomes the recipe filter's input* — the calorie and
protein targets it derives are passed straight into the meal search. That dynamic
chaining is the clever tool use at the heart of the design.

## 4. Implementation & Journey

I built the system bottom-up: the deterministic engine first (the three skills and
the file MCP, each fully unit-tested), then the ADK agent wrapped around it. That
ordering meant the hard logic was proven before any LLM was involved, and the
agent layer became thin and reliable.

Several decisions and course corrections shaped the result:

**Claude inside ADK was not a one-liner.** The obvious wiring — passing
`model="claude-sonnet-4-6"` as a string — silently routes to ADK's native Gemini
backend. Claude requires the `google-adk[extensions]` extra and the LiteLLM
wrapper (`LiteLlm("anthropic/claude-sonnet-4-6")`), reading `ANTHROPIC_API_KEY`. I
discovered this during a Phase 0 environment check rather than mid-build, which is
exactly why that check existed.

**Hardcoded recipes over a live API.** A live nutrition API adds rate limits and a
network dependency that can fail during a demo, for no gain in the part that
matters — the reasoning. A curated 70-recipe database makes the agent reliable and
keeps everything local, which also serves the privacy story.

**Portion scaling was the fix for an early failure.** My first recipe filter
produced plans that capped around 1,700 calories — useless for a bulk. The cause
was structural: individual recipes are ~400-500 calories, so four of them can't
reach 3,000. The fix was to select recipes by *protein density* and then scale
servings per day to hit the calorie target. Now the same recipes serve a 1,600-cal
cut and a 3,100-cal bulk.

**Variety became a question, not a rule.** An early version produced oddly
repetitive "paired" days. I first assumed I should forbid repeats — until I
realized many people deliberately eat the same breakfast every day. Forcing variety
is as wrong as forcing repetition. So variety became a user preference the agent
asks about (`varied` vs. `simple` meal-prep), which is both more correct and a
better demonstration of adaptive behavior.

**Coverage matters more than count.** Testing a vegan plan revealed the database
had *zero* vegan breakfast or snack options — the filter would have starved. The
lesson was that database *coverage of constraint intersections* matters more than
raw size, so I expanded deliberately to fill the thin gaps.

What surprised me most was how much of "agent quality" lives in the tools and the
data, not the prompt. The model is only as good as what it can call.

## 5. Course Concepts Used

This project targets five of the six course concepts.

| Concept | How it's used | File(s) |
|---------|---------------|---------|
| **Agent (ADK)** | Root agent runs Claude via LiteLLM, orchestrates tools, manages multi-turn conversation | `agent.py` |
| **Agent Skills** | Three skills registered as ADK `FunctionTool`s with typed schemas | `skills/macro_calculator.py`, `skills/recipe_filter.py`, `skills/workout_selector.py` |
| **MCP Server** | Local File MCP saves plans (JSON + CSV); Calendar MCP stub for Phase 2 | `mcp/file_storage.py`, `mcp/calendar_sync.py` |
| **Security** | Env-only keys, no PII in logs, local storage, input sanitization, session clearing | `main.py`, `utils/validators.py`, `SECURITY.md` |
| **Deployability** | One command to run; cloud = clone, set env, run | `main.py`, README |

The standout is the interplay between the agent and its skills: the macro
calculator's derived targets are passed dynamically into the recipe filter, and
the agent decides the call order from the conversation rather than following a
hardcoded script.

## 6. Security & Privacy

Because this is a Concierge agent handling personal body data, security is
treated as a feature, not an afterthought — and all of it is implemented and
tested. API keys are loaded only from a git-ignored `.env`, and the app fails fast
at startup if the key is missing. Logs contain only a session id and plan id —
never weight, age, goals, or preferences. Plans are written exclusively to a local
`plans/` directory and never transmitted anywhere. User input is sanitized: the
`plan_id` is cleaned before use in a file path to prevent traversal (covered by a
test), and raw input is bounded. In-session state is cleared on exit. The only
data that leaves the machine is the conversation text sent to Claude for reasoning —
the same as any LLM application. There is no telemetry and no third-party
nutrition service.

## 7. Results & Future Work

The agent works end-to-end. Given a real profile — 180 lb, 25M, moderate activity,
bulk, Italian/Asian, no peanuts, 5 training days — it asks for the two missing
details (prep time and dislikes), then produces a 7-day plan hitting ~3,100
calories per day with a categorized shopping list and a 5-day Upper/Lower workout,
saved locally as JSON and CSV. The full engine is covered by 71 unit tests; the
live conversation is verified manually.

It is honest about its limits: an aggressive protein target on a low-calorie
restricted diet can't always be met, and in those cases the agent surfaces a
warning rather than faking the numbers or breaking a restriction.

Three features would extend it. First, a **live nutrition API** to replace the
curated database and scale variety for many users. Second, a **preference feedback
loop** that remembers "skip beef" across sessions and learns tastes over time.
Third, **Google Calendar sync** to push the generated workouts straight onto the
user's calendar. Each is scoped in `FUTURE.md` — captured as vision without
expanding what was deliberately a focused, reliable MVP.
