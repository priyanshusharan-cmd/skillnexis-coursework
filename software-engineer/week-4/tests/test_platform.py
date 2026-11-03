"""Week 4 additions: real-time events, monitoring, logging, web UI."""
import json
import logging

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from blogly.app import create_app

SECRET = "test-secret-" + "x" * 32


@pytest.fixture
def client(tmp_path):
    return TestClient(create_app(db_path=str(tmp_path / "t.db"), secret=SECRET, rate_per_min=1000, login_per_min=1000))


def signup(c, name="priya"):
    c.post("/auth/register", json={"username": name, "password": "correct-horse-1"})
    tok = c.post("/auth/login", json={"username": name, "password": "correct-horse-1"}).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


def test_websocket_receives_live_events(client):
    h = signup(client)
    with client.websocket_connect("/ws") as ws:
        assert ws.receive_json() == {"type": "hello", "clients": 1}
        post = client.post("/posts", json={"title": "Live", "body": "now"}, headers=h).json()
        ev = ws.receive_json()
        assert ev["type"] == "post_created" and ev["post"]["title"] == "Live" and ev["post"]["author"] == "priya"
        client.post(f"/posts/{post['id']}/comments", json={"body": "hi"}, headers=h)
        ev = ws.receive_json()
        assert ev["type"] == "comment_added" and ev["comment"]["body"] == "hi"
        client.put(f"/posts/{post['id']}/like", headers=h)
        assert ws.receive_json() == {"type": "likes_changed", "post_id": post["id"], "likes": 1}
        client.delete(f"/posts/{post['id']}/like", headers=h)
        assert ws.receive_json() == {"type": "likes_changed", "post_id": post["id"], "likes": 0}
        client.delete(f"/posts/{post['id']}", headers=h)
        assert ws.receive_json() == {"type": "post_deleted", "post_id": post["id"]}
        ws.send_text("ping")
        assert ws.receive_json() == {"type": "pong"}


def test_two_clients_both_get_events_and_gauge_tracks_them(client):
    h = signup(client)
    with client.websocket_connect("/ws") as a, client.websocket_connect("/ws") as b:
        a.receive_json(), b.receive_json()
        assert client.get("/api/status").json()["websocket_clients"] == 2
        client.post("/posts", json={"title": "Both", "body": "see this"}, headers=h)
        assert a.receive_json()["post"]["title"] == b.receive_json()["post"]["title"] == "Both"
    assert client.get("/api/status").json()["websocket_clients"] == 0


def test_websocket_connection_cap(tmp_path):
    app = create_app(db_path=str(tmp_path / "t.db"), secret=SECRET)
    app.state.hub.max_clients = 1
    c = TestClient(app)
    with c.websocket_connect("/ws") as first:
        first.receive_json()
        with pytest.raises(WebSocketDisconnect):
            with c.websocket_connect("/ws") as second:
                second.receive_json()


def test_prometheus_metrics_use_route_templates(client):
    h = signup(client)
    pid = client.post("/posts", json={"title": "T", "body": "B"}, headers=h).json()["id"]
    for _ in range(3):
        client.get(f"/posts/{pid}")
    client.get("/posts/999")
    text = client.get("/metrics").text
    assert 'blogly_http_requests_total{method="GET",route="/posts/{post_id}",status="200"} 3.0' in text
    assert 'blogly_http_requests_total{method="GET",route="/posts/{post_id}",status="404"} 1.0' in text
    assert "blogly_http_request_duration_seconds_bucket" in text and "blogly_signups_total 1.0" in text
    assert f'route="/posts/{pid}"' not in text  # raw ids would explode label cardinality
    assert 'blogly_events_published_total{type="post_created"} 1.0' in text


def test_metrics_token_protects_metrics(tmp_path):
    c = TestClient(create_app(db_path=str(tmp_path / "t.db"), secret=SECRET, metrics_token="m-token"))
    assert c.get("/metrics").status_code == 401
    assert c.get("/metrics", headers={"Authorization": "Bearer m-token"}).status_code == 200


def test_status_summary_counts_errors_and_latency(client):
    for _ in range(4):
        client.get("/health")
    client.get("/posts/12345")
    s = client.get("/api/status").json()
    assert s["requests_total"] >= 5 and s["errors_5xx"] == 0 and s["error_rate"] == 0
    assert s["p95_latency_ms_upper_bound"] is not None and s["uptime_seconds"] >= 0
    assert ["GET /health", 4] in s["top_routes"]


def test_unhandled_error_is_logged_and_counted_as_500(client, caplog):
    def boom():
        raise RuntimeError("kaboom")

    client.app.add_api_route("/boom", boom)
    caplog.set_level(logging.INFO, logger="blogly")
    logging.getLogger("blogly").propagate = True
    r = TestClient(client.app, raise_server_exceptions=False).get("/boom")
    assert r.status_code == 500
    assert client.get("/api/status").json()["errors_5xx"] == 1
    line = json.loads([rec.getMessage() for rec in caplog.records if "/boom" in rec.getMessage()][-1])
    assert line["status"] == 500 and line["level"] == "error" and len(line["request_id"]) == 16


def test_request_id_is_echoed_or_generated(client, caplog):
    caplog.set_level(logging.INFO, logger="blogly")
    logging.getLogger("blogly").propagate = True
    assert client.get("/health", headers={"X-Request-ID": "trace-123"}).headers["X-Request-ID"] == "trace-123"
    assert len(client.get("/health").headers["X-Request-ID"]) == 16
    logged = [json.loads(r.getMessage()) for r in caplog.records if r.name == "blogly"]
    assert any(e["request_id"] == "trace-123" and e["route"] == "/health" and "duration_ms" in e for e in logged)


def test_web_ui_and_status_page_are_served(client):
    home = client.get("/")
    assert home.status_code == 200 and "<title>Blogly</title>" in home.text
    assert client.get("/status").status_code == 200
    assert "textContent" in client.get("/static/app.js").text
    assert client.get("/static/styles.css").headers["content-type"].startswith("text/css")


def test_ui_and_monitoring_are_not_rate_limited(tmp_path):
    c = TestClient(create_app(db_path=str(tmp_path / "t.db"), secret=SECRET, rate_per_min=2))
    assert all(c.get(p).status_code == 200 for p in ["/", "/status", "/static/app.js", "/metrics", "/health"] * 3)
    assert [c.get("/posts").status_code for _ in range(3)] == [200, 200, 429]


def test_static_files_get_a_bounded_route_label(client):
    client.get("/static/app.js")
    client.get("/static/does-not-exist.js")
    text = client.get("/metrics").text
    assert 'route="/static/*",status="200"' in text and 'route="/static/*",status="404"' in text
