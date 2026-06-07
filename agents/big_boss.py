import json
from typing import Dict, Any
from pydantic import BaseModel, Field
from state import SharedGraphState
from agents.utils import get_llm

class BigBossResponse(BaseModel):
    needs_rereview: bool = Field(description="Set to True if there is a glaring discrepancy or contradiction in the analyses requiring another pass. Else False.")
    re_review_reason: str = Field(description="Reason for requesting a re-review pass, or empty if approved.")
    audit_report: str = Field(description="Synthesized markdown report summarizing issues, vulnerabilities, and exact remediation patches.")

def big_boss(state: SharedGraphState) -> Dict[str, Any]:
    """
    The Big Boss Agent reviews reports from all specialized agents,
    resolves conflicts, synthesizes an executive summary, and decides if
    a reflection / re-review pass is necessary (reflection guardrail).
    """
    print(">>> Big Boss: Synthesizing Specialist Assessments...")
    agent_analyses = state.get("agent_analyses", {})
    git_diff = state.get("git_diff", "")
    loop_count = state.get("loop_count", 0)

    # Format agent analyses for Big Boss review
    specialist_reports = ""
    for agent, report in agent_analyses.items():
        specialist_reports += f"\n=========================================\n"
        specialist_reports += f"Specialist Report: {agent.upper()}\n"
        specialist_reports += f"=========================================\n"
        specialist_reports += f"{report}\n"

    system_prompt = (
        "You are the 'Big Boss' - the Principal Engineering and Release Director. Your job is to "
        "synthesize specialized DevOps audit reports (Git, Cloud, and Code) into an executive-level summary.\n\n"
        "Instructions:\n"
        "1. Read all specialist reports and resolve any contradictions or gaps.\n"
        "2. Formulate a final, comprehensive Markdown audit text. Include a clear 'Verdict' (APPROVED or BLOCKED), "
        "   a summary of risks, and actionable code patches.\n"
        "3. Decide if the current analysis has glaring inconsistencies or missed critical context that requires "
        "   a corrective pass (needs_rereview = True). You should only trigger this if absolutely critical and "
        "   the loop count is 0. Otherwise, set needs_rereview = False.\n\n"
        "Format your response in JSON matching:\n"
        "{\n"
        "  \"needs_rereview\": boolean,\n"
        "  \"re_review_reason\": \"string description of why we are looping back or empty\",\n"
        "  \"audit_report\": \"markdown string here\"\n"
        "}"
    )

    user_prompt = (
        f"Original Git Diff:\n```diff\n{git_diff}\n```\n\n"
        f"Current Loop Count: {loop_count}\n\n"
        f"Specialist Reports Received:\n{specialist_reports}\n"
    )

    llm = get_llm()
    try:
        structured_llm = llm.with_structured_output(BigBossResponse)
        response = structured_llm.invoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ])
        needs_rereview = response.needs_rereview
        re_review_reason = response.re_review_reason
        audit_report = response.audit_report
    except Exception as e:
        print(f"Big Boss: Fallback due to structured output exception: {e}")
        fallback_prompt = user_prompt + "\nOutput your response ONLY as valid JSON matching the format: {\"needs_rereview\": bool, \"re_review_reason\": \"text\", \"audit_report\": \"markdown text\"}"
        text_response = llm.invoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": fallback_prompt}
        ]).content
        try:
            cleaned = text_response.strip().replace("```json", "").replace("```", "").strip()
            data = json.loads(cleaned)
            needs_rereview = bool(data.get("needs_rereview", False))
            re_review_reason = data.get("re_review_reason", "")
            audit_report = data.get("audit_report", "Markdown report fallback.")
        except Exception as json_err:
            print(f"Big Boss: JSON parsing failed: {json_err}. Raw output: {text_response}")
            needs_rereview = False
            re_review_reason = ""
            audit_report = f"# Synthesized DevOps Audit Report\n\n{specialist_reports}"

    # If the Big Boss requests a re-review and we haven't looped yet, flag it
    # We enforce a single-reflection guardrail: only allow looping if loop_count < 1
    if needs_rereview and loop_count >= 1:
        print("Big Boss requested re-review, but loop limit (1) was reached. Forcing approval/end.")
        needs_rereview = False

    print(f"Big Boss: Decision -> Needs Re-Review: {needs_rereview} (Reason: '{re_review_reason}')")
    
    # Store the reason for re-review in metadata if we are looping
    new_metadata = dict(state.get("metadata", {}))
    if needs_rereview:
        new_metadata["last_re_review_reason"] = re_review_reason

    return {
        "final_audit": audit_report,
        "metadata": new_metadata,
        # We pass this flag via metadata or a custom state attribute if needed.
        # But to be cleaner, we can also check this flag in the conditional router.
        # Let's save needs_rereview to metadata so the router can inspect it.
        "metadata": {**new_metadata, "needs_rereview": needs_rereview}
    }
