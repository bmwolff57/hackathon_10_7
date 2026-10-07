from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse, Response

app = FastAPI(title="Get Me Home NYC")

HOME_PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Get Me Home NYC</title><style>
:root{font-family:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;color:#17231f;background:#f1f5f2;font-synthesis:none}
*{box-sizing:border-box}body{margin:0}.top{background:#10251f;color:#fff;padding:18px max(24px,calc((100vw - 1080px)/2));display:flex;justify-content:space-between;align-items:center}
.brand{font-weight:750;letter-spacing:-.03em}.live{font-size:12px;color:#c9d9d1}.live:before{content:"";display:inline-block;width:8px;height:8px;border-radius:99px;background:#f4b544;margin-right:8px}
main{max-width:1080px;margin:48px auto;padding:0 22px}.eyebrow{text-transform:uppercase;letter-spacing:.12em;font-weight:700;font-size:11px;color:#527063}
h1{font-size:clamp(32px,5vw,52px);line-height:1.02;letter-spacing:-.05em;margin:12px 0}.lede{max-width:650px;line-height:1.6;color:#64736d;margin:0 0 26px}
.grid{display:grid;grid-template-columns:1.2fr .8fr;gap:18px}.card{background:#fff;border:1px solid #dce5df;border-radius:18px;padding:24px;box-shadow:0 10px 30px #203b2b0a}
.head{display:flex;align-items:center;justify-content:space-between;gap:12px}.badge{font-size:11px;font-weight:750;letter-spacing:.06em;text-transform:uppercase;background:#fff2d7;color:#875c10;padding:8px 10px;border-radius:99px}
.badge.on{background:#e0f5e9;color:#1d7046}.event{font-size:21px;font-weight:700;margin:20px 0 4px}.muted{color:#728079;font-size:14px;line-height:1.5}
button{font:inherit;font-size:14px;font-weight:700;border:0;border-radius:10px;padding:12px 16px;cursor:pointer;background:#163b2c;color:#fff}button:hover{background:#24593f}button.secondary{background:#edf3ef;color:#29483a}button:disabled{opacity:.55;cursor:wait}
.actions{display:flex;flex-wrap:wrap;gap:9px;margin-top:20px}.row{padding:13px 0;border-bottom:1px solid #edf1ee;display:flex;justify-content:space-between;gap:12px}.row:last-child{border:0}.name{font-weight:650}.tag{font-size:11px;color:#775c24;background:#fbf1d8;padding:5px 8px;border-radius:99px;height:max-content}.tag.confirmed{color:#1d7046;background:#e0f5e9}
.route{font-size:21px;font-weight:750;line-height:1.3;margin:18px 0 7px}.notice{min-height:24px;color:#a13d32;font-size:13px;margin-top:10px}.foot{font-size:12px;color:#7c8983;margin-top:24px}
@media(max-width:720px){main{margin:30px auto}.grid{grid-template-columns:1fr}.top{padding:16px 22px}}
</style></head><body>
<header class="top"><div class="brand">GET ME HOME <span style="color:#a6c7b5">NYC</span></div><div class="live">CITY EVENT RESPONSE</div></header>
<main><div class="eyebrow">Live event travel guidance</div><h1>Find a safer way<br>home.</h1><p class="lede">Official reports and crowd signals become clear closure status and practical routes. This demo uses seeded station data and turns on only for a declared event.</p>
<section class="grid"><article class="card"><div class="head"><div class="eyebrow">Event window</div><div id="status" class="badge">FEED OFF</div></div><div id="event" class="event">No active event</div><div id="summary" class="muted">Start the demo event to see live route guidance for tonight.</div>
<div class="actions"><button id="activate" onclick="startDemo()">Start demo event</button><button id="verify" class="secondary" onclick="verifyClosure()" hidden>NYPD confirms closure</button><button id="deactivate" class="secondary" onclick="endEvent()" hidden>End event</button></div><div id="notice" class="notice"></div></article>
<article class="card"><div class="eyebrow">Recommended from MSG</div><div id="route" class="route">Activate an event to get a route</div><div id="advice" class="muted">Recommendations balance walking distance and station crowding.</div><div class="foot">Route scoring includes current assigned riders.</div></article>
<article class="card"><div class="head"><div class="eyebrow">Verified closures</div><div class="muted">OFFICIAL + CROWD SIGNALS</div></div><div id="closures" style="margin-top:12px"><div class="muted">No reports yet.</div></div></article>
<article class="card"><div class="eyebrow">How to read this feed</div><div class="row"><span class="name">Confirmed</span><span class="muted">Official agency report</span></div><div class="row"><span class="name">Likely</span><span class="muted">3+ matching social reports</span></div><div class="row"><span class="name">Reported</span><span class="muted">1–2 reports; route stays open</span></div></article></section>
<div class="foot">Demo only · Not an official NYC emergency service</div></main>
<script>
const $=id=>document.getElementById(id); const penn='34 St-Penn Station';
async function api(path,method='GET',body){const r=await fetch(path,{method,headers:body?{'Content-Type':'application/json'}:{},body:body?JSON.stringify(body):undefined});const d=await r.json();if(!r.ok)throw Error(d.error||d.detail?.error||'Request failed');return d}
function showError(e){$('notice').textContent=e.message}
async function refresh(){try{const [f,r]=await Promise.all([api('/api/feed'),api('/api/route?from=MSG')]);$('status').textContent='FEED LIVE';$('status').className='badge on';$('event').textContent=f.event;$('summary').textContent='Event guidance is active. Closures are ranked by verification level.';$('route').textContent=r.best.name;$('advice').textContent=r.advice;$('verify').hidden=f.closures.some(c=>c.place===penn&&c.status==='confirmed');$('deactivate').hidden=false;$('activate').hidden=true;$('closures').innerHTML=f.closures.length?f.closures.map(c=>`<div class="row"><span class="name">${c.place}</span><span class="tag ${c.status}">${c.status}</span></div>`).join(''):'<div class="muted">No reports yet. Stations are available.</div>';}catch(e){$('status').textContent='FEED OFF';$('status').className='badge';}}
async function startDemo(){try{$('activate').disabled=true;await api('/api/activate','POST',{event:'Knicks championship parade'});await api('/api/social','POST',{place:penn});$('verify').hidden=false;$('notice').textContent='One crowd report is visible. It does not close the station.';await refresh()}catch(e){showError(e)}finally{$('activate').disabled=false}}
async function verifyClosure(){try{await api('/api/official','POST',{place:penn,source:'NYPD',note:'Platform closure confirmed'});$('notice').textContent='Aha: official confirmation changed the recommended station.';await refresh()}catch(e){showError(e)}}
async function endEvent(){try{await api('/api/deactivate','POST');$('status').textContent='FEED OFF';$('status').className='badge';$('event').textContent='No active event';$('summary').textContent='Start the demo event to see live route guidance for tonight.';$('route').textContent='Activate an event to get a route';$('advice').textContent='Recommendations balance walking distance and station crowding.';$('closures').innerHTML='<div class="muted">No reports yet.</div>';$('activate').hidden=false;$('verify').hidden=true;$('deactivate').hidden=true;$('notice').textContent='Event ended. Social signals were cleared.'}catch(e){showError(e)}}
refresh();
</script></body></html>"""


@app.get("/", response_class=HTMLResponse)
def home():
    return HOME_PAGE


@app.get("/favicon.ico")
def favicon():
    return Response(status_code=204)


class FeedOff(Exception):
    pass


@app.exception_handler(FeedOff)
def feed_off_handler(request, exc):
    return JSONResponse(status_code=403, content={"error": "Feed is off. Available only during a declared event window."})

ORIGINS = ("MSG", "Times Sq", "Bryant Park")
STATIONS = [
    {"name": "34 St-Penn Station", "lines": "1 2 3", "load": 90, "walk": {"MSG": 2, "Times Sq": 12, "Bryant Park": 10}},
    {"name": "34 St-Herald Sq", "lines": "B D F M N Q R W", "load": 95, "walk": {"MSG": 4, "Times Sq": 9, "Bryant Park": 7}},
    {"name": "28 St", "lines": "1", "load": 35, "walk": {"MSG": 7, "Times Sq": 16, "Bryant Park": 13}},
    {"name": "Times Sq-42 St", "lines": "1 2 3 7 N Q R W S", "load": 85, "walk": {"MSG": 11, "Times Sq": 1, "Bryant Park": 5}},
    {"name": "47-50 Sts-Rockefeller Ctr", "lines": "B D F M", "load": 70, "walk": {"MSG": 18, "Times Sq": 6, "Bryant Park": 6}},
    {"name": "50 St", "lines": "1", "load": 30, "walk": {"MSG": 15, "Times Sq": 7, "Bryant Park": 11}},
]
RIDESHARE = {"name": "10th Ave & W 37th St", "walk": {"MSG": 8, "Times Sq": 12, "Bryant Park": 15}}
state = {"active": False, "event": "", "official": [], "social": [], "audit": [], "assigned": {}}


def log(message):
    state["audit"].append({"time": datetime.now(timezone.utc).isoformat(), "message": message})


def require_active():
    if not state["active"]:
        raise FeedOff()


def tier_for(place):
    report = next((item for item in state["official"] if item["place"].casefold() == place.casefold()), None)
    if report:
        return "confirmed", report["source"], report["note"]
    count = sum(1 for signal in state["social"] if signal.casefold() == place.casefold())
    if count >= 3:
        return "likely", "social", f"{count} social signals"
    if count:
        return "reported", "social", f"{count} social signal{'s' if count != 1 else ''}"
    return None


def closed(place):
    tier = tier_for(place)
    return tier is not None and tier[0] in ("confirmed", "likely")


def route_for(origin):
    options = []
    for station in STATIONS:
        if closed(station["name"]):
            continue
        assigned = state["assigned"].get(station["name"], 0)
        effective_load = station["load"] + 5 * assigned
        options.append({"name": station["name"], "lines": station["lines"], "walk_minutes": station["walk"][origin], "score": station["walk"][origin] + effective_load / 20})
    options.sort(key=lambda item: item["score"])
    if not options:
        raise HTTPException(status_code=503, detail={"error": "No open subway stations are available."})
    best = options[0]
    state["assigned"][best["name"]] = state["assigned"].get(best["name"], 0) + 1
    nearest = min(STATIONS, key=lambda station: station["walk"][origin])
    if best["name"] != nearest["name"]:
        reason = "is closed" if closed(nearest["name"]) else "is overloaded"
        advice = f"{nearest['name']} {reason}. Walk {best['walk_minutes']} min to {best['name']} ({best['lines']} train)."
    else:
        advice = f"Head to {best['name']} ({best['lines']} train), {best['walk_minutes']} min walk."
    return {"origin": origin, "best": best, "alternatives": options[1:3], "advice": advice, "rideshare": {"name": RIDESHARE["name"], "walk_minutes": RIDESHARE["walk"][origin]}}


@app.post("/api/activate")
def activate(body: dict):
    event = str(body.get("event", "")).strip()
    if not event:
        raise HTTPException(status_code=400, detail={"error": "event is required"})
    state.update(active=True, event=event, official=[], assigned={})
    log(f"Activated event: {event}")
    return {"active": True, "event": event}


@app.post("/api/deactivate")
def deactivate():
    require_active()
    deleted = len(state["social"])
    state["social"].clear()
    state["active"] = False
    state["event"] = ""
    state["assigned"].clear()
    log(f"Deactivated event; deleted {deleted} social signals")
    return {"active": False, "deleted_social_signals": deleted}


@app.post("/api/official")
def official(body: dict):
    require_active()
    place = str(body.get("place", "")).strip()
    if not place:
        raise HTTPException(status_code=400, detail={"error": "place is required"})
    source = str(body.get("source", "")).strip().upper()
    if source not in {"NYPD", "DOT", "MTA", "OEM"}:
        raise HTTPException(status_code=400, detail={"error": "source must be NYPD, DOT, MTA, or OEM"})
    report = {"place": place, "source": source, "note": str(body.get("note", ""))}
    state["official"].append(report)
    log(f"Official report from {source}: {place} — {report['note']}")
    return {"place": place, "status": "confirmed", "source": source, "note": report["note"]}


@app.post("/api/social")
def social(body: dict):
    require_active()
    place = str(body.get("place", "")).strip()
    if not place:
        raise HTTPException(status_code=400, detail={"error": "place is required"})
    state["social"].append(place)
    return {"place": place, "status": tier_for(place)[0]}


@app.get("/api/feed")
def feed():
    require_active()
    places = list(dict.fromkeys([item["place"] for item in state["official"]] + state["social"]))
    closures, banners = [], []
    priority = {"confirmed": 0, "likely": 1, "reported": 2}
    for place in places:
        status, source, note = tier_for(place)
        closures.append({"place": place, "status": status, "source": source, "note": note})
        banners.append({"level": status, "text": f"{place}: {status} report — {note}"})
    closures.sort(key=lambda item: priority[item["status"]])
    banners.sort(key=lambda item: priority[item["level"]])
    loads = {s["name"]: min(100, s["load"] + 5 * state["assigned"].get(s["name"], 0)) for s in STATIONS}
    return {"event": state["event"], "closures": closures, "banners": banners, "stations": loads}


@app.get("/api/route")
def route(origin: str = Query("MSG", alias="from")):
    require_active()
    if origin not in ORIGINS:
        raise HTTPException(status_code=400, detail={"error": f"Unknown origin. Choose one of: {', '.join(ORIGINS)}"})
    return route_for(origin)


@app.post("/api/sms")
def sms(body: dict):
    require_active()
    message = str(body.get("body", "")).casefold()
    origin = "Times Sq" if "times" in message or "42" in message else "Bryant Park" if "bryant" in message or "6th" in message else "MSG"
    return {"reply": f"GetMeHome: {route_for(origin)['advice']}"[:299]}


@app.get("/api/audit")
def audit():
    return {"audit": state["audit"]}


@app.post("/api/reset")
def reset():
    state.update(active=False, event="", official=[], social=[], audit=[], assigned={})
    return {"reset": True}
