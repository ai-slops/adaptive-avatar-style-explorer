import asyncio
import json
import stat
import time
from urllib.parse import parse_qs, urlsplit

import httpx
import jwt
import pytest
from app.common import DomainError, uid
from app.contracts import JobInput
from app.jobs import Jobs
from app.providers.siwc import ISSUER, RESOURCE, SIWC, ProviderError
from app.storage.assets import Assets
from cryptography.hazmat.primitives.asymmetric import rsa


@pytest.fixture(scope="module")
def signing_key():
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


class MockOpenAI:
    def __init__(self, key):
        self.key = key
        self.nonce = ""
        self.subject = "alice-sub"
        self.scope = "openid resource.invoke chatgpt.tokens.use.direct"
        self.requests = []
        self.completed = True
        self.usage_limit = False
        self.client_id = "oaiapp_alice"

    def handler(self, request):
        self.requests.append(request)
        path = request.url.path
        if path == "/.well-known/openid-configuration":
            return httpx.Response(
                200,
                json={
                    "issuer": ISSUER,
                    "jwks_uri": ISSUER + "/.well-known/jwks.json",
                    "revocation_endpoint": ISSUER + "/api/accounts/oauth/revoke",
                },
            )
        if path == "/.well-known/jwks.json":
            jwk = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(self.key.public_key()))
            return httpx.Response(
                200,
                json={"keys": [{**jwk, "kid": "test", "use": "sig", "alg": "RS256"}]},
            )
        if path == "/api/accounts/oauth/token":
            form = parse_qs(request.content.decode())
            assert form["client_id"] == [self.client_id]
            claims = {
                "iss": ISSUER,
                "sub": self.subject,
                "aud": self.client_id,
                "exp": int(time.time()) + 3600,
                "iat": int(time.time()),
                "nonce": self.nonce,
                "email": "same@example.test",
            }
            token = jwt.encode(
                claims, self.key, algorithm="RS256", headers={"kid": "test"}
            )
            return httpx.Response(
                200,
                json={
                    "access_token": "oauth-test",
                    "refresh_token": "rotated-test",
                    "id_token": token,
                    "scope": self.scope,
                    "expires_in": 3600,
                },
            )
        if path == "/api/accounts/oauth/revoke":
            return httpx.Response(200)
        assert request.headers["authorization"] == "Bearer oauth-test"
        if path == "/v1/models":
            return httpx.Response(
                200,
                json={
                    "models": [
                        {"slug": "hidden", "visibility": "hidden"},
                        {
                            "slug": "admitted-z",
                            "display_name": "Model Z",
                            "visibility": "list",
                        },
                        {
                            "slug": "admitted-a",
                            "display_name": "Model A",
                            "visibility": "list",
                        },
                    ]
                },
            )
        if path == "/v1/responses":
            payload = json.loads(request.content)
            assert set(payload) == {"model", "instructions", "input", "store", "stream"}
            assert payload["stream"] and payload["store"] is False
            assert isinstance(payload["input"], list)
            if self.usage_limit:
                return httpx.Response(
                    429,
                    json={
                        "detail": {"code": "subscription_sharing_usage_limit_exceeded"}
                    },
                    headers={"x-request-id": "request-test"},
                )
            event = {
                "type": "response.completed",
                "response": {
                    "status": "completed",
                    "output": [
                        {
                            "type": "message",
                            "content": [
                                {
                                    "type": "output_text",
                                    "text": json.dumps(
                                        {
                                            "summary": "An observed design hypothesis.",
                                            "observations": [],
                                            "findings": [],
                                            "nextActions": [],
                                        }
                                    ),
                                }
                            ],
                        }
                    ],
                },
            }
            text = (
                "data: " + json.dumps(event) + "\n\n"
                if self.completed
                else 'data: {"type":"response.output_text.delta","delta":"partial"}\n\n'
            )
            return httpx.Response(
                200, text=text, headers={"content-type": "text/event-stream"}
            )
        raise AssertionError("Unapproved outbound route: " + str(request.url))


def connect(service, tmp_path, signing_key):
    mock = MockOpenAI(signing_key)
    provider = SIWC(
        service,
        tmp_path / "credentials",
        "http://127.0.0.1:8765",
        transport=httpx.MockTransport(mock.handler),
    )
    attempt = provider.start("session")
    query = parse_qs(urlsplit(attempt["authorizationUrl"]).query)
    mock.nonce = query["nonce"][0]
    result = provider.callback(
        query["state"][0], code="authorized", client_id=mock.client_id
    )
    return provider, mock, result


def test_oauth_pkce_state_identity_scope_and_credentials(
    service, tmp_path, signing_key
):
    provider, mock, result = connect(service, tmp_path, signing_key)
    assert result["grantState"] == "plan_enabled"
    reg = provider.registration(result["registrationId"])
    assert reg["subject"] == "alice-sub"
    assert (
        stat.S_IMODE(provider.credentials.path(result["registrationId"]).stat().st_mode)
        == 0o600
    )
    assert "access_token" not in json.dumps(provider.list_registrations())
    attempt = provider.start("session", result["registrationId"])
    query = parse_qs(urlsplit(attempt["authorizationUrl"]).query)
    assert query["client_id"] == ["oaiapp_alice"] and "agent_name_hint" not in query
    assert "id_token_hint" in query and query["code_challenge_method"] == ["S256"]
    assert query["ext_agent_host_id"][0].startswith("urn:uuid:")
    assert query["redirect_uri"] == ["http://127.0.0.1:8765/auth/callback"]
    mock.nonce = query["nonce"][0]
    mock.subject = "wrong-user"
    with pytest.raises(DomainError, match="identity changed"):
        provider.callback(query["state"][0], code="code")
    with pytest.raises(DomainError, match="state"):
        provider.callback(query["state"][0], code="replayed")
    assert provider.credentials.read(result["registrationId"])["subject"] == "alice-sub"
    assert (
        provider.credentials.host_id
        == SIWC(
            service, tmp_path / "credentials", "http://127.0.0.1:8765"
        ).credentials.host_id
    )
    asyncio.run(provider.close())


def test_declined_invalid_nonce_and_identity_only(service, tmp_path, signing_key):
    mock = MockOpenAI(signing_key)
    provider = SIWC(
        service,
        tmp_path,
        "http://127.0.0.1:8765",
        transport=httpx.MockTransport(mock.handler),
    )
    state = parse_qs(urlsplit(provider.start("s")["authorizationUrl"]).query)["state"][
        0
    ]
    with pytest.raises(DomainError, match="declined"):
        provider.callback(state, error="access_denied")
    assert not mock.requests
    state = parse_qs(urlsplit(provider.start("s")["authorizationUrl"]).query)["state"][
        0
    ]
    with pytest.raises(DomainError, match="nonce"):
        provider.callback(state, code="code", client_id=mock.client_id)
    query = parse_qs(urlsplit(provider.start("s")["authorizationUrl"]).query)
    mock.nonce, mock.scope = query["nonce"][0], "openid"
    result = provider.callback(query["state"][0], code="code", client_id=mock.client_id)
    assert result["grantState"] == "identity_only"
    with pytest.raises(DomainError, match="permission"):
        provider.access_token(result["principalId"], result["registrationId"])
    asyncio.run(provider.close())


def test_signature_audience_expiry_and_discovery_are_validated(
    service, tmp_path, signing_key
):
    provider, mock, result = connect(service, tmp_path, signing_key)
    good = provider.credentials.read(result["registrationId"])["id_token"]
    claims = jwt.decode(good, options={"verify_signature": False})
    for changes in (
        {"aud": "another-client"},
        {"exp": 1},
        {"iss": "https://attacker.test"},
        {"nonce": "other"},
    ):
        token = jwt.encode(
            {**claims, **changes},
            signing_key,
            algorithm="RS256",
            headers={"kid": "test"},
        )
        with pytest.raises(DomainError):
            provider.validate_identity(token, mock.client_id, mock.nonce)
    bad = jwt.encode(claims, "not-rsa-" * 8, algorithm="HS256")
    with pytest.raises(DomainError):
        provider.validate_identity(bad, mock.client_id, mock.nonce)
    with pytest.raises(DomainError, match="Untrusted"):
        provider.discovered_url({"jwks_uri": "https://attacker.test/jwks"}, "jwks_uri")
    asyncio.run(provider.close())


def test_refresh_is_rotated_and_registration_scoped(service, tmp_path, signing_key):
    provider, _mock, result = connect(service, tmp_path, signing_key)
    principal, reg = result["principalId"], result["registrationId"]
    saved = provider.credentials.read(reg)
    provider.credentials.write(reg, {**saved, "expires_at": 0})
    assert provider.access_token(principal, reg) == "oauth-test"
    assert provider.credentials.read(reg)["refresh_token"] == "rotated-test"
    with pytest.raises(DomainError, match="another user"):
        provider.access_token("bob", reg)
    assert provider.disconnect(principal, reg)["remoteRevocationConfirmed"]
    assert provider.registration(reg)["grant_state"] == "disconnected"
    assert not provider.credentials.path(reg).exists()
    asyncio.run(provider.close())


def test_catalog_and_terminal_stream_no_key_fallback(
    service, tmp_path, signing_key, monkeypatch
):
    monkeypatch.setenv("OPENAI_API_KEY", "must-never-be-used")
    provider, mock, result = connect(service, tmp_path, signing_key)

    async def check():
        models = await provider.models(result["principalId"], result["registrationId"])
        assert [m["slug"] for m in models] == ["admitted-z", "admitted-a"]
        args = (
            result["principalId"],
            result["registrationId"],
            "admitted-z",
            "summarize_preferences",
            {"outputSchema": {}},
        )
        output = await provider.reason(*args)
        assert output["summary"]
        mock.completed = False
        with pytest.raises(ProviderError, match="interrupted_stream"):
            await provider.reason(*args)
        mock.usage_limit = True
        with pytest.raises(ProviderError, match="usage_limit_exceeded"):
            await provider.reason(*args)
        for task in ("generate_image", "render", "shell", "proxy"):
            with pytest.raises(DomainError):
                await provider.reason(*args[:3], task, {})
        await provider.close()

    asyncio.run(check())
    assert {str(r.url) for r in mock.requests} <= {
        ISSUER + "/.well-known/openid-configuration",
        ISSUER + "/.well-known/jwks.json",
        ISSUER + "/api/accounts/oauth/token",
        RESOURCE + "/models",
        RESOURCE + "/responses",
    }


def test_jobs_budget_stale_usage_and_payer(service, tmp_path, signing_key):
    provider, mock, result = connect(service, tmp_path, signing_key)
    principal, reg = result["principalId"], result["registrationId"]
    p = service.create_project(principal, "Account-bound")["project_id"]
    from app.contracts import CanonicalInput, DesignInput

    v = service.create_design(
        principal, p, DesignInput(title="Idea", spec=CanonicalInput())
    )["version_id"]
    sessions = {
        "session": {"principal": principal, "registration": reg, "remainingRequests": 0}
    }
    jobs = Jobs(service, provider, Assets(service, tmp_path / "images"), sessions)
    data = JobInput(
        requestId=uid(),
        task="summarize_preferences",
        versionId=v,
        model="admitted-z",
        expectedEventSequence=1,
    )

    async def check():
        with pytest.raises(DomainError, match="budget"):
            await jobs.enqueue("session", p, data)
        sessions["session"]["remainingRequests"] = 3
        job = await jobs.enqueue("session", p, data)
        await asyncio.gather(*list(jobs.tasks.values()))
        current = jobs.read(principal, p, job["jobId"])
        assert current["state"] == "succeeded"
        assert current["result"]["geometricVerification"] == "none"
        again = await jobs.enqueue("session", p, data)
        assert (
            again["jobId"] == job["jobId"]
            and sessions["session"]["remainingRequests"] == 2
        )
        with pytest.raises(DomainError):
            jobs.read("bob", p, job["jobId"])
        # Mutations after enqueue make the result stale rather than current.
        new = await jobs.enqueue(
            "session", p, data.model_copy(update={"requestId": uid()})
        )
        with service.database.connect() as db:
            db.execute(
                "UPDATE projects SET event_sequence=event_sequence+1 WHERE project_id=?",
                (p,),
            )
        await asyncio.gather(*list(jobs.tasks.values()))
        assert jobs.read(principal, p, new["jobId"])["state"] == "stale"
        mock.usage_limit = True
        paused = await jobs.enqueue(
            "session",
            p,
            data.model_copy(update={"requestId": uid(), "expectedEventSequence": 2}),
        )
        await asyncio.gather(*list(jobs.tasks.values()))
        assert jobs.read(principal, p, paused["jobId"])["state"] == "failed"
        assert (
            sessions["session"]["usagePaused"]
            and sessions["session"]["remainingRequests"] == 0
        )
        await jobs.close()
        await provider.close()

    asyncio.run(check())


def test_api_account_switch_isolates_projects_and_explicit_offline_binding(
    tmp_path, signing_key
):
    from app.main import create_app
    from fastapi.testclient import TestClient

    mock = MockOpenAI(signing_key)
    app = create_app(
        tmp_path / "data",
        bootstrap_secret="secret",
        provider_transport=httpx.MockTransport(mock.handler),
    )
    with TestClient(app, base_url="http://127.0.0.1:8765") as client:
        headers = {"origin": "http://127.0.0.1:8765"}
        bootstrap = client.post(
            "/api/session/bootstrap", json={"secret": "secret"}, headers=headers
        )
        headers["x-csrf-token"] = bootstrap.json()["csrfToken"]
        offline = client.post(
            "/api/projects", json={"title": "Offline project"}, headers=headers
        ).json()["project_id"]
        attempt = client.post("/api/auth/siwc/start", json={}, headers=headers).json()
        query = parse_qs(urlsplit(attempt["authorizationUrl"]).query)
        mock.nonce = query["nonce"][0]
        response = client.get(
            "/auth/callback",
            params={
                "state": query["state"][0],
                "code": "code",
                "client_id": mock.client_id,
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        first_reg = client.get("/api/session").json()["registrationId"]
        assert client.get("/api/projects").json() == []
        assert (
            client.post(
                "/api/auth/bind-offline-project",
                json={"projectId": offline},
                headers=headers,
            ).status_code
            == 200
        )
        assert len(client.get("/api/projects").json()) == 1
        # A second registration with identical email must remain a distinct workspace/payer.
        mock.client_id, mock.subject = "oaiapp_bob", "bob-sub"
        attempt = client.post("/api/auth/siwc/start", json={}, headers=headers).json()
        query = parse_qs(urlsplit(attempt["authorizationUrl"]).query)
        mock.nonce = query["nonce"][0]
        assert (
            client.get(
                "/auth/callback",
                params={
                    "state": query["state"][0],
                    "code": "code",
                    "client_id": mock.client_id,
                },
                follow_redirects=False,
            ).status_code
            == 303
        )
        assert client.get("/api/projects").json() == []
        assert client.get(f"/api/projects/{offline}/designs").status_code == 404
        assert client.get("/api/session").json()["remainingRequests"] == 0
        assert (
            client.post(
                "/api/auth/active-registration",
                json={"registrationId": first_reg},
                headers=headers,
            ).status_code
            == 200
        )
        assert client.get("/api/projects").json()[0]["project_id"] == offline
        assert client.get("/api/session").json()["remainingRequests"] == 0
        assert (
            client.post(
                "/api/provider/budget", json={"requests": 2}, headers=headers
            ).status_code
            == 200
        )
        assert (
            client.post(
                "/api/auth/active-registration",
                json={"registrationId": None},
                headers=headers,
            ).status_code
            == 200
        )
        assert client.get("/api/projects").json() == []
        assert client.get("/api/session").json()["remainingRequests"] == 0


def test_cancellation_and_restart_never_resubmit(service, tmp_path, signing_key):
    from app.contracts import CanonicalInput, DesignInput

    provider, mock, result = connect(service, tmp_path, signing_key)
    principal, registration = result["principalId"], result["registrationId"]
    project = service.create_project(principal, "Bound")["project_id"]
    version = service.create_design(
        principal, project, DesignInput(title="Idea", spec=CanonicalInput())
    )["version_id"]
    sessions = {
        "session": {
            "principal": principal,
            "registration": registration,
            "remainingRequests": 2,
        }
    }
    jobs = Jobs(service, provider, Assets(service, tmp_path / "images"), sessions)
    data = JobInput(
        requestId=uid(),
        task="summarize_preferences",
        versionId=version,
        model="admitted-z",
        expectedEventSequence=1,
    )

    async def check():
        entered = asyncio.Event()

        async def blocked(*args):
            entered.set()
            await asyncio.Event().wait()

        provider.reason = blocked
        job = await jobs.enqueue("session", project, data)
        await entered.wait()
        jobs.pause_session("session")
        sessions["session"]["registration"] = "another-account"
        await asyncio.gather(*list(jobs.tasks.values()))
        assert jobs.read(principal, project, job["jobId"])["state"] == "cancelled"
        assert sessions["session"]["remainingRequests"] == 0
        with service.database.connect() as db:
            db.execute(
                "UPDATE jobs SET state='running' WHERE project_id=? AND job_id=?",
                (project, job["jobId"]),
            )
        restarted = Jobs(service, provider, jobs.assets, sessions)
        assert restarted.read(principal, project, job["jobId"])["state"] == "failed"
        assert (
            "completion_unknown"
            in restarted.read(principal, project, job["jobId"])["result"]["error"]
        )
        assert not restarted.tasks
        assert not any(r.url.path == "/v1/responses" for r in mock.requests)
        await jobs.close()
        await provider.close()

    asyncio.run(check())
