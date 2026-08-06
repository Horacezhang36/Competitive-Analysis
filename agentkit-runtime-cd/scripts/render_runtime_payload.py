#!/usr/bin/env python3
"""Render AgentKit Runtime create/update JSON payloads for the CD demo."""

import argparse
import json


def envs(version: str, marker: str) -> list[dict[str, str]]:
    return [
        {"Key": "DEMO_VERSION", "Value": version},
        {"Key": "DEMO_RELEASE_MARKER", "Value": marker},
    ]


def tags(stage: str) -> list[dict[str, str]]:
    return [
        {"Key": "agentkit:course", "Value": "runtime-continuous-delivery"},
        {"Key": "agentkit:release-stage", "Value": stage},
    ]


def render_create(args: argparse.Namespace) -> dict:
    return {
        "Name": args.name,
        "Description": "AgentKit Runtime CD demo v1.",
        "ArtifactType": "image",
        "ArtifactUrl": args.image,
        "RoleName": args.role_name,
        "ProjectName": args.project_name,
        "CpuMilli": args.cpu_milli,
        "MemoryMb": args.memory_mb,
        "MinInstance": 1,
        "MaxInstance": 2,
        "MaxConcurrency": 10,
        "ApmplusEnable": True,
        "AuthorizerConfiguration": {
            "KeyAuth": {
                "ApiKeyName": f"API-KEY-{args.name}",
                "ApiKeyLocation": "header",
            }
        },
        "Envs": envs("v1", "COURSE_CD_V1"),
        "Tags": tags("v1"),
    }


def render_update(args: argparse.Namespace, *, version: str, marker: str, stage: str, release: bool, max_instance: int) -> dict:
    return {
        "RuntimeId": args.runtime_id,
        "Description": f"AgentKit Runtime CD demo {version}.",
        "ArtifactType": "image",
        "ArtifactUrl": args.image,
        "CpuMilli": args.cpu_milli,
        "MemoryMb": args.memory_mb,
        "MinInstance": 1,
        "MaxInstance": max_instance,
        "MaxConcurrency": 10,
        "ReleaseEnable": release,
        "Envs": envs(version, marker),
        "Tags": tags(stage),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Render AgentKit Runtime CD JSON payloads.")
    parser.add_argument("mode", choices=["create-v1", "update-v2-unreleased", "update-v3-release"])
    parser.add_argument("--name", default="agentkit-runtime-cd-demo")
    parser.add_argument("--runtime-id")
    parser.add_argument("--image", required=True)
    parser.add_argument("--role-name", default="")
    parser.add_argument("--project-name", default="default")
    parser.add_argument("--cpu-milli", type=int, default=1000)
    parser.add_argument("--memory-mb", type=int, default=2048)
    args = parser.parse_args()

    if args.mode == "create-v1":
        if not args.role_name:
            parser.error("--role-name is required for create-v1")
        payload = render_create(args)
    else:
        if not args.runtime_id:
            parser.error("--runtime-id is required for update modes")
        if args.mode == "update-v2-unreleased":
            payload = render_update(
                args,
                version="v2",
                marker="COURSE_CD_V2_UNRELEASED",
                stage="v2-unreleased",
                release=False,
                max_instance=2,
            )
        else:
            payload = render_update(
                args,
                version="v3",
                marker="COURSE_CD_V3_SCALEOUT",
                stage="v3-scaleout",
                release=True,
                max_instance=3,
            )

    print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
