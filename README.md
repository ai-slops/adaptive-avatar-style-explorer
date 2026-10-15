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
