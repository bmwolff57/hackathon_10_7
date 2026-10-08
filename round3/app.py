from copy import deepcopy
from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__, static_folder="static")
CATEGORIES = {"reckless", "noise", "property", "crash", "fire", "medical", "fight"}
COMPAT = {"reckless", "noise", "property", "crash", "fire"}
NEEDS = {"crash": "EMS", "fire": "FDNY engine", "reckless": "NYPD patrol", "fight": "NYPD patrol x2", "medical": "EMS"}
POOLS = {"EMS": ["A-22", "A-31"], "FDNY engine": ["E-74"], "NYPD patrol": ["P-7", "P-9", "P-12"], "NYPD patrol x2": ["P-7", "P-9", "P-12"]}
CRITICAL = ("not breathing", "collapsed", "trapped", "still in the car", "gun", "knife")
SEED = [
 {"minute":2,"source":"911","street":86,"ave":0,"category":"reckless","vehicle":"silver sedan","text":"car flying north on Broadway","distress":2},
 {"minute":3,"source":"911","street":88,"ave":0,"category":"reckless","vehicle":"silver sedan","text":"silver car speeding, almost hit me","distress":3},
 {"minute":3,"source":"311","street":89,"ave":0,"category":"noise","vehicle":"","text":"really loud engine outside","distress":1},
 {"minute":4,"source":"911","street":91,"ave":0,"category":"reckless","vehicle":"silver sedan","text":"silver sedan running red lights","distress":3},
 {"minute":5,"source":"311","street":93,"ave":0,"category":"property","vehicle":"silver sedan","text":"a car hit my parked car and kept going","distress":2},
 {"minute":6,"source":"911","street":96,"ave":0,"category":"crash","vehicle":"silver sedan","text":"car crashed into a pole","distress":3},
 {"minute":6,"source":"911","street":96,"ave":0,"category":"fire","vehicle":"silver sedan","text":"the car is on fire","distress":4},
 {"minute":6,"source":"911","street":96,"ave":0,"category":"fire","vehicle":"","text":"car on fire at 96th and Broadway","distress":4},
 {"minute":6,"source":"form","street":96,"ave":0,"category":"fire","vehicle":"","text":"photo: car burning by pole","distress":3},
 {"minute":7,"source":"911","street":96,"ave":0,"category":"fire","vehicle":"silver sedan","text":"someone is still in the car","distress":5},
 {"minute":8,"source":"911","street":94,"ave":0,"category":"medical","vehicle":"","text":"my father collapsed, not breathing","distress":5},
 {"minute":9,"source":"radio","street":96,"ave":0,"category":"fire","vehicle":"silver sedan","text":"Engine 74 on scene, one occupant removed","distress":2},
 {"minute":14,"source":"911","street":96,"ave":1,"category":"fight","vehicle":"","text":"another group fighting across the street","distress":3},
 {"minute":15,"source":"911","street":96,"ave":1,"category":"fight","vehicle":"","text":"big fight on Amsterdam","distress":3},
]
state = {"reports": {}, "incidents": {}, "log": [], "next_report": 1, "next_incident": 0, "minute": 0}

@app.before_request
def role_guard():
    if request.path.startswith("/api/"):
        role = request.headers.get("X-Role")
        if role not in {"calltaker", "dispatcher", "supervisor"}:
            return jsonify(error="Missing or unknown role."), 401
        request.role = role

def _supervisor_error():
    if request.role != "supervisor":
        return jsonify(error="Only the dispatch supervisor can make this decision."), 403
    return None

def _distance(report, point):
    return abs(report["street"] - point[0]) + 3 * abs(report["ave"] - point[1])

def _reports(i):
    return [state["reports"][rid] for rid in i["reports"]]

def _open():
    return [i for i in state["incidents"].values() if i["status"] != "sent_back"]

def _new(report, parent_id=None):
    state["next_incident"] += 1
    iid = chr(64 + state["next_incident"])
    labels = {"reckless":"Silver sedan incident","medical":"Cardiac emergency","fight":"Fight","crash":"Vehicle crash","fire":"Vehicle fire","noise":"Noise report","property":"Property damage"}
    state["incidents"][iid] = {"id":iid,"title":f"{labels[report['category']]} — W {report['street']}th St","categories":set(),"reports":[],"footprint":[],"first_minute":report["minute"],"last_minute":report["minute"],"parent_id":parent_id,"needs":[],"status":"proposed","dispatch_now":False,"priority":0,"flags":[],"plan":[]}
    return state["incidents"][iid]

def _matches(i, r):
    if r["category"] == "medical" or r["minute"] - i["last_minute"] > 15:
        return False
    old = _reports(i)
    vehicle = bool(r.get("vehicle")) and any(x.get("vehicle","").casefold() == r["vehicle"].casefold() for x in old)
    # A matching vehicle can extend a moving incident's path beyond the local join radius.
    if vehicle:
        return True
    if not any(_distance(r, p) <= 2 for p in i["footprint"]):
        return False
    compatible = r["category"] in COMPAT and any(c in COMPAT for c in i["categories"])
    fight = r["category"] == "fight" and "fight" in i["categories"]
    return vehicle or compatible or fight

def _audit(action, iid, reason, minute=None):
    state["log"].append({"minute":state["minute"] if minute is None else minute,"role":request.role,"action":action,"incident_id":iid,"reason":reason})

def _attach(i, r, label, reason):
    r.update(label=label,reason=reason,incident_id=i["id"])
    i["reports"].append(r["id"])
    point=[r["street"],r["ave"]]
    if point not in i["footprint"]: i["footprint"].append(point)
    i["categories"].add(r["category"])
    i["first_minute"]=min(i["first_minute"],r["minute"])
    i["last_minute"]=max(i["last_minute"],r["minute"])
    i["dispatch_now"] = i["dispatch_now"] or r["critical"]
    need=NEEDS.get(r["category"])
    if need and need not in i["needs"]: i["needs"].append(need)
    if r["source"]=="radio" and "on scene" in r["text"].casefold() and need in i["needs"]: i["needs"].remove(need)

def _rebuild(i):
    reports=_reports(i)
    i["categories"]=set(); i["footprint"]=[]; i["needs"]=[]; i["dispatch_now"]=False
    if not reports: return
    i["first_minute"]=min(r["minute"] for r in reports); i["last_minute"]=max(r["minute"] for r in reports)
    for r in reports:
        point=[r["street"],r["ave"]]
        if point not in i["footprint"]: i["footprint"].append(point)
        i["categories"].add(r["category"]); i["dispatch_now"] |= r["critical"]
        need=NEEDS.get(r["category"])
        if need and need not in i["needs"]: i["needs"].append(need)
    for r in reports:
        need=NEEDS.get(r["category"])
        if r["source"]=="radio" and "on scene" in r["text"].casefold() and need in i["needs"]: i["needs"].remove(need)

def _recompute():
    for i in state["incidents"].values():
        rs=_reports(i)
        recent=sum(1 for r in rs if state["minute"]-r["minute"]<=5)
        peak=max((r["distress"] for r in rs),default=0)
        i["priority"]=(100 if i["dispatch_now"] else 0)+15*peak+2*recent
    used=set()
    for i in sorted(state["incidents"].values(),key=lambda x:(-x["priority"],x["id"])):
        plan=[]; met=set()
        for need in i["needs"]:
            count=2 if need=="NYPD patrol x2" else 1
            assigned=0
            for unit in POOLS.get(need,[]):
                if unit not in used:
                    used.add(unit); plan.append(f"{unit} ({need})"); met.add(need); assigned+=1
                    if assigned==count: break
        i["plan"]=plan
        if any(n not in met for n in i["needs"]): i["priority"]+=10

def _process(data):
    r=dict(data); r["id"]=state["next_report"]; state["next_report"]+=1
    r.setdefault("caller",""); r.setdefault("vehicle",""); r.setdefault("distress",1)
    text=r["text"].casefold(); r["critical"]=any(term in text for term in CRITICAL)
    state["minute"]=max(state["minute"],r["minute"])
    opens=_open(); chosen=None; label="separate"; reason="no matching open incident within time and location limits"
    if r["caller"]:
        for i in opens:
            if any(old.get("caller")==r["caller"] for old in _reports(i)):
                chosen=i; label="update"; reason=f"same caller '{r['caller']}'"; break
    phrases=("another group","different group","started because")
    if chosen is None and r["category"]=="fight" and any(p in text for p in phrases):
        parents=[i for i in opens if abs(r["minute"]-i["last_minute"])<=15 and any(_distance(r,p)<=3 for p in i["footprint"])]
        if parents:
            parent=min(parents,key=lambda i:(min(_distance(r,p) for p in i["footprint"]),i["id"]))
            chosen=_new(r,parent["id"]); label="consequence"; reason=f"new fight linked to nearby incident #{parent['id']}"
    if chosen is None:
        for i in opens:
            if _matches(i,r):
                chosen=i; point=[r["street"],r["ave"]]
                adds=r["category"] not in i["categories"] or point not in i["footprint"] or r["critical"]
                label="update" if adds else "duplicate"
                blocks=min(_distance(r,p) for p in i["footprint"]); elapsed=abs(r["minute"]-i["last_minute"])
                reason=f"same vehicle '{r['vehicle']}', {blocks} blocks, {elapsed} min later" if r["vehicle"] else f"compatible {r['category']} report, {blocks} blocks, {elapsed} min later"
                break
    if chosen is None: chosen=_new(r)
    _attach(chosen,r,label,reason); state["reports"][r["id"]]=r
    _audit(f"label:{label}",chosen["id"],reason,r["minute"]); _recompute()
    return {"report_id":r["id"],"label":label,"reason":reason,"incident_id":chosen["id"]}

def _reset():
    state.update(reports={},incidents={},log=[],next_report=1,next_incident=0,minute=0)

def _serial(i):
    out=deepcopy(i); out["categories"]=sorted(out["categories"]); return out

def _ranked():
    return sorted(state["incidents"].values(),key=lambda i:(-i["priority"],i["id"]))

@app.get("/")
def home():
    return send_from_directory("static","index.html")

@app.post("/api/reset")
def reset():
    _reset(); return jsonify(reset=True)

@app.post("/api/demo/load")
def demo_load():
    _reset()
    for item in SEED: _process(dict(item))
    return jsonify(reports=len(state["reports"]),incidents=len(state["incidents"]))

@app.post("/api/reports")
def add_report():
    data=request.get_json(silent=True) or {}
    required=("street","ave","minute","category","text")
    if any(k not in data or data[k] is None or data[k]=="" for k in required):
        return jsonify(error="street, ave, minute, category, and text are required."),400
    try:
        for k in ("street","ave","minute"): data[k]=int(data[k])
        data["distress"]=int(data.get("distress",1))
    except (TypeError,ValueError):
        return jsonify(error="street, ave, minute, and distress must be integers."),400
    if data["category"] not in CATEGORIES or data.get("source","form") not in {"911","311","form","radio"} or not isinstance(data["text"],str):
        return jsonify(error="invalid source, category, or text."),400
    data.setdefault("source","form")
    return jsonify(_process(data)),201

@app.get("/api/incidents")
def incidents():
    out=[]
    for i in _ranked():
        recent=sum(1 for r in _reports(i) if state["minute"]-r["minute"]<=5)
        out.append({"id":i["id"],"title":i["title"],"status":i["status"],"priority":i["priority"],"dispatch_now":i["dispatch_now"],"report_count":len(i["reports"]),"needs":i["needs"],"parent_id":i["parent_id"],"trend":"up" if recent>=2 else "flat"})
    return jsonify(out)

@app.get("/api/incidents/<iid>")
def detail(iid):
    i=state["incidents"].get(iid)
    if not i: return jsonify(error="incident not found."),404
    timeline=[{k:r[k] for k in ("minute","source","text","label","reason")} for r in _reports(i)]
    return jsonify(incident=_serial(i),timeline=timeline)

@app.get("/api/calltaker/banner")
def banner():
    try: r={"street":int(request.args["street"]),"ave":int(request.args["ave"]),"minute":int(request.args["minute"]),"category":request.args["category"]}
    except (KeyError,ValueError): return jsonify(error="street, ave, minute, and category are required."),400
    found=[i for i in _open() if _matches(i,r)]
    if not found: return jsonify(likely_incident=None,others_on_it=0,known=[],unknown=["vehicle description","caller identity","what happened next"])
    i=min(found,key=lambda x:(min(_distance(r,p) for p in x["footprint"]),-x["priority"]))
    vehicles=sorted({x.get("vehicle") for x in _reports(i) if x.get("vehicle")})
    known=sorted(i["categories"])+[f"W {s}th St, avenue {a}" for s,a in i["footprint"]]
    if vehicles: known.append("vehicle: "+", ".join(vehicles))
    return jsonify(likely_incident=i["id"],others_on_it=max(0,len(i["reports"])-1),known=known,unknown=["caller identity","number of people involved"])

@app.post("/api/incidents/<iid>/flag")
def flag(iid):
    i=state["incidents"].get(iid)
    if not i: return jsonify(error="incident not found."),404
    reason=str((request.get_json(silent=True) or {}).get("reason","Needs supervisor review"))
    i["flags"].append({"role":request.role,"reason":reason}); i["status"]="flagged"
    _audit("flag",iid,reason); _recompute()
    return jsonify(incident_id=iid,status=i["status"],flags=i["flags"])

@app.get("/api/review")
def review():
    if request.role!="supervisor": return jsonify(error="Only the dispatch supervisor can make this decision."),403
    return jsonify(incidents=[{**_serial(i),"report_count":len(i["reports"])} for i in _ranked() if i["status"] in {"proposed","flagged"}])

@app.post("/api/incidents/<iid>/approve")
def approve(iid):
    if err:=_supervisor_error(): return err
    i=state["incidents"].get(iid)
    if not i: return jsonify(error="incident not found."),404
    i["status"]="approved"; _audit("approve",iid,"Approved by dispatch supervisor"); _recompute()
    return jsonify(incident_id=iid,status=i["status"],plan=i["plan"])

@app.post("/api/incidents/<iid>/split")
def split(iid):
    if err:=_supervisor_error(): return err
    i=state["incidents"].get(iid); ids=(request.get_json(silent=True) or {}).get("report_ids",[])
    if not i: return jsonify(error="incident not found."),404
    if not ids or any(rid not in i["reports"] for rid in ids): return jsonify(error="report_ids must identify reports in this incident."),400
    moved=[state["reports"][rid] for rid in ids]; new=_new(moved[0])
    for r in moved:
        i["reports"].remove(r["id"]); r["incident_id"]=new["id"]; new["reports"].append(r["id"])
        p=[r["street"],r["ave"]]
        if p not in new["footprint"]: new["footprint"].append(p)
        new["categories"].add(r["category"]); new["first_minute"]=min(new["first_minute"],r["minute"]); new["last_minute"]=max(new["last_minute"],r["minute"])
        new["dispatch_now"] |= r["critical"]
        need=NEEDS.get(r["category"])
        if need and need not in new["needs"]: new["needs"].append(need)
    _rebuild(i); _rebuild(new)
    _audit("split",iid,f"Moved report IDs {ids} to incident #{new['id']}"); _recompute()
    return jsonify(new_incident_id=new["id"],moved_report_ids=ids)

@app.post("/api/incidents/<iid>/send_back")
def send_back(iid):
    if err:=_supervisor_error(): return err
    i=state["incidents"].get(iid)
    if not i: return jsonify(error="incident not found."),404
    reason=str((request.get_json(silent=True) or {}).get("reason","Please review this grouping"))
    i["status"]="sent_back"; _audit("send_back",iid,reason); _recompute()
    return jsonify(incident_id=iid,status="sent_back")

@app.get("/api/log")
def get_log():
    return jsonify(state["log"])
