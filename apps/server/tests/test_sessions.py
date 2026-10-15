import time

from app.main import create_app
from fastapi.testclient import TestClient

ORIGIN = "http://127.0.0.1:8765"
HEADERS = {"origin": ORIGIN}


def application(data, **kwargs):
    return create_app(
        data, origin=ORIGIN, bootstrap_secret="first-connection", **kwargs
    )


def connect(client, **extra):
    response = client.post(
        "/api/session/bootstrap",
        json={"secret": "first-connection", **extra},
        headers=HEADERS,
    )
    assert response.status_code == 200
    return {**HEADERS, "x-csrf-token": response.json()["csrfToken"]}


def test_remembered_browser_survives_restart_without_resuming_provider_budget(tmp_path):
    app = application(tmp_path)
    with TestClient(app, base_url=ORIGIN) as client:
        headers = connect(client)
        cookie = client.cookies.get("avatar_session")
        session = app.state.sessions[cookie]
        session["remainingRequests"] = 4
        session["usagePaused"] = True
        response = client.post(
            "/api/projects", json={"title": "Remembered workspace"}, headers=headers
        )
        assert response.status_code == 200
        with app.state.service.database.connect() as db:
            row = db.execute("SELECT * FROM browser_sessions").fetchone()
            assert cookie not in tuple(row)
            assert len(row["token_digest"]) == 64
    restarted = application(tmp_path)
    with TestClient(restarted, base_url=ORIGIN) as client:
        client.cookies.set("avatar_session", cookie)
        response = client.get("/api/session")
        assert response.status_code == 200
        assert response.json()["rememberBrowser"] is True
        assert response.json()["remainingRequests"] == 0
        assert response.json()["usagePaused"] is True
        assert client.get("/api/projects").json()[0]["title"] == "Remembered workspace"
        assert (
            client.post(
                "/api/projects", json={"title": "CSRF denied"}, headers=HEADERS
            ).status_code
            == 403
        )
        held_session = restarted.state.sessions[cookie]
        assert client.post("/api/auth/sign-out", headers=headers).status_code == 200
        # A provider task holding an old object cannot restore a revoked browser.
        held_session["usagePaused"] = False
        assert client.get("/api/session").status_code == 401
    with TestClient(application(tmp_path), base_url=ORIGIN) as client:
        client.cookies.set("avatar_session", cookie)
        assert client.get("/api/session").status_code == 401


def test_unremembered_tampered_expired_and_other_mode_sessions_cannot_resume(tmp_path):
    app = application(tmp_path)
    with TestClient(app, base_url=ORIGIN) as client:
        connect(client, rememberBrowser=False)
        temporary_cookie = client.cookies.get("avatar_session")
        assert client.get("/api/session").json()["rememberBrowser"] is False
    with TestClient(application(tmp_path), base_url=ORIGIN) as client:
        client.cookies.set("avatar_session", temporary_cookie)
        assert client.get("/api/session").status_code == 401
        client.cookies.clear()
        headers = connect(client)
        cookie = client.cookies.get("avatar_session")
        assert (
            client.post(
                "/api/session/remember",
                json={"rememberBrowser": False},
                headers=headers,
            ).status_code
            == 200
        )
        assert client.get("/api/session").json()["rememberBrowser"] is False
        assert (
            client.post(
                "/api/session/remember", json={"rememberBrowser": True}, headers=headers
            ).status_code
            == 200
        )
    with TestClient(
        application(tmp_path, execution_mode="codex_local"), base_url=ORIGIN
    ) as client:
        client.cookies.set("avatar_session", cookie)
        assert client.get("/api/session").status_code == 401
    restarted = application(tmp_path)
    with TestClient(restarted, base_url=ORIGIN) as client:
        client.cookies.set("avatar_session", cookie[:-2] + "xx")
        assert client.get("/api/session").status_code == 401
        client.cookies.set("avatar_session", cookie)
        assert client.get("/api/session").status_code == 200
        restarted.state.sessions[cookie]["expires"] = time.time() - 1
        assert client.get("/api/session").status_code == 401
    with TestClient(application(tmp_path), base_url=ORIGIN) as client:
        client.cookies.set("avatar_session", cookie)
        assert client.get("/api/session").status_code == 401


def test_browser_pairing_opens_only_on_local_os_without_disclosing_capability(tmp_path):
    opened = []

    def opener(url):
        opened.append(url)
        return True

    with TestClient(
        application(tmp_path, browser_opener=opener), base_url=ORIGIN
    ) as client:
        assert client.post("/api/session/open-browser", json={}).status_code == 403
        assert (
            client.post(
                "/api/session/open-browser",
                json={},
                headers={"origin": "https://attacker.test"},
            ).status_code
            == 403
        )
        assert (
            client.post(
                "/api/session/open-browser",
                json={},
                headers={**HEADERS, "host": "attacker.test"},
            ).status_code
            == 403
        )
        assert opened == []
        response = client.post("/api/session/open-browser", json={}, headers=HEADERS)
        assert response.status_code == 200 and response.json() == {"opened": True}
        assert response.cookies.get("avatar_session") is None
        assert client.get("/api/session").status_code == 401
        assert opened == [ORIGIN + "/#launch=first-connection"]
        assert "first-connection" not in response.text
        assert (
            client.post(
                "/api/session/open-browser", json={}, headers=HEADERS
            ).status_code
            == 429
        )
    with TestClient(
        application(tmp_path / "no-desktop", browser_opener=lambda _: False),
        base_url=ORIGIN,
    ) as client:
        response = client.post("/api/session/open-browser", json={}, headers=HEADERS)
        assert response.status_code == 503
        assert client.get("/api/session").status_code == 401
