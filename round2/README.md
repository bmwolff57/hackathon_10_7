# Get Me Home NYC API

A tiny, in-memory FastAPI demo for verified closures and route recommendations during a declared city event. The feed starts off, and social reports store only a place name.

## Run

```powershell
uv sync
uv run uvicorn round2.app:app --reload
uv run pytest -x -q
```

Open `http://127.0.0.1:8000/` for the demo dashboard. Select **Start demo event** to activate the feed and show the first crowd report; select **NYPD confirms closure** to see the recommended route change. The API itself remains off until the event is activated. Use `/docs` for direct endpoint access.

## Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/activate` | Turn on the feed for a declared event (`{"event":"..."}`) |
| POST | `/api/deactivate` | Turn off the feed and clear social signals |
| POST | `/api/official` | Record an NYPD, DOT, MTA, or OEM report |
| POST | `/api/social` | Add a place-only social signal |
| GET | `/api/feed` | View event, tiered reports, banners, and station loads |
| GET | `/api/route?from=MSG` | Recommend a station from MSG, Times Sq, or Bryant Park |
| POST | `/api/sms` | Return a short text-message route suggestion |
| GET | `/api/audit` | Read activation, deactivation, and official-report audit entries |
| POST | `/api/reset` | Reset in-memory demo state |

The feed and all incident endpoints return 403 while inactive. Official reports are confirmed; three social signals make a place likely; one or two are reported. Only confirmed and likely places are skipped during routing.

## Curl demo (happy path)

With the server running at `http://127.0.0.1:8000`, run these commands in order in PowerShell. A temporary JSON file keeps Windows `curl.exe` argument quoting predictable:

1. Activate an event:

   ```powershell
   $bodyPath = Join-Path $env:TEMP 'get-me-home.json'
   Set-Content -Path $bodyPath -NoNewline -Encoding ascii -Value '{"event":"Knicks championship parade"}'
   curl.exe -X POST http://127.0.0.1:8000/api/activate -H 'Content-Type: application/json' --data-binary "@$bodyPath"
   ```

2. Check the initial recommendation (34 St-Penn Station):

   ```powershell
   curl.exe "http://127.0.0.1:8000/api/route?from=MSG"
   ```

3. Add one social report. It is only reported; routing still recommends Penn:

   ```powershell
   Set-Content -Path $bodyPath -NoNewline -Encoding ascii -Value '{"place":"34 St-Penn Station"}'
   curl.exe -X POST http://127.0.0.1:8000/api/social -H 'Content-Type: application/json' --data-binary "@$bodyPath"
   curl.exe "http://127.0.0.1:8000/api/route?from=MSG"
   ```

4. **Aha — NYPD confirms Penn is closed, so the recommended route flips:**

   ```powershell
   Set-Content -Path $bodyPath -NoNewline -Encoding ascii -Value '{"place":"34 St-Penn Station","source":"NYPD","note":"Platform closed"}'
   curl.exe -X POST http://127.0.0.1:8000/api/official -H 'Content-Type: application/json' --data-binary "@$bodyPath"
   curl.exe "http://127.0.0.1:8000/api/route?from=MSG"
   ```
