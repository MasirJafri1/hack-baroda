#!/usr/bin/env python3
"""Ingest synthetic incidents from Backend/database.json into a running Hindsight service.

Supports --bulk (send all incidents in one run) or --iterative (send one-by-one with delay).
"""
import os
import time
import json
import argparse
from typing import List, Dict, Any

import sys

# Ensure project Backend is on path
ROOT = os.path.dirname(os.path.dirname(__file__))
BACKEND = os.path.join(ROOT, "Backend")
sys.path.insert(0, BACKEND)

from hindsight_client import HindsightHTTPClient


def load_incidents(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def post_incident(client: HindsightHTTPClient, incident: Dict[str, Any], endpoint: str = "/incidents") -> Any:
    try:
        return client._request("POST", endpoint, json=incident)
    except Exception as e:
        print(f"[ERROR] Failed to post incident: {e}")
        return None


def bulk_import(client: HindsightHTTPClient, incidents: List[Dict[str, Any]], endpoint: str):
    print(f"Starting bulk import of {len(incidents)} incidents to {client.base_url}{endpoint}")
    for i, inc in enumerate(incidents, 1):
        res = post_incident(client, inc, endpoint)
        print(f"[{i}/{len(incidents)}] -> {res}")


def iterative_import(client: HindsightHTTPClient, incidents: List[Dict[str, Any]], endpoint: str, delay: float):
    print(f"Starting iterative import of {len(incidents)} incidents with {delay}s delay")
    for i, inc in enumerate(incidents, 1):
        res = post_incident(client, inc, endpoint)
        print(f"[{i}/{len(incidents)}] -> {res}")
        time.sleep(delay)


def main():
    parser = argparse.ArgumentParser(description="Ingest synthetic incidents into Hindsight service")
    parser.add_argument("--hindsight-url", default=os.getenv("HINDSIGHT_URL", "http://localhost:8080"))
    parser.add_argument("--api-key", default=os.getenv("HINDSIGHT_API_KEY"))
    parser.add_argument("--mode", choices=["bulk", "iterative"], default="iterative")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between iterative posts (seconds)")
    parser.add_argument("--endpoint", default="/incidents", help="Relative endpoint path to post incidents")
    parser.add_argument("--dry-run", action="store_true", help="Show payloads but do not send")
    parser.add_argument("--source", default=os.path.join(BACKEND, "database.json"), help="Path to synthetic incidents JSON file")

    args = parser.parse_args()

    incidents = load_incidents(args.source)
    client = HindsightHTTPClient(args.hindsight_url, api_key=args.api_key)

    if args.dry_run:
        print("Dry run mode - showing first 3 incidents")
        for inc in incidents[:3]:
            print(json.dumps(inc, indent=2))
        return

    if args.mode == "bulk":
        bulk_import(client, incidents, args.endpoint)
    else:
        iterative_import(client, incidents, args.endpoint, args.delay)


if __name__ == "__main__":
    main()
