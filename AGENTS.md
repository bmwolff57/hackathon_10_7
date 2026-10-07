# AGENTS.md — Rapid Response Hackathon (45-minute rounds)

Repository instructions for agents working on 45-minute emergency-response build rounds. These instructions apply throughout this repository.

## Start here

- Read `ROUND-PLAN.md` if it exists to understand the active problem, scope, and demo path.
- At the start of a new round, copy `ROUND-PLAN-template.md` to `ROUND-PLAN.md` and fill in the problem and architecture before coding.
- Treat bracketed text in the template as placeholders, not requirements for a specific emergency scenario.
- Measure the round windows below from the actual round start, not from the start of an unrelated repository task.

## Project commands

```powershell
uv sync
uv run pytest -x -q
```

Dependencies live in `pyproject.toml`; `uv.lock` records resolved versions. Use uv to manage dependencies and run Python commands.

## The situation

- **Format:** New problem drops at the start of each round. ~45 minutes to build, then judging.
- **Teams:** 2–4 people, formed on-site. Roles: one person owns the plan/demo, the rest build.
- **Judging:** Problem-framing and tradeoff reasoning score over finished products. A coherent, demoable answer to the right problem beats a polished app solving the wrong one.

## Round discipline (the 45-minute clock)

| Window | Do |
| --- | --- |
| 0:00–0:05 | Write the one-paragraph plan + mermaid diagram. Name the core loop: input → decision → output. |
| 0:05–0:30 | Build. One service, one UI page, one data path. No scaffolding rabbit holes. |
| 0:30–0:38 | Smoke tests + run the demo path end to end. Fix only what breaks the demo. |
| 0:38–0:45 | Write `ROUND-PLAN.md` (problem, architecture, tradeoffs, demo script). Rehearse the 60-second pitch. |

Hard rule: at minute 30, whatever exists IS the demo. Build the demo path first, polish never.

## Technical rules

- **API-first, no heavy deps.** No training, no local GPUs, no Docker builds. If a model call is needed, use a hosted API with the key in env vars.
- **Stack:** Python + FastAPI backend (or pure Streamlit/Gradio if UI-first). SQLite or in-memory state. No databases requiring setup.
- **UI:** One page. The demo path must be clickable end-to-end with no config.
- **Dependencies:** stdlib + requests + one web framework + one LLM SDK if needed. If you can't install it with uv in 60 seconds, skip it.

## Testing policy

- 3–5 pytest smoke tests MAX, on the demo path only (e.g., `test_demo_happy_path`, `test_api_rejects_bad_input`).
- Tests exist to prove the demo works to judges, not to be a suite. No unit tests for helpers unless they're on the demo path.
- Run `uv run pytest -x -q` at 0:30 and 0:38. Fix red only if it's the demo path.

## Communication (judges score this)

Every round ships `ROUND-PLAN.md` with:

1. **Problem** (2–3 sentences) — what emergency-response failure does this fix?
2. **Architecture** — mermaid diagram: user → decision logic → output. Under 8 boxes.
3. **Tradeoffs** (bullets) — what you chose NOT to build and why (this is where judging points live).
4. **Demo script** — numbered clicks, under 90 seconds, with the "aha" moment labeled.

## Emergency-response round patterns

Common themes: coordination, communication, resource allocation, information management, public safety, rapid decision-making. Likely winning shapes:

- **Triage/dispatch board** — incoming reports → priority queue → assignment
- **Comms hub** — fragmented channels → single verified feed
- **Resource tracker** — who has what, where, what's needed
- **Decision log** — timestamped decisions with rationale, so a changing situation stays auditable

Whatever the problem: find the single decision-maker's workflow and make it 10x faster. Judges are emergency-response people; speak in their verbs (dispatch, triage, escalate, verify).

## House rules for the agent

- Prefer editing existing files over creating new ones. Prefer the smallest change that keeps the demo path green.
- Never refactor. Never "improve" working code. Duplication is fine.
- Ask before: adding a dependency, touching the demo path, deleting anything.
- Time is the scarcest resource: if a task takes >10 min, cut scope and say what you cut.
