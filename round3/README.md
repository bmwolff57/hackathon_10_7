# Incident Twin - Round 3

A small Flask API and browser demo for grouping call-surge reports into incidents. Critical reports are marked for immediate dispatch; call-takers and dispatchers can flag a grouping, while only a dispatch supervisor can approve, split, or send it back. State is in memory and resets when the process restarts.

## Run

From the repository root:

    uv sync
    uv run flask --app round3.app:app run --debug

Open http://127.0.0.1:5000/. Run tests in another terminal from the repository root:

    uv run pytest -x -q

## Endpoints

All /api requests require X-Role: calltaker, dispatcher, or supervisor.

| Method | Path | Purpose |
| --- | --- | --- |
| POST | /api/reset | Clear demo state |
| POST | /api/demo/load | Load the 14 seeded reports |
| POST | /api/reports | Add a report and return its label and incident |
| GET | /api/incidents | List incidents ranked by priority |
| GET | /api/incidents/<id> | Read incident details and report timeline |
| GET | /api/calltaker/banner | Find a likely existing incident for a new call |
| POST | /api/incidents/<id>/flag | Flag a grouping for supervisor review |
| GET | /api/review | Supervisor queue with flags and draft unit plans |
| POST | /api/incidents/<id>/approve | Supervisor approval |
| POST | /api/incidents/<id>/split | Supervisor splits report IDs into a new incident |
| POST | /api/incidents/<id>/send_back | Supervisor returns a grouping for review |
| GET | /api/log | Read report labels, flags, and decisions |
| GET | / | Serve the dispatch-floor demo page |

## Browser demo (under 90 seconds)

1. Set the role to **Dispatcher** and click **Load demo calls**. **Aha:** 14 reports collapse into 3 incidents.
2. Open incident A's timeline to show the silver sedan moving from W 86th to W 96th.
3. Point out incident B: the cardiac call is two blocks away, remains separate, and is marked **Sent now**.
4. Try a dispatcher approval with curl (blocked), then flag incident A in the page:

       curl.exe -X POST http://127.0.0.1:5000/api/incidents/A/approve -H "X-Role: dispatcher"

5. Switch the page role to **Dispatch supervisor**. Review the groupings and draft plan, then approve incident A.
6. Show the decision log entry.

## Smoke tests

Exactly five demo-path tests:

    uv run pytest -x -q
