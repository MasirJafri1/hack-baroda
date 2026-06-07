from typing import Dict, Any
from state import SharedGraphState
from agents.utils import get_llm

def cloud_expert(state: SharedGraphState) -> Dict[str, Any]:
    """
    Cloud Expert Agent analyzes Infrastructure as Code (IaC) files like Terraform,
    Dockerfiles, and Kubernetes YAML configurations to detect security misconfigurations,
    unprivileged user omissions, and unpinned base images.
    """
    print(">>> Cloud Expert: Analyzing Cloud Infrastructure & IaC patterns...")
    git_diff = state.get("git_diff", "")
    retrieved_logs = state.get("retrieved_logs", [])
    
    system_prompt = (
        "You are a Principal Cloud Infrastructure Architect and Site Reliability Engineer. "
        "Your task is to analyze the git diff and retrieved incident telemetry to identify infrastructure security risks "
        "and architectural vulnerabilities.\n\n"
        "Instructions:\n"
        "1. Focus solely on Cloud IaC configurations (Terraform, Dockerfile, Kubernetes yml, security groups, port bindings).\n"
        "2. Look for patterns like open CIDRs (0.0.0.0/0 on sensitive ports), container running as root, and unpinned base image tags (e.g. node:latest).\n"
        "3. Cross-reference findings with the retrieved compliance/log alerts.\n"
        "4. If no infrastructure changes or issues are detected, state that the Cloud assessment is clear.\n"
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
    print("Cloud Expert: Completed analysis.")
    
    return {
        "agent_analyses": {"cloud_expert": analysis}
    }
