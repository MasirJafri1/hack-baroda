import re
from typing import Dict, Any
from state import SharedGraphState
from github_crawler_agent import build_agent_graph
from langchain_core.messages import HumanMessage

def parse_github_repo(repo_str: str) -> tuple[str, str] | None:
    if not repo_str:
        return None
    repo_str = repo_str.strip()
    if repo_str.startswith("http"):
        # Match pattern like https://github.com/owner/repo
        match = re.search(r"github\.com/([^/]+)/([^/.]+)", repo_str)
        if match:
            return match.group(1), match.group(2)
    else:
        # Match pattern like owner/repo
        parts = repo_str.split("/")
        if len(parts) == 2:
            return parts[0].strip(), parts[1].strip()
    return None

def github_crawler_node(state: SharedGraphState) -> Dict[str, Any]:
    """
    Checks if a github_repo is provided. If so, runs the github_crawler_agent to fetch
    the latest commits, commit diffs, and open issues. Updates state with the retrieved diff.
    """
    # Check top-level or within metadata
    github_repo = state.get("github_repo") or state.get("metadata", {}).get("github_repo")
        
    if not github_repo:
        print(">>> GitHub Crawler Node: No github_repo provided. Skipping crawling stage.")
        return {}
        
    parsed = parse_github_repo(github_repo)
    if not parsed:
        print(f">>> GitHub Crawler Node: Could not parse github_repo '{github_repo}'. Skipping.")
        return {}
        
    owner, repo = parsed
    print(f">>> GitHub Crawler Node: Starting crawl for repository {owner}/{repo}...")
    
    try:
        agent = build_agent_graph()
        crawler_state = {
            "messages": [
                HumanMessage(
                    content=f"Get the 3 latest commits, look up the diff for the newest commit, and crawl open issues for '{owner}/{repo}'."
                )
            ],
            "repo_owner": owner,
            "repo_name": repo,
            "extracted_data": {
                "commits": [],
                "diffs": [],
                "issues": []
            }
        }
        
        result = agent.invoke(crawler_state)
        extracted = result.get("extracted_data", {})
        
        # Extract the latest commit diff
        git_diff = ""
        diffs = extracted.get("diffs", [])
        if diffs:
            git_diff = diffs[0].get("diff", "")
        else:
            print(">>> GitHub Crawler Node: No diff retrieved by crawler.")
            
        print(f">>> GitHub Crawler Node: Successfully crawled {owner}/{repo}.")
        
        # Update metadata with crawler data
        new_metadata = dict(state.get("metadata", {}))
        new_metadata["github_repo"] = github_repo
        new_metadata["github_data"] = {
            "commits": extracted.get("commits", []),
            "issues": extracted.get("issues", [])
        }
        
        return {
            "git_diff": git_diff,
            "metadata": new_metadata
        }
    except Exception as e:
        print(f"[ERROR] GitHub Crawler Node failed: {e}")
        return {}
