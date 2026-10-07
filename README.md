# hackathon_10_7

Rapid-response hackathon project using Python, FastAPI, Uvicorn, and Requests, with pytest for smoke tests.

## Setup

Requires Python 3.11 or newer and uv.

```powershell
uv sync
```

## Tests

Once smoke tests have been added, run:

```powershell
uv run pytest -x -q
```

## Round workflow

- [AGENTS.md](AGENTS.md) contains repository instructions for coding agents.
- Copy [ROUND-PLAN-template.md](ROUND-PLAN-template.md) to `ROUND-PLAN.md` at the start of a round.
- Fill in the problem and architecture before coding, then update the demo script, tradeoffs, and test results during the round.

## Installable round packages

Round packages live in `round1/`, `round2/`, and `round3/` at the repository root. The top-level `pyproject.toml` includes them in the single `hackathon-10-7` distribution.

Install all rounds into the shared environment:

```powershell
uv sync
```

Alternatively, install the project with pip:

```powershell
python -m pip install -e .
```

Put each round's application code directly in `roundN/`. Import it with `import round1`, `import round2`, or `import round3`. Manage shared dependencies and package includes in the top-level `pyproject.toml`.
