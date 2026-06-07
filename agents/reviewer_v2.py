import json
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from state import SharedGraphState
from agents.utils import get_llm

class V2Response(BaseModel):
    retrieval_queries: List[str] = Field(description="List of 2 to 4 search queries to fetch relevant logs or PR histories.")

def reviewer_v2(state: SharedGraphState) -> Dict[str, Any]:
    """
    Reviewer V2 formulates search criteria / query strategies to retrieve
    historical files, logs, or issues associated with the risk flagged by V1.
    """
    print(">>> Reviewer V2: Formulating Telemetry & Historical Search Queries...")
    git_diff = state.get("git_diff", "")
    risk_reason = state.get("risk_reason", "")
    
    system_prompt = (
        "You are an Advanced DevOps Triage Architect. A code change has been flagged "
        "as carrying risk. Your task is to write a list of 2-4 targeted search queries "
        "to retrieve telemetry logs, historical pull requests, issues, or hotfixes "
        "that would help engineers analyze and resolve this issue.\n"
        "Keep queries short, precise, and focused on logs or issues (e.g., 'java.io.IOException: Too many open files', 'Terraform open SSH port 22', etc.).\n"
        "Provide your output as a JSON object containing:\n"
        "- retrieval_queries: list of strings."
    )
    
    user_prompt = (
        f"Git Diff:\n```diff\n{git_diff}\n```\n\n"
        f"Risk Reason Flagged by V1:\n{risk_reason}\n"
    )
    
    llm = get_llm()
    try:
        structured_llm = llm.with_structured_output(V2Response)
        response = structured_llm.invoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ])
        queries = response.retrieval_queries
    except Exception as e:
        print(f"Reviewer V2: Fallback due to structured output exception: {e}")
        fallback_prompt = user_prompt + "\nOutput your response ONLY as valid JSON: {\"retrieval_queries\": [\"query1\", \"query2\"]}"
        text_response = llm.invoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": fallback_prompt}
        ]).content
        try:
            cleaned = text_response.strip().replace("```json", "").replace("```", "").strip()
            data = json.loads(cleaned)
            queries = list(data.get("retrieval_queries", []))
        except Exception as json_err:
            print(f"Reviewer V2: JSON parsing failed: {json_err}. Raw: {text_response}")
            # Dynamic fallback query based on risk reason keywords
            queries = [risk_reason[:100], "DevOps failure log"]

    print(f"Reviewer V2 Formulated Queries: {queries}")
    return {
        "retrieval_queries": queries
    }
