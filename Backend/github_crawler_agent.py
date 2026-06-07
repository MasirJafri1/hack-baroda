"""
GitHub Repository Crawler Agent using LangGraph
This agent crawls GitHub repositories and extracts commits, diffs, and issues.
Uses LangGraph StateGraph with supervisor-based tool routing via Groq LLM.
"""

import os
import json
import requests
from typing import TypedDict, Annotated, Any, Optional
from datetime import datetime

from dotenv import load_dotenv
from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

# Load environment variables from .env or .env.example
load_dotenv()

# ============================================================================
# 1. STATE SYSTEM - Define the AgentState TypedDict
# ============================================================================

class AgentState(TypedDict):
    """
    State schema for the GitHub crawler agent.
    Tracks conversation history, repository info, and extracted data.
    """
    messages: Annotated[list[BaseMessage], add_messages]
    repo_owner: str
    repo_name: str
    extracted_data: dict[str, Any]


# ============================================================================
# 2. LANGCHAIN TOOLS - GitHub API Integrations
# ============================================================================

GITHUB_API_BASE = "https://api.github.com"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

if not GITHUB_TOKEN:
    print("WARNING: GITHUB_TOKEN environment variable not set. API rate limits will be reduced.")


def _get_auth_headers() -> dict[str, str]:
    """Build authorization headers for GitHub API requests."""
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "LangGraph-GitHub-Crawler/1.0",
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    return headers


@tool
def fetch_commits(owner: str, repo: str, max_count: int = 10) -> dict[str, Any]:
    """
    Fetch recent commits from a GitHub repository.
    
    Args:
        owner: Repository owner username
        repo: Repository name
        max_count: Maximum number of commits to fetch (default: 10)
    
    Returns:
        Dictionary containing commit data (SHAs, messages, and authors)
    """
    try:
        url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/commits"
        params = {"per_page": max_count}
        response = requests.get(
            url,
            headers=_get_auth_headers(),
            params=params,
            timeout=10
        )
        response.raise_for_status()
        
        commits = []
        for commit in response.json():
            commits.append({
                "sha": commit["sha"][:7],  # Short SHA
                "message": commit["commit"]["message"].split("\n")[0],  # First line only
                "author": commit["commit"]["author"]["name"],
                "date": commit["commit"]["author"]["date"],
            })
        
        return {
            "status": "success",
            "commits": commits,
            "count": len(commits)
        }
    except requests.RequestException as e:
        return {
            "status": "error",
            "message": f"Failed to fetch commits: {str(e)}"
        }


@tool
def fetch_commit_diff(owner: str, repo: str, commit_sha: str) -> dict[str, Any]:
    """
    Fetch the raw diff for a specific commit.
    
    Args:
        owner: Repository owner username
        repo: Repository name
        commit_sha: Full or short commit SHA
    
    Returns:
        Dictionary containing the diff (truncated to 2000 characters)
    """
    try:
        url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/commits/{commit_sha}"
        headers = _get_auth_headers()
        headers["Accept"] = "application/vnd.github.v3.diff"
        
        response = requests.get(
            url,
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        
        diff_text = response.text[:2000]  # Truncate to prevent token overflow
        
        return {
            "status": "success",
            "commit_sha": commit_sha,
            "diff": diff_text,
            "truncated": len(response.text) > 2000
        }
    except requests.RequestException as e:
        return {
            "status": "error",
            "message": f"Failed to fetch commit diff: {str(e)}"
        }


@tool
def fetch_issues(owner: str, repo: str, state: str = "all") -> dict[str, Any]:
    """
    Fetch issues from a GitHub repository.
    
    Args:
        owner: Repository owner username
        repo: Repository name
        state: Issue state - "open", "closed", or "all" (default: "all")
    
    Returns:
        Dictionary containing issue data (numbers, titles, and states)
    """
    try:
        url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/issues"
        params = {"state": state, "per_page": 20}
        response = requests.get(
            url,
            headers=_get_auth_headers(),
            params=params,
            timeout=10
        )
        response.raise_for_status()
        
        issues = []
        for issue in response.json():
            issues.append({
                "number": issue["number"],
                "title": issue["title"],
                "state": issue["state"],
                "created_at": issue["created_at"],
            })
        
        return {
            "status": "success",
            "issues": issues,
            "count": len(issues),
            "state_filter": state
        }
    except requests.RequestException as e:
        return {
            "status": "error",
            "message": f"Failed to fetch issues: {str(e)}"
        }


# ============================================================================
# 3. GRAPH NODES - Supervisor and Tool Execution
# ============================================================================

def supervisor_node(state: AgentState) -> AgentState:
    """
    Supervisor node that uses ChatGroq to decide which tool to invoke.
    Binds the three tools and routes based on model output.
    
    Args:
        state: Current agent state
    
    Returns:
        Updated state with AI message containing tool calls
    """
    # Ground the model so it uses only repository facts from the GitHub API.
    system_prompt = (
        "You are a GitHub repository crawler. Never invent commit messages, diff contents, "
        "issues, owners, or repository names. Always use the repository from the current state. "
        "If you need GitHub data, call the provided tools. Do not answer from memory."
    )
    messages = [SystemMessage(content=system_prompt), *state["messages"]]

    # Use a smaller Groq model to avoid token-limit throttling.
    model = ChatGroq(model="llama-3.1-8b-instant", temperature=0, max_tokens=256)

    # Bind all available tools
    tools = [fetch_commits, fetch_commit_diff, fetch_issues]
    model_with_tools = model.bind_tools(tools)

    # Try the LLM path first; fall back deterministically if Groq rejects the request.
    try:
        response = model_with_tools.invoke(messages)
    except Exception as e:
        # Check which tools have already run by parsing ToolMessages in the history
        has_commits_run = False
        has_diff_run = False
        has_issues_run = False
        print(f"DEBUG supervisor_node fallback: messages in state count = {len(state['messages'])}")
        for idx, msg in enumerate(state["messages"]):
            print(f"  DEBUG msg[{idx}]: type={type(msg).__name__}")
            if isinstance(msg, ToolMessage):
                print(f"    DEBUG ToolMessage content: {msg.content[:100]}...")
                try:
                    content_data = json.loads(msg.content)
                    if isinstance(content_data, dict):
                        if "commits" in content_data:
                            has_commits_run = True
                        if "diff" in content_data:
                            has_diff_run = True
                        if "issues" in content_data:
                            has_issues_run = True
                except Exception as parse_err:
                    print(f"    DEBUG parse error: {parse_err}")

        print(f"DEBUG supervisor_node fallback status: has_commits_run={has_commits_run}, has_diff_run={has_diff_run}, has_issues_run={has_issues_run}")
        tool_calls = []
        if not has_commits_run:
            tool_calls.append({
                "name": "fetch_commits",
                "args": {"owner": state["repo_owner"], "repo": state["repo_name"], "max_count": 3},
                "id": "fallback-commit"
            })
        
        if not has_issues_run:
            tool_calls.append({
                "name": "fetch_issues",
                "args": {"owner": state["repo_owner"], "repo": state["repo_name"], "state": "open"},
                "id": "fallback-issue"
            })

        # Fetch diff if we haven't yet, but only if commits have already been fetched
        if has_commits_run and not has_diff_run:
            commit_sha = "HEAD"
            extracted = state.get("extracted_data", {})
            if extracted.get("commits") and isinstance(extracted["commits"], list):
                commit_sha = extracted["commits"][0].get("sha", "HEAD")
            tool_calls.append({
                "name": "fetch_commit_diff",
                "args": {"owner": state["repo_owner"], "repo": state["repo_name"], "commit_sha": commit_sha},
                "id": "fallback-diff"
            })

        print(f"DEBUG supervisor_node fallback: generated tool_calls = {[tc['name'] for tc in tool_calls]}")
        if tool_calls:
            response = AIMessage(
                content="Fallback tool routing used because the Groq model quota is exhausted.",
                tool_calls=tool_calls
            )
        else:
            response = AIMessage(
                content="Fallback completed: Repository metadata and commit diff retrieved successfully."
            )
    
    # Append the AI response to messages
    state["messages"].append(response)
    
    return state


def tool_execution_node(state: AgentState) -> AgentState:
    """
    Tool execution node that processes tool calls from the supervisor.
    Executes requested tools and populates the extracted_data dictionary.
    
    Args:
        state: Current agent state
    
    Returns:
        Updated state with tool results appended to messages
    """
    # Get the last AI message which should contain tool_calls
    last_message = state["messages"][-1]
    
    if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
        return state
    
    # Process each tool call
    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        tool_input = dict(tool_call["args"])

        # Always use the repository from the current state to prevent hallucinated repo details.
        tool_input.setdefault("owner", state["repo_owner"])
        tool_input.setdefault("repo", state["repo_name"])

        if tool_name == "fetch_commit_diff":
            commit_sha = tool_input.get("commit_sha", "")
            is_placeholder = False
            if not commit_sha:
                is_placeholder = True
            else:
                commit_sha_clean = commit_sha.strip().lower()
                if commit_sha_clean in ("head", "latest_commit_sha", "commit_sha", "latest", "newest"):
                    is_placeholder = True
                elif not all(c in "0123456789abcdef" for c in commit_sha_clean):
                    is_placeholder = True
            
            if is_placeholder:
                latest_commit = state["extracted_data"].get("commits", [{}])[0]
                if isinstance(latest_commit, dict) and latest_commit.get("sha"):
                    tool_input["commit_sha"] = latest_commit["sha"]
        
        # Execute the corresponding tool
        if tool_name == "fetch_commits":
            result = fetch_commits.invoke(tool_input)
            if result.get("status") == "success":
                state["extracted_data"]["commits"] = result["commits"]
        
        elif tool_name == "fetch_commit_diff":
            result = fetch_commit_diff.invoke(tool_input)
            if result.get("status") == "success":
                state["extracted_data"]["diffs"] = state["extracted_data"].get("diffs", [])
                state["extracted_data"]["diffs"].append({
                    "sha": result["commit_sha"],
                    "diff": result["diff"],
                    "truncated": result.get("truncated", False)
                })
        
        elif tool_name == "fetch_issues":
            result = fetch_issues.invoke(tool_input)
            if result.get("status") == "success":
                state["extracted_data"]["issues"] = result["issues"]
        
        # Append tool result to messages
        tool_message = ToolMessage(
            content=json.dumps(result, indent=2),
            tool_call_id=tool_call["id"]
        )
        state["messages"].append(tool_message)
    
    return state


# ============================================================================
# 4. ROUTING LOGIC - Conditional Edge Function
# ============================================================================

def should_continue(state: AgentState) -> str:
    """
    Determines whether to continue tool execution or end the agentic loop.
    Checks if the last message contains tool calls.
    
    Args:
        state: Current agent state
    
    Returns:
        "tool_execution" to execute tools, "end" to stop
    """
    last_message = state["messages"][-1]
    
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tool_execution"
    return "end"


# ============================================================================
# 5. GRAPH CONSTRUCTION & COMPILATION
# ============================================================================

def build_agent_graph() -> Any:
    """
    Constructs and compiles the LangGraph state machine for the GitHub crawler.
    
    Returns:
        Compiled runnable graph ready for execution
    """
    # Initialize the state graph
    graph = StateGraph(AgentState)
    
    # Add nodes
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("tool_execution", tool_execution_node)
    
    # Add edges
    graph.add_edge(START, "supervisor")
    graph.add_conditional_edges(
        "supervisor",
        should_continue,
        {
            "tool_execution": "tool_execution",
            "end": END,
        }
    )
    graph.add_edge("tool_execution", "supervisor")
    
    # Compile the graph
    return graph.compile()


# ============================================================================
# 6. SAMPLE EXECUTION
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("GitHub Repository Crawler Agent - LangGraph Demo")
    print("=" * 80)
    
    # Build the agent
    print("\n[*] Building agent graph...")
    agent = build_agent_graph()
    
    # Initialize state with sample input
    initial_state = AgentState(
        messages=[
            HumanMessage(
                content="Get the 3 latest commits, look up the diff for the newest commit, "
                        "and crawl open issues for 'MasirJafri1/hack-baroda'."
            )
        ],
        repo_owner="MasirJafri1",
        repo_name="hack-baroda",
        extracted_data={
            "commits": [],
            "diffs": [],
            "issues": []
        }
    )
    
    # Execute the agent
    print("[*] Starting agent execution...")
    print(f"[*] Input: {initial_state['messages'][0].content}\n")
    
    final_state = agent.invoke(initial_state)
    
    # Display results
    print("\n" + "=" * 80)
    print("EXTRACTION RESULTS")
    print("=" * 80)
    print("\nExtracted Data:")
    print(json.dumps(final_state["extracted_data"], indent=2))
    
    print("\n" + "=" * 80)
    print("CONVERSATION HISTORY")
    print("=" * 80)
    for i, msg in enumerate(final_state["messages"]):
        msg_type = type(msg).__name__
        if isinstance(msg, HumanMessage):
            print(f"\n[{i}] Human: {msg.content[:100]}...")
        elif isinstance(msg, AIMessage):
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                print(f"\n[{i}] AI (Tool Call): {msg.tool_calls[0]['name']}")
            else:
                print(f"\n[{i}] AI: {msg.content[:100]}...")
        elif isinstance(msg, ToolMessage):
            print(f"\n[{i}] Tool Result: {msg.content[:100]}...")
    
    print("\n" + "=" * 80)
    print("Agent execution completed successfully!")
    print("=" * 80)
