import asyncio
import os
import socket
import time
import uuid

from fastapi import FastAPI, Query, Request


STARTED_AT = time.time()
HOSTNAME = socket.gethostname()
PID = os.getpid()


def runtime_info() -> dict:
    return {
        "demo": "agentkit-runtime-cd",
        "version": os.getenv("DEMO_VERSION", "v1"),
        "release_marker": os.getenv("DEMO_RELEASE_MARKER", "COURSE_CD_V1"),
        "elasticity_model": "request-level",
        "hostname": HOSTNAME,
        "pid": PID,
        "started_at": STARTED_AT,
        "uptime_seconds": round(time.time() - STARTED_AT, 3),
    }


app = FastAPI(title="AgentKit Runtime Release and Concurrency Course Demo")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", **runtime_info()}


@app.get("/version")
async def version() -> dict:
    return runtime_info()


@app.get("/sleep")
async def sleep_probe(
    request: Request,
    seconds: float = Query(default=2.0, ge=0.0, le=20.0),
) -> dict:
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    started = time.time()
    await asyncio.sleep(seconds)
    ended = time.time()
    return {
        **runtime_info(),
        "request_id": request_id,
        "requested_sleep_seconds": seconds,
        "actual_elapsed_seconds": round(ended - started, 3),
        "server_received_at": started,
        "server_finished_at": ended,
    }


@app.get("/work")
async def work_probe(iterations: int = Query(default=20000, ge=1, le=2000000)) -> dict:
    started = time.time()
    total = 0
    for i in range(iterations):
        total += (i * i) % 97
    ended = time.time()
    return {
        **runtime_info(),
        "iterations": iterations,
        "checksum": total,
        "actual_elapsed_seconds": round(ended - started, 3),
    }
