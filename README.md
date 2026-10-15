# Adaptive Avatar Style Explorer

A local, prompt-only workspace for discovering a reusable 3D character design.
The implementation target is [the version 2 specification](specs/implementation-v2.md).
Images are imported evidence about immutable design versions. Camera, pose, lighting,
and expression are test conditions, never taste features. The community application
must not generate images or submit prompts to external generators.

Implementation is in progress. See [implementation status](specs/STATUS.md) for
verified capabilities and remaining release gates.

## Development

Use Python 3.11 or newer with a virtual environment, then:

```sh
python -m pip install -r requirements.lock
python -m pytest
```

The numerical baseline is extracted from Appendix B of the specification. The
initial SQLite schema is extracted from Appendix A; service validation must enforce
the additional invariants described by the specification.

## Run the local application

```sh
npm ci --prefix apps/web
npm run build --prefix apps/web
PYTHONPATH=apps/server .venv/bin/python -m app
```

The server binds to `127.0.0.1:8765` and prints a private launch link. Open that link
to establish an application session. Pass `--no-browser`, `--port`, or `--data-dir`
to the launcher as needed. The default `.data/` directory is ignored by Git.

The current offline workflow supports project/design creation, original raster
imports, manual evidence assessments and feature entry, frozen scoped comparisons,
shortlists and property locks, immutable revisions, text prompt export/manual result
import, checkpoints, and ZIP handoffs. Provider connection is still in progress.

For browser tests, install Chromium with `npx playwright install chromium` in
`apps/web`, then run `npm test --prefix apps/web`. Linux may need Playwright's
browser dependencies and fonts installed. Tests use an isolated temporary database.
