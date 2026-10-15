import sys
import tempfile
from pathlib import Path
import uvicorn

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "server"))
from app.main import create_app
from app.discovery_contracts import DiscoveryRoundInput
from fastapi import Request

with tempfile.TemporaryDirectory(prefix="style-explorer-browser-") as data:
    app = create_app(
        data, origin="http://127.0.0.1:8766", bootstrap_secret="browser-test"
    )

    @app.post("/api/fixture/legacy-round")
    async def legacy_round(request: Request):
        payload = await request.json()
        project = payload["projectId"]
        discovery = app.state.discovery
        state = discovery.state(request.state.principal, project)
        # Construct historical four-option data without weakening the new public contract.
        old_request = DiscoveryRoundInput.model_construct(
            requestId="legacy-round-fixture",
            expectedRevision=state["revision"],
            count=4,
        )
        return {
            "roundId": discovery.prepare(request.state.principal, project, old_request)
        }

    uvicorn.run(app, host="127.0.0.1", port=8766, log_level="warning")
