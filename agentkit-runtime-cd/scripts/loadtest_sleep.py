#!/usr/bin/env python3
"""Run a small concurrency probe against the /sleep endpoint.

The script uses only Python standard library modules and reads the Runtime API key
from an environment variable so secrets are not saved into files.
"""

import argparse
import asyncio
import json
import os
import statistics
import time
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path


def call_sleep(endpoint: str, api_key: str, seconds: float, index: int, timeout: float) -> dict:
    url = endpoint.rstrip("/") + f"/sleep?seconds={seconds}"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "x-request-id": f"loadtest-{int(time.time())}-{index}",
        },
    )
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
            status = resp.status
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        status = exc.code
    except Exception as exc:
        return {
            "index": index,
            "status": "ERROR",
            "client_elapsed_seconds": round(time.perf_counter() - started, 3),
            "error": repr(exc),
        }

    elapsed = round(time.perf_counter() - started, 3)
    try:
        parsed = json.loads(body)
    except json.JSONDecodeError:
        parsed = body

    return {
        "index": index,
        "status": status,
        "client_elapsed_seconds": elapsed,
        "hostname": parsed.get("hostname") if isinstance(parsed, dict) else None,
        "version": parsed.get("version") if isinstance(parsed, dict) else None,
        "body": parsed if status != 200 else None,
    }


async def run_load(endpoint: str, api_key: str, concurrency: int, seconds: float, timeout: float) -> list[dict]:
    tasks = [
        asyncio.to_thread(call_sleep, endpoint, api_key, seconds, index, timeout)
        for index in range(concurrency)
    ]
    return await asyncio.gather(*tasks)


def summarize(results: list[dict], endpoint: str, concurrency: int, seconds: float) -> dict:
    status_counts = Counter(str(item["status"]) for item in results)
    hostname_counts = Counter(
        item["hostname"] for item in results if item.get("status") == 200 and item.get("hostname")
    )
    latencies = sorted(
        item["client_elapsed_seconds"] for item in results if isinstance(item.get("status"), int) and item["status"] == 200
    )
    summary = {
        "endpoint": endpoint.rstrip("/"),
        "test_concurrency": concurrency,
        "sleep_seconds": seconds,
        "status_counts": dict(status_counts),
        "hostname_counts": dict(hostname_counts),
        "unique_hostnames": sorted(hostname_counts),
        "results": results,
    }
    if latencies:
        p95_index = min(len(latencies) - 1, int(len(latencies) * 0.95))
        summary.update(
            {
                "latency_min": round(latencies[0], 3),
                "latency_median": round(statistics.median(latencies), 3),
                "latency_p95_approx": round(latencies[p95_index], 3),
                "latency_max": round(latencies[-1], 3),
            }
        )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a concurrency probe against AgentKit Runtime /sleep.")
    parser.add_argument("--endpoint", default=os.getenv("RUNTIME_ENDPOINT"), help="Runtime endpoint URL.")
    parser.add_argument("--api-key-env", default="RUNTIME_API_KEY", help="Environment variable containing the Runtime API key.")
    parser.add_argument("--concurrency", type=int, default=30)
    parser.add_argument("--seconds", type=float, default=5.0)
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--out", help="Optional JSON output path.")
    args = parser.parse_args()

    if not args.endpoint:
        raise SystemExit("Missing endpoint. Pass --endpoint or set RUNTIME_ENDPOINT.")

    api_key = os.getenv(args.api_key_env)
    if not api_key:
        raise SystemExit(f"Missing API key. Set {args.api_key_env}; do not write it into source files.")

    started = time.perf_counter()
    results = asyncio.run(run_load(args.endpoint, api_key, args.concurrency, args.seconds, args.timeout))
    summary = summarize(results, args.endpoint, args.concurrency, args.seconds)
    summary["wall_elapsed_seconds"] = round(time.perf_counter() - started, 3)

    text = json.dumps(summary, ensure_ascii=False, indent=2)
    print(text)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
