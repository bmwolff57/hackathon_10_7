import pytest
from round3.app import app

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        client.post("/api/reset", headers={"X-Role": "supervisor"})
        yield client

def load(client):
    return client.post("/api/demo/load", headers={"X-Role": "dispatcher"})

def test_demo_groups_into_three_incidents(client):
    response = load(client)
    assert response.status_code == 200
    assert response.json == {"reports": 14, "incidents": 3}
    assert len(client.get("/api/incidents", headers={"X-Role": "dispatcher"}).json) == 3

def test_cardiac_stays_separate_and_dispatches_now(client):
    load(client)
    cardiac = client.get("/api/incidents/B", headers={"X-Role": "dispatcher"}).json["incident"]
    car = client.get("/api/incidents/A", headers={"X-Role": "dispatcher"}).json["incident"]
    assert cardiac["reports"] == [11]
    assert cardiac["dispatch_now"] is True
    assert 11 not in car["reports"]

def test_fight_is_consequence_of_car_incident(client):
    load(client)
    fight = client.get("/api/incidents/C", headers={"X-Role": "dispatcher"}).json["incident"]
    timeline = client.get("/api/incidents/C", headers={"X-Role": "dispatcher"}).json["timeline"]
    assert fight["parent_id"] == "A"
    assert fight["reports"] == [13, 14]
    assert timeline[0]["label"] == "consequence"

def test_only_supervisor_can_decide(client):
    load(client)
    denied = client.post("/api/incidents/A/approve", headers={"X-Role": "dispatcher"})
    assert denied.status_code == 403
    flagged = client.post("/api/incidents/A/flag", json={"reason": "Check vehicle path"}, headers={"X-Role": "dispatcher"})
    assert flagged.status_code == 200
    assert flagged.json["status"] == "flagged"
    approved = client.post("/api/incidents/A/approve", headers={"X-Role": "supervisor"})
    assert approved.status_code == 200
    assert approved.json["status"] == "approved"
    log = client.get("/api/log", headers={"X-Role": "supervisor"}).json
    assert any(entry["action"] == "approve" and entry["incident_id"] == "A" for entry in log)

def test_api_rejects_bad_input(client):
    missing_field = client.post("/api/reports", json={"ave": 0, "minute": 1, "category": "fire", "text": "smoke"}, headers={"X-Role": "dispatcher"})
    missing_role = client.post("/api/reports", json={"street": 96, "ave": 0, "minute": 1, "category": "fire", "text": "smoke"})
    assert missing_field.status_code == 400
    assert missing_role.status_code == 401
