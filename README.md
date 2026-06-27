# Accessible Fitness & Macro Coach

An AI agent (built on **Google ADK 2.0**, with Claude as the LLM backend) that takes
conversational input — your goals, body stats, dietary preferences, and training
availability — and produces a personalized 7-day meal plan, a shopping list, and a
week of workouts.

**Author:** Sanchit Rai
**Capstone:** Kaggle AI Agents — Concierge Agents track

> This README is a placeholder scaffolded during Phase 0. Full documentation
> (architecture diagram, setup steps, example output, course-concept map, design
> decisions) lands in Sprint 2c.

## Status

🚧 In development — Phase 0 (repo + environment setup).

## Quick start (planned)

```bash
git clone https://github.com/<you>/fitness-coach-agent.git
cd fitness-coach-agent
pip install -r requirements.txt
cp .env.example .env   # then add your ANTHROPIC_API_KEY
python main.py
```

## Course concepts demonstrated

| Concept | Where |
|---------|-------|
| ADK Agent (multi-agent) | `agent.py` |
| MCP Server | `mcp/file_storage.py`, `mcp/calendar_sync.py` |
| Agent Skills | `skills/macro_calculator.py`, `skills/recipe_filter.py` |
| Security | `utils/validators.py`, `main.py`, `SECURITY.md` |
| Antigravity | Video demo |
| Deployability | Video; one-command `python main.py` |
