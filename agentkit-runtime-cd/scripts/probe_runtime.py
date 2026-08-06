#!/usr/bin/env python3
"""Probe an AgentKit Runtime endpoint without storing secrets in files."""

import argparse
import json
import os
import time
import urllib.error
import urllib.request


def request_json(endpoint: str, path: str, api_key: str, timeout: float) -> dict:
    url = endpoint.rstrip("/") + path
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {api_key}"})
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
            "path": path,
            "status": "ERROR",
            "elapsed_seconds": round(time.perf_counter() - started, 3),
            "error": repr(exc),
        }

    try:
        parsed_body = json.loads(body)
    except json.JSONDecodeError:
        parsed_body = body

    return {
        "path": path,
        "status": status,
        "elapsed_seconds": round(time.perf_counter() - started, 3),
        "body": parsed_body,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Probe an AgentKit Runtime endpoint.")
    parser.add_argument("--endpoint", default=os.getenv("RUNTIME_ENDPOINT"), help="Runtime endpoint URL.")
    parser.add_argument("--api-key-env", default="RUNTIME_API_KEY", help="Environment variable containing the Runtime API key.")
    parser.add_argument("--timeout", type=float, default=20.0)
    args = parser.parse_args()

    if not args.endpoint:
        raise SystemExit("Missing endpoint. Pass --endpoint or set RUNTIME_ENDPOINT.")

    api_key = os.getenv(args.api_key_env)
    if not api_key:
        raise SystemExit(f"Missing API key. Set {args.api_key_env}; do not write it into source files.")

    result = {
        "endpoint": args.endpoint.rstrip("/"),
        "api_key_env": args.api_key_env,
        "checks": [
            request_json(args.endpoint, "/version", api_key, args.timeout),
            request_json(args.endpoint, "/sleep?seconds=1", api_key, args.timeout),
        ],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
