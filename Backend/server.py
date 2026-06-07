from __future__ import annotations

import json
import queue
import threading
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from pipeline_runner import execute_pipeline


app = FastAPI(title="Hindsight DevOps Pipeline SSE API", version="0.1.0")

jobs: Dict[str, queue.Queue] = {}
results: Dict[str, Dict[str, Any]] = {}


class PipelineStartRequest(BaseModel):
    git_diff: str = Field(..., description="Unified git diff to analyze.")
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


@app.post("/api/pipeline/start")
def start_pipeline(request: PipelineStartRequest) -> Dict[str, Any]:
    session_id = request.hindsight_session_id or f"session_{uuid.uuid4().hex[:12]}"
    event_queue: queue.Queue = queue.Queue()
    jobs[session_id] = event_queue

    metadata = _default_metadata(request.metadata)
    payload = {
        "git_diff": request.git_diff,
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