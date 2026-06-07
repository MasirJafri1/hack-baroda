from typing import TypedDict, List, Dict, Any, Annotated

def merge_analyses(left: Dict[str, str], right: Dict[str, str]) -> Dict[str, str]:
    """Reducer function to merge agent analyses from parallel nodes."""
    merged = dict(left or {})
    for k, v in (right or {}).items():
        merged[k] = v
    return merged

class SharedGraphState(TypedDict):
    git_diff: str
    metadata: Dict[str, Any]
    hindsight_session_id: str
    risk_flag: bool
    risk_reason: str
    matches_found: int
    retrieval_queries: List[str]
    retrieved_logs: List[Dict[str, Any]]
    # Using the reducer to support parallel fan-out / fan-in updates
    agent_analyses: Annotated[Dict[str, str], merge_analyses]
    loop_count: int
    final_audit: str
    frontend_payload: Dict[str, Any]
