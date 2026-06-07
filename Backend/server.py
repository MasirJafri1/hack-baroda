from __future__ import annotations

import hashlib
import hmac
import json
import os
import queue
import threading
import uuid
from collections import deque
from datetime import datetime, timezone
from typing import Any, Deque, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from pipeline_runner import execute_pipeline


from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Hindsight DevOps Pipeline SSE API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET", "")

jobs: Dict[str, queue.Queue] = {}
results: Dict[str, Dict[str, Any]] = {}
# Stores last 50 webhook events for the frontend activity feed
webhook_events: Deque[Dict[str, Any]] = deque(maxlen=50)


class PipelineStartRequest(BaseModel):
    git_diff: Optional[str] = Field(default="", description="Unified git diff to analyze.")
    github_repo: Optional[str] = Field(default=None, description="GitHub repository owner/name or URL.")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    hindsight_session_id: Optional[str] = None


def _default_metadata(user_metadata: Dict[str, Any]) -> Dict[str, Any]:
    metadata = dict(user_metadata or {})
    metadata.setdefault("author", "unknown_developer")
    metadata.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
    return metadata


def _worker(session_id: str, payload: Dict[str, Any], event_queue: queue.Queue) -> None:
    def emit(event: str, data: Dict[str, Any]) -> None:
        event_queue.put((event, data))

    try:
        result_state = execute_pipeline(payload, emit=emit)
        results[session_id] = result_state
    except Exception as exc:
        event_queue.put(("error", {"session_id": session_id, "message": str(exc)}))
        results[session_id] = {"error": str(exc)}
    finally:
        event_queue.put(("done", {"session_id": session_id}))


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# GitHub Webhook
# ---------------------------------------------------------------------------

def _verify_github_signature(body: bytes, signature_header: str) -> bool:
    """Verify the X-Hub-Signature-256 header from GitHub."""
    if not GITHUB_WEBHOOK_SECRET:
        # If no secret is configured, skip verification (dev mode)
        return True
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(
        GITHUB_WEBHOOK_SECRET.encode(), body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature_header)


@app.post("/api/webhook/github")
async def github_webhook(request: Request) -> Dict[str, Any]:
    """Receive GitHub push / pull_request webhook events and auto-trigger the pipeline."""
    body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256", "")

    if not _verify_github_signature(body, signature):
        raise HTTPException(status_code=403, detail="Invalid webhook signature")

    event_type = request.headers.get("X-GitHub-Event", "ping")
    delivery_id = request.headers.get("X-GitHub-Delivery", str(uuid.uuid4()))

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    repo_full_name: Optional[str] = (
        payload.get("repository", {}).get("full_name")
    )

    webhook_record: Dict[str, Any] = {
        "delivery_id": delivery_id,
        "event": event_type,
        "repo": repo_full_name or "unknown",
        "received_at": datetime.now(timezone.utc).isoformat(),
        "session_id": None,
        "status": "received",
    }

    if event_type == "ping":
        webhook_record["status"] = "pong"
        webhook_events.appendleft(webhook_record)
        return {"message": "pong", "delivery_id": delivery_id}

    if event_type in ("push", "pull_request") and repo_full_name:
        # Determine the branch / PR info for metadata
        if event_type == "push":
            ref = payload.get("ref", "refs/heads/main")
            branch = ref.replace("refs/heads/", "")
            author = (
                payload.get("pusher", {}).get("name")
                or payload.get("sender", {}).get("login")
                or "github_webhook"
            )
            head_commit_msg = (
                (payload.get("head_commit") or {}).get("message", "")
            )
        else:  # pull_request
            branch = payload.get("pull_request", {}).get("head", {}).get("ref", "")
            author = payload.get("sender", {}).get("login", "github_webhook")
            head_commit_msg = payload.get("pull_request", {}).get("title", "")

        session_id = f"webhook_{uuid.uuid4().hex[:12]}"
        event_queue: queue.Queue = queue.Queue()
        jobs[session_id] = event_queue

        wh_payload = {
            "git_diff": "",
            "github_repo": repo_full_name,
            "metadata": {
                "author": author,
                "branch": branch,
                "trigger": f"github_webhook:{event_type}",
                "head_commit": head_commit_msg,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "github_repo": repo_full_name,
            },
            "hindsight_session_id": session_id,
            "risk_flag": False,
            "risk_reason": "",
            "matches_found": 0,
            "retrieval_queries": [],
            "retrieved_logs": [],
            "agent_analyses": {},
            "loop_count": 0,
            "final_audit": "",
            "frontend_payload": {},
        }

        thread = threading.Thread(
            target=_worker, args=(session_id, wh_payload, event_queue), daemon=True
        )
        thread.start()

        webhook_record["session_id"] = session_id
        webhook_record["status"] = "pipeline_triggered"
        webhook_record["branch"] = branch
        webhook_events.appendleft(webhook_record)

        return {
            "message": "pipeline triggered",
            "session_id": session_id,
            "events_url": f"/api/pipeline/{session_id}/events",
            "result_url": f"/api/pipeline/{session_id}/result",
        }

    # Unsupported event type — log it and return 200
    webhook_record["status"] = "ignored"
    webhook_events.appendleft(webhook_record)
    return {"message": f"event '{event_type}' acknowledged but not processed"}


@app.get("/api/webhook/events")
def list_webhook_events(limit: int = 20) -> List[Dict[str, Any]]:
    """Return the most recent webhook events for the frontend activity feed."""
    return list(webhook_events)[:limit]



@app.post("/api/pipeline/start")
def start_pipeline(request: PipelineStartRequest) -> Dict[str, Any]:
    session_id = request.hindsight_session_id or f"session_{uuid.uuid4().hex[:12]}"
    event_queue: queue.Queue = queue.Queue()
    jobs[session_id] = event_queue

    metadata = _default_metadata(request.metadata)
    if request.github_repo:
        metadata["github_repo"] = request.github_repo

    payload = {
        "git_diff": request.git_diff or "",
        "github_repo": request.github_repo or "",
        "metadata": metadata,
        "hindsight_session_id": session_id,
        "risk_flag": False,
        "risk_reason": "",
        "matches_found": 0,
        "retrieval_queries": [],
        "retrieved_logs": [],
        "agent_analyses": {},
        "loop_count": 0,
        "final_audit": "",
        "frontend_payload": {},
    }


    thread = threading.Thread(target=_worker, args=(session_id, payload, event_queue), daemon=True)
    thread.start()

    return {
        "session_id": session_id,
        "events_url": f"/api/pipeline/{session_id}/events",
        "result_url": f"/api/pipeline/{session_id}/result",
    }


def _sse_format(event: str, payload: Dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


def _event_stream(session_id: str):
    event_queue = jobs.get(session_id)
    if event_queue is None:
        raise HTTPException(status_code=404, detail="Session not found")

    while True:
        event, payload = event_queue.get()
        yield _sse_format(event, payload)
        if event == "done":
            break


@app.get("/api/pipeline/{session_id}/events")
def pipeline_events(session_id: str):
    return StreamingResponse(_event_stream(session_id), media_type="text/event-stream")


@app.get("/api/pipeline/{session_id}/result")
def pipeline_result(session_id: str) -> Dict[str, Any]:
    if session_id not in results:
        raise HTTPException(status_code=404, detail="Result not ready or session not found")
    return results[session_id].get("frontend_payload", results[session_id])