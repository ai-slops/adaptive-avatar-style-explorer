"""Isolated native-mode browser fixture; no provider usage."""
import asyncio
import sys
import tempfile
from pathlib import Path

import uvicorn

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root / "server"))
sys.path.insert(0, str(root / "server" / "tests"))
from app.main import create_app
from test_codex import FakeCodex

class BrowserCodex(FakeCodex):
    async def turn(self, *args, **kwargs):
        await asyncio.sleep(0.3)
        return await super().turn(*args, **kwargs)

with tempfile.TemporaryDirectory(prefix="style-explorer-codex-browser-") as data:
    uvicorn.run(create_app(data, origin="http://127.0.0.1:8767", bootstrap_secret="codex-browser-test", execution_mode="codex_local", codex_rpc_factory=BrowserCodex),host="127.0.0.1",port=8767,log_level="warning")
