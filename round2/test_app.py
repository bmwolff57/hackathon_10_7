from fastapi.testclient import TestClient

from round2.app import app

client = TestClient(app)


def setup_function():
    client.post("/api/reset")


def test_feed_off_by_default():
    response = client.get("/api/feed")
    assert response.status_code == 403
    assert response.json()["error"] == "Feed is off. Available only during a declared event window."


def test_demo_happy_path():
    client.post("/api/activate", json={"event": "Knicks championship parade"})
    first = client.get("/api/route", params={"from": "MSG"})
    assert first.json()["best"]["name"] == "34 St-Penn Station"

    social = client.post("/api/social", json={"place": "34 St-Penn Station"})
    assert social.json()["status"] == "reported"
    second = client.get("/api/route", params={"from": "MSG"})
    assert second.json()["best"]["name"] == "34 St-Penn Station"

    client.post("/api/official", json={"place": "34 St-Penn Station", "source": "NYPD", "note": "Platform closed"})
    assert client.get("/api/feed").json()["closures"][0]["status"] == "confirmed"
    after = client.get("/api/route", params={"from": "MSG"}).json()
    assert after["best"]["name"] != "34 St-Penn Station"
    assert "closed" in after["advice"]


def test_api_rejects_bad_input():
    client.post("/api/activate", json={"event": "Test event"})
    assert client.get("/api/route", params={"from": "Mars"}).status_code == 400
    assert client.post("/api/social", json={}).status_code == 400


def test_deactivate_deletes_social():
    client.post("/api/activate", json={"event": "Test event"})
    client.post("/api/social", json={"place": "34 St-Penn Station"})
    response = client.post("/api/deactivate")
    assert response.json()["deleted_social_signals"] == 1
    assert client.get("/api/feed").status_code == 403
