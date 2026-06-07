import json
from typing import Dict, Any
from pydantic import BaseModel, Field
from state import SharedGraphState
from agents.utils import get_llm, get_db

class V1Response(BaseModel):
    risk_flag: bool = Field(description="Set to True if the git diff carries a risk of repeating a historical incident, otherwise False.")
    risk_reason: str = Field(description="A brief explanation of why the risk is flagged, or why the code is considered safe.")

def reviewer_v1(state: SharedGraphState) -> Dict[str, Any]:
    """
    Performs fast heuristic triage. Looks up similar historical incidents in Hindsight DB.
    If matching historical anomalies are found, calls the LLM to verify the risk.
    """
    print(">>> Reviewer V1: Performing Heuristic Triage against Hindsight DB...")
    git_diff = state.get("git_diff", "")
    
    db = get_db()
    # Find matching incidents in Hindsight
    matched_incidents = db.query_incidents(git_diff, limit=2)
    
    if not matched_incidents:
        print("Reviewer V1: No matching historical incident patterns found in DB. Clearing pipeline.")
        return {
            "risk_flag": False,
            "risk_reason": "No matching historical failure patterns detected in Hindsight database."
        }
    
    print(f"Reviewer V1: Found {len(matched_incidents)} matching historical incident(s). Running LLM verification...")
    
    # Format incidents for LLM review
    incidents_text = ""
    for idx, inc in enumerate(matched_incidents):
        incidents_text += f"\n--- Historical Incident {idx+1}: {inc['title']} (ID: {inc['id']}) ---\n"
        incidents_text += f"Description: {inc['description']}\n"
        incidents_text += f"Symptoms: {', '.join(inc['symptoms'])}\n"
        incidents_text += f"Mitigation: {inc['mitigation']}\n"
        
    system_prompt = (
        "You are an expert DevOps Triage Agent. Your task is to compare a new git diff against "
        "historical incident reports of past systems failures.\n"
        "Analyze if the code modifications inside the git diff risk reproducing the symptoms, root cause, "
        "or vulnerability of the historical incidents.\n"
        "Provide your evaluation in a JSON structure containing:\n"
        "1. risk_flag (boolean): True if there is a realistic risk of repeating the historical failure, False otherwise.\n"
        "2. risk_reason (string): A short explanation summarizing your decision."
    )
    
    user_prompt = (
        f"Git Diff:\n```diff\n{git_diff}\n```\n\n"
        f"Retrieved Historical Incidents:\n{incidents_text}\n"
    )
    
    llm = get_llm()
    try:
        # Request structured output from Groq LLM
        structured_llm = llm.with_structured_output(V1Response)
        response = structured_llm.invoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ])
        risk_flag = response.risk_flag
        risk_reason = response.risk_reason
    except Exception as e:
        print(f"Reviewer V1: Fallback due to structured output exception: {e}")
        # Standard fallback to plain text JSON parsing if structured output has issues
        fallback_prompt = user_prompt + "\nOutput your response ONLY as valid JSON matching the format: {\"risk_flag\": bool, \"risk_reason\": \"text\"}"
        text_response = llm.invoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": fallback_prompt}
        ]).content
        try:
            # Clean possible markdown wrap
            cleaned = text_response.strip().replace("```json", "").replace("```", "").strip()
            data = json.loads(cleaned)
            risk_flag = bool(data.get("risk_flag", False))
            risk_reason = data.get("risk_reason", "Fallback parsed reasoning.")
        except Exception as json_err:
            print(f"Reviewer V1: JSON parsing failed: {json_err}. Raw output: {text_response}")
            risk_flag = True
            risk_reason = f"Unparsed LLM output warning potential risk: {text_response[:100]}"
            
    print(f"Reviewer V1 Decision: Risk Flag = {risk_flag}")
    print(f"Reviewer V1 Reason: {risk_reason}")
    
    return {
        "risk_flag": risk_flag,
        "risk_reason": risk_reason
    }
