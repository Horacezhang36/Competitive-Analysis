# AgentKit Runtime Continuous Delivery Demo

This directory contains a deterministic FastAPI Runtime app used to verify the AgentKit Runtime continuous delivery path:

- build an image with AgentKit CLI
- create a Runtime
- update a new version without releasing it
- release the pending version
- scale out and run a concurrency probe
- roll back to a previous version

The app avoids model calls so release and concurrency behavior can be validated without LLM variance.

## Endpoints

| Endpoint | Purpose |
|---|---|
| `GET /health` | Liveness and current version marker |
| `GET /version` | Current demo version, release marker, hostname and process metadata |
| `GET /sleep?seconds=5` | Async delay used for request-level concurrency probes |
| `GET /work?iterations=20000` | Small CPU probe |

## Required Local Environment

Do not store credentials in this repository. Export credentials in the shell or configure them as GitHub Actions secrets:

```bash
export VOLCENGINE_ACCESS_KEY="..."
export VOLCENGINE_SECRET_KEY="..."
export VOLCENGINE_REGION="cn-beijing"
export VOLCENGINE_AGENTKIT_REGION="cn-beijing"
```

## Local Smoke

```bash
python3 -m pip install -r requirements.txt
uvicorn app:app --host 127.0.0.1 --port 8000
```

Open another terminal:

```bash
curl http://127.0.0.1:8000/version
```

## Runtime Probe

After a Runtime is created, export the endpoint and Runtime API key only in your shell:

```bash
export RUNTIME_ENDPOINT="https://your-runtime-endpoint"
export RUNTIME_API_KEY="your-runtime-api-key"
python3 scripts/probe_runtime.py
python3 scripts/loadtest_sleep.py --concurrency 30 --seconds 2 --out loadtest.json
```

