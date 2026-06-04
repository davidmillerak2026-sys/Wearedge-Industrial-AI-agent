# Contributing

WearEdge Pro is organized around reproducible edge-AI engineering evidence. Contributions should keep the repository easy to review, clone, and run.

## Development Flow

1. Keep product claims tied to tests, PoC summaries, audit logs, or documented field evidence.
2. Put runtime code in `jetson/`, client code in `clients/`, fixtures in `data/`, and permanent proof in `docs/`.
3. Keep local outputs out of Git: `runtime/`, `outputs/`, model weights, deployment tar files, generated videos, and temporary logs.
4. Run Python tests before opening a pull request:

```bash
python -m pytest
```

5. For Jetson work, also run the gateway smoke test when hardware is available:

```bash
source .env
scripts/smoke_test.sh
```

## Evidence Rule

If a change adds a new industrial capability, include at least one of:

- deterministic unit tests,
- a small JSON fixture,
- a short PoC summary under `docs/poc-results/`,
- or a documentation update that explains the runtime boundary and failure mode.

Avoid adding raw customer data, private factory images, secrets, model files, or large generated media.
