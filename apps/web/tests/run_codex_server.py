"""Isolated native-mode browser fixture; no provider usage."""

import asyncio
import sys
import tempfile
from pathlib import Path

import uvicorn
from fastapi import Request

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root / "server"))
sys.path.insert(0, str(root / "server" / "tests"))
from app.common import DomainError
from app.main import create_app
from test_codex import FakeCodex


class BrowserCodex(FakeCodex):
    calls = 0
    fail_at = 0
    delay = 0.3

    async def turn(self, *args, **kwargs):
        await asyncio.sleep(type(self).delay)
        if type(self).calls + 1 == type(self).fail_at:
            type(self).calls += 1
            raise DomainError(
                "이 후보의 테스트 생성이 실패했습니다. 자동 재시도하지 않습니다.", 502
            )
        return await super().turn(*args, **kwargs)


with tempfile.TemporaryDirectory(prefix="style-explorer-codex-browser-") as data:
    app = create_app(
        data,
        origin="http://127.0.0.1:8767",
        bootstrap_secret="codex-browser-test",
        execution_mode="codex_local",
        codex_rpc_factory=BrowserCodex,
    )
    connected_account = dict(BrowserCodex.account_value)

    # This control exists only in the isolated mock server, never in the product.
    @app.post("/fixture/codex")
    async def configure_fixture(request: Request):
        config = await request.json()
        BrowserCodex.calls = 0
        BrowserCodex.fail_at = config.get("failAt", 0)
        BrowserCodex.delay = config.get("delay", 0.3)
        BrowserCodex.account_value = (
            connected_account if config.get("connected", True) else None
        )
        return {"configured": True}

    @app.get("/fixture/codex")
    async def fixture_counts():
        return {"calls": BrowserCodex.calls}

    # Put the fixture GET before the product SPA fallback.
    app.router.routes.insert(0, app.router.routes.pop())

    uvicorn.run(app, host="127.0.0.1", port=8767, log_level="warning")
