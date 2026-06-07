from typing import Dict, Any
from state import SharedGraphState
from agents.utils import get_llm

def git_expert(state: SharedGraphState) -> Dict[str, Any]:
    """
    Git Expert Agent analyzes git metadata, branch management, deletions,
    and potential secrets exposure (e.g., credentials, keys, env files).
    """
    print(">>> Git Expert: Analyzing Git metadata & secrets leak patterns...")
    git_diff = state.get("git_diff", "")
    retrieved_logs = state.get("retrieved_logs", [])
    
    system_prompt = (
        "You are a Senior DevOps Security and Git Expert. Your job is to analyze the git diff "
        "and retrieved incident telemetry to identify git-related violations, branch issues, "
        "improper exclusions, and exposed credentials or configuration secrets (like API keys, passwords, "
        "AWS tokens, DATABASE_URL, or private key blocks).\n\n"
        "Instructions:\n"
        "1. Focus solely on git metadata, .gitignore rules, and secrets leaks in the diff.\n"
        "2. Review the retrieved log telemetry to contextualize if a leak was scanned.\n"
        "3. If nothing is found, state that the Git assessment is clear.\n"
        "4. Write your output in clear Markdown with headers, identifying findings and proposing mitigation patches."
    )
    
    user_prompt = (
        f"Git Diff:\n```diff\n{git_diff}\n```\n\n"
        f"Retrieved Telemetry:\n{retrieved_logs}\n"
    )
    
    llm = get_llm()
    response = llm.invoke([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ])
    
    analysis = response.content
    print("Git Expert: Completed analysis.")
    
    return {
        "agent_analyses": {"git_expert": analysis}
    }
