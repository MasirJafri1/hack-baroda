from __future__ import annotations

import io
import json
from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
from typing import Any, Callable, Dict, Optional

from agents.big_boss import big_boss
from agents.cloud_expert import cloud_expert
from agents.code_expert import code_expert
from agents.context_agent import context_agent
from agents.git_expert import git_expert
from agents.retrieval_agent import retrieval_agent
from agents.reviewer_v1 import reviewer_v1
from agents.reviewer_v2 import reviewer_v2
from agents.github_crawler_node import github_crawler_node
from frontend_payload import build_frontend_payload


EmitFn = Callable[[str, Dict[str, Any]], None]


def _initial_state(inputs: Dict[str, Any]) -> Dict[str, Any]:
    state = {
        "git_diff": inputs.get("git_diff", ""),
        "github_repo": inputs.get("github_repo", ""),
        "metadata": deepcopy(inputs.get("metadata", {})),
        "hindsight_session_id": inputs.get("hindsight_session_id", ""),
        "risk_flag": inputs.get("risk_flag", False),
        "risk_reason": inputs.get("risk_reason", ""),
        "matches_found": inputs.get("matches_found", 0),
        "retrieval_queries": inputs.get("retrieval_queries", []),
        "retrieved_logs": inputs.get("retrieved_logs", []),
        "agent_analyses": inputs.get("agent_analyses", {}),
        "loop_count": inputs.get("loop_count", 0),
        "final_audit": inputs.get("final_audit", ""),
        "frontend_payload": inputs.get("frontend_payload", {}),
    }
    state["metadata"] = state["metadata"] or {}
    return state


def _emit(emit: Optional[EmitFn], event: str, payload: Dict[str, Any]) -> None:
    if emit:
        emit(event, payload)


def execute_pipeline(inputs: Dict[str, Any], emit: Optional[EmitFn] = None) -> Dict[str, Any]:
    state = _initial_state(inputs)
    _emit(emit, "run_started", {"session_id": state.get("hindsight_session_id", "")})

    # Suppress noisy console logs for the SSE path; progress is emitted as SSE.
    sink = io.StringIO()
    with redirect_stdout(sink), redirect_stderr(sink):
        _emit(emit, "stage_started", {"stage": "github_crawler"})
        crawler_out = github_crawler_node(state)
        state.update(crawler_out)
        _emit(emit, "stage_completed", {"stage": "github_crawler", "output": {"github_repo": state.get("github_repo"), "has_diff": bool(state.get("git_diff"))}})

        _emit(emit, "stage_started", {"stage": "context_agent"})
        state.update(context_agent(state))
        _emit(emit, "stage_completed", {"stage": "context_agent", "state": {"hindsight_session_id": state.get("hindsight_session_id"), "metadata": state.get("metadata", {})}})

        _emit(emit, "stage_started", {"stage": "reviewer_v1"})
        rv1 = reviewer_v1(state)
        state.update(rv1)
        _emit(emit, "stage_completed", {"stage": "reviewer_v1", "output": rv1})

        if not state.get("risk_flag", False):
            frontend_payload = build_frontend_payload(
                state,
                verdict="APPROVED",
                risks=[],
                mitigation_patches=[],
                example_patch_code="",
                conclusion="No high-risk historical match was detected, so the pipeline cleared the change.",
            )
            state["frontend_payload"] = frontend_payload
            state["final_audit"] = json.dumps(frontend_payload, ensure_ascii=False)
            _emit(emit, "final_payload", frontend_payload)
            return state

        _emit(emit, "stage_started", {"stage": "reviewer_v2"})
        rv2 = reviewer_v2(state)
        state.update(rv2)
        _emit(emit, "stage_completed", {"stage": "reviewer_v2", "output": rv2})

        _emit(emit, "stage_started", {"stage": "retrieval_agent"})
        retrieval = retrieval_agent(state)
        state.update(retrieval)
        _emit(emit, "stage_completed", {"stage": "retrieval_agent", "output": retrieval})

        for stage_name, agent_fn in (
            ("git_expert", git_expert),
            ("cloud_expert", cloud_expert),
            ("code_expert", code_expert),
        ):
            _emit(emit, "stage_started", {"stage": stage_name})
            output = agent_fn(state)
            state.update(output)
            _emit(emit, "stage_completed", {"stage": stage_name, "output": output})

        _emit(emit, "stage_started", {"stage": "big_boss"})
        boss_output = big_boss(state)
        state.update(boss_output)
        _emit(emit, "stage_completed", {"stage": "big_boss", "output": {"metadata": state.get("metadata", {}), "frontend_payload": state.get("frontend_payload", {})}})

    payload = state.get("frontend_payload") or {}
    if not payload:
        try:
            payload = json.loads(state.get("final_audit", "{}"))
        except Exception:
            payload = build_frontend_payload(state)
            state["frontend_payload"] = payload
            state["final_audit"] = json.dumps(payload, ensure_ascii=False)

    _emit(emit, "final_payload", payload)
    return state