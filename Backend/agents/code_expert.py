from typing import Dict, Any
from state import SharedGraphState
from agents.utils import get_llm

def code_expert(state: SharedGraphState) -> Dict[str, Any]:
    """
    Code Expert Agent reviews application source code changes to detect software bugs,
    memory/resource leaks, connection management mistakes, and application vulnerabilities.
    """
    print(">>> Code Expert: Analyzing Application Code patterns...")
    git_diff = state.get("git_diff", "")
    retrieved_logs = state.get("retrieved_logs", [])
    
    system_prompt = (
        "You are an Elite Principal Software Engineer and Security Code Auditor. "
        "Your task is to analyze application source code modifications in the git diff and review "
        "historical failure logs to detect runtime or vulnerability risks.\n\n"
        "Instructions:\n"
        "1. Focus on application-level source files (Python, Javascript, Typescript, Java, etc.).\n"
        "2. Look for memory leaks, connection pooling failures (e.g. unclosed sockets, unclosed files, DB connections not released in a 'finally' block), "
        "   SQL injection risks (string interpolation in SQL commands), and logic errors.\n"
        "3. Incorporate context from retrieved exception logs if they trace to app issues.\n"
        "4. If no application code modifications are present or clean, state that the Application Code assessment is clear.\n"
        "5. Write your output in clear Markdown with headers, identifying findings and proposing mitigation patches."
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
    print("Code Expert: Completed analysis.")
    
    return {
        "agent_analyses": {"code_expert": analysis}
    }
