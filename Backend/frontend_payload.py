from __future__ import annotations

from typing import Any, Dict, List, Optional


def build_frontend_payload(
    state: Dict[str, Any],
    verdict: Optional[str] = None,
    risks: Optional[List[str]] = None,
    mitigation_patches: Optional[List[str]] = None,
    example_patch_code: str = "",
    conclusion: str = "",
) -> Dict[str, Any]:
    metadata = state.get("metadata", {}) or {}
    classifications = metadata.get("classification", {}) or {}
    agent_analyses = state.get("agent_analyses", {}) or {}
    risk_flag = bool(state.get("risk_flag", False))
    matches_found = int(state.get("matches_found", 0) or 0)
    reasoning = state.get("risk_reason", "") or ""

    if verdict is None:
        if state.get("metadata", {}).get("needs_rereview", False):
            verdict = "REQUIRES_REVIEW"
        elif risk_flag:
            verdict = "BLOCKED"
        else:
            verdict = "APPROVED"

    if risks is None:
        risks = [] if not risk_flag else [reasoning or "Historical risk pattern matched."]

    if mitigation_patches is None:
        mitigation_patches = []
        for key in ("git_expert", "cloud_expert", "code_expert"):
            note = agent_analyses.get(key, "")
            if note:
                mitigation_patches.append(note)

    if not conclusion:
        conclusion = state.get("final_audit", "") or (
            "The change set is low risk based on the current Hindsight history and specialist review."
            if verdict == "APPROVED"
            else "The system detected conflicting or incomplete context and recommends one more review pass."
            if verdict == "REQUIRES_REVIEW"
            else "The change set should not be merged until the listed risks are addressed."
        )

    return {
        "session_id": state.get("hindsight_session_id", ""),
        "pipeline_metadata": {
            "author": metadata.get("author", "unknown_developer"),
            "changed_files": metadata.get("changed_files", []),
            "classification": {
                "cloud_infra": classifications.get("cloud_infra", []),
                "git_meta": classifications.get("git_meta", []),
                "app_code": classifications.get("app_code", []),
            },
        },
        "triage_layer": {
            "risk_flagged": risk_flag,
            "matches_found": matches_found,
            "reasoning": reasoning,
        },
        "expert_analysis": {
            "cloud_expert_notes": agent_analyses.get("cloud_expert", ""),
            "code_expert_notes": agent_analyses.get("code_expert", ""),
            "git_expert_notes": agent_analyses.get("git_expert", ""),
        },
        "final_audit_report": {
            "verdict": verdict,
            "risks": risks,
            "mitigation_patches": mitigation_patches,
            "example_patch_code": example_patch_code,
            "conclusion": conclusion,
        },
    }