from __future__ import annotations

import json
import logging
import time
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

# ---------------------------------------------------------------------------
# Logging setup — rich coloured output in uvicorn terminal
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("hindsight.pipeline")

DIVIDER = "─" * 60


EmitFn = Callable[[str, Dict[str, Any]], None]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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


def _run_stage(name: str, fn, state: Dict[str, Any], emit: Optional[EmitFn]) -> Dict[str, Any]:
    """Run a single agent stage with timing, logging, and SSE events."""
    log.info("┌── STAGE START  ▸ %s", name.upper())
    _emit(emit, "stage_started", {"stage": name})
    t0 = time.perf_counter()

    output = fn(state)

    elapsed = time.perf_counter() - t0
    log.info("└── STAGE DONE   ▸ %-20s  (%.2fs)", name.upper(), elapsed)

    # Log meaningful output keys (skip large blobs)
    if output:
        for k, v in output.items():
            if k in ("git_diff", "final_audit"):
                preview = str(v)[:120].replace("\n", " ")
                log.info("    %-22s = %s…", k, preview)
            elif isinstance(v, (dict, list)):
                log.info("    %-22s = %s", k, json.dumps(v, ensure_ascii=False)[:200])
            else:
                log.info("    %-22s = %s", k, str(v)[:200])

    _emit(emit, "stage_completed", {"stage": name, "output": _safe_output(name, output, state)})
    return output


def _safe_output(stage: str, output: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
    """Return a concise SSE-safe summary of stage output."""
    if stage == "github_crawler":
        return {
            "github_repo": state.get("github_repo"),
            "has_diff": bool(state.get("git_diff")),
            "diff_length": len(state.get("git_diff", "")),
        }
    if stage == "context_agent":
        return {
            "hindsight_session_id": state.get("hindsight_session_id"),
            "metadata": state.get("metadata", {}),
        }
    if stage == "big_boss":
        return {
            "metadata": state.get("metadata", {}),
            "frontend_payload_keys": list((state.get("frontend_payload") or {}).keys()),
        }
    return output or {}


# ---------------------------------------------------------------------------
# Main pipeline executor
# ---------------------------------------------------------------------------

def execute_pipeline(inputs: Dict[str, Any], emit: Optional[EmitFn] = None) -> Dict[str, Any]:
    state = _initial_state(inputs)
    session_id = state.get("hindsight_session_id", "unknown")
    trigger = state.get("metadata", {}).get("trigger", "manual")
    author = state.get("metadata", {}).get("author", "unknown")
    github_repo = state.get("github_repo", "") or state.get("metadata", {}).get("github_repo", "")

    log.info(DIVIDER)
    log.info("🚀  PIPELINE STARTED")
    log.info("    session_id   = %s", session_id)
    log.info("    trigger      = %s", trigger)
    log.info("    author       = %s", author)
    log.info("    github_repo  = %s", github_repo or "(none)")
    log.info("    diff_length  = %d chars", len(state.get("git_diff", "")))
    log.info(DIVIDER)

    _emit(emit, "run_started", {"session_id": session_id})

    # ------------------------------------------------------------------
    # Stage 1: GitHub Crawler
    # ------------------------------------------------------------------
    crawler_out = _run_stage("github_crawler", github_crawler_node, state, emit)
    state.update(crawler_out)

    diff_len = len(state.get("git_diff", ""))
    log.info("    ✔ Diff available: %d chars", diff_len)
    if diff_len == 0:
        log.warning("    ⚠ No git diff — downstream agents will have limited context.")

    # ------------------------------------------------------------------
    # Stage 2: Context Agent (file classification)
    # ------------------------------------------------------------------
    ctx_out = _run_stage("context_agent", context_agent, state, emit)
    state.update(ctx_out)

    classification = state.get("metadata", {}).get("classification", {})
    log.info("    ✔ Classification → app_code=%s | cloud_infra=%s | git_meta=%s",
             classification.get("app_code", []),
             classification.get("cloud_infra", []),
             classification.get("git_meta", []))

    # ------------------------------------------------------------------
    # Stage 3: Reviewer v1 (triage / Hindsight recall)
    # ------------------------------------------------------------------
    rv1 = _run_stage("reviewer_v1", reviewer_v1, state, emit)
    state.update(rv1)

    risk_flag = state.get("risk_flag", False)
    matches = state.get("matches_found", 0)
    reason = state.get("risk_reason", "")
    log.info("    ✔ Triage result → risk_flag=%s | matches_found=%d | reason=%s",
             risk_flag, matches, reason[:120] if reason else "(none)")

    # ------------------------------------------------------------------
    # Early exit: APPROVED (no risk)
    # ------------------------------------------------------------------
    if not risk_flag:
        log.info("")
        log.info("✅  VERDICT: APPROVED — no historical risk match. Pipeline exits early.")
        log.info(DIVIDER)

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

    log.info("")
    log.info("⚠️   Risk flagged — escalating to full specialist review...")
    log.info("")

    # ------------------------------------------------------------------
    # Stage 4: Reviewer v2 (deeper semantic check)
    # ------------------------------------------------------------------
    rv2 = _run_stage("reviewer_v2", reviewer_v2, state, emit)
    state.update(rv2)

    # ------------------------------------------------------------------
    # Stage 5: Retrieval Agent (fetch historical logs)
    # ------------------------------------------------------------------
    retrieval = _run_stage("retrieval_agent", retrieval_agent, state, emit)
    state.update(retrieval)

    retrieved = state.get("retrieved_logs", [])
    log.info("    ✔ Retrieved %d historical log(s)", len(retrieved))
    for i, entry in enumerate(retrieved[:3]):          # show first 3
        log.info("      [%d] %s", i, str(entry)[:120])

    # ------------------------------------------------------------------
    # Stages 6-8: Domain experts
    # ------------------------------------------------------------------
    for stage_name, agent_fn in (
        ("git_expert", git_expert),
        ("cloud_expert", cloud_expert),
        ("code_expert", code_expert),
    ):
        out = _run_stage(stage_name, agent_fn, state, emit)
        state.update(out)
        note = state.get("agent_analyses", {}).get(stage_name.replace("_expert", "_expert"), "")
        if note:
            log.info("    ✔ %s note: %s", stage_name, str(note)[:160])

    # ------------------------------------------------------------------
    # Stage 9: Big Boss (final verdict)
    # ------------------------------------------------------------------
    boss_out = _run_stage("big_boss", big_boss, state, emit)
    state.update(boss_out)

    # ------------------------------------------------------------------
    # Emit final payload
    # ------------------------------------------------------------------
    payload = state.get("frontend_payload") or {}
    if not payload:
        try:
            payload = json.loads(state.get("final_audit", "{}"))
        except Exception:
            payload = build_frontend_payload(state)
            state["frontend_payload"] = payload
            state["final_audit"] = json.dumps(payload, ensure_ascii=False)

    final_verdict = (payload.get("final_audit_report") or {}).get("verdict", "UNKNOWN")
    risks = (payload.get("final_audit_report") or {}).get("risks", [])

    log.info("")
    log.info("🏁  PIPELINE COMPLETE")
    log.info("    session_id = %s", session_id)
    log.info("    verdict    = %s", final_verdict)
    log.info("    risks (%d):", len(risks))
    for r in risks:
        log.info("      • %s", str(r)[:120])
    log.info(DIVIDER)

    _emit(emit, "final_payload", payload)
    return state