"""
GitHub Crawler Agent - Usage Examples
Demonstrates various ways to interact with the GitHub crawler agent.
"""

import os
import json
from github_crawler_agent import build_agent_graph, AgentState
from langchain_core.messages import HumanMessage


def example_1_sample_execution():
    """
    Example 1: Basic execution with sample repository
    Matches the main block of the agent
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 1: Basic Execution with MasirJafri1/hack-baroda")
    print("=" * 80)
    
    agent = build_agent_graph()
    
    state = AgentState(
        messages=[
            HumanMessage(
                content="Get the 3 latest commits, look up the diff for the newest commit, "
                        "and crawl open issues for 'MasirJafri1/hack-baroda'."
            )
        ],
        repo_owner="MasirJafri1",
        repo_name="hack-baroda",
        extracted_data={"commits": [], "diffs": [], "issues": []}
    )
    
    result = agent.invoke(state)
    print(json.dumps(result["extracted_data"], indent=2))
    return result


def example_2_commits_only():
    """
    Example 2: Fetch only commits from a repository
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Fetch Commits Only from python/cpython")
    print("=" * 80)
    
    agent = build_agent_graph()
    
    state = AgentState(
        messages=[
            HumanMessage(
                content="Fetch the 5 most recent commits from the python/cpython repository."
            )
        ],
        repo_owner="python",
        repo_name="cpython",
        extracted_data={"commits": [], "diffs": [], "issues": []}
    )
    
    result = agent.invoke(state)
    
    if result["extracted_data"]["commits"]:
        print(f"\nFound {len(result['extracted_data']['commits'])} commits:")
        for commit in result["extracted_data"]["commits"]:
            print(f"  - [{commit['sha']}] {commit['message']} by {commit['author']}")
    
    return result


def example_3_issues_analysis():
    """
    Example 3: Analyze open issues in a repository
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Analyze Open Issues from facebook/react")
    print("=" * 80)
    
    agent = build_agent_graph()
    
    state = AgentState(
        messages=[
            HumanMessage(
                content="Show me all open issues in the facebook/react repository. "
                        "I want to understand what bugs and features are being tracked."
            )
        ],
        repo_owner="facebook",
        repo_name="react",
        extracted_data={"commits": [], "diffs": [], "issues": []}
    )
    
    result = agent.invoke(state)
    
    if result["extracted_data"]["issues"]:
        print(f"\nFound {len(result['extracted_data']['issues'])} issues:")
        open_count = sum(1 for i in result["extracted_data"]["issues"] if i["state"] == "open")
        closed_count = sum(1 for i in result["extracted_data"]["issues"] if i["state"] == "closed")
        print(f"  Open: {open_count}, Closed: {closed_count}")
        
        print("\nFirst 5 open issues:")
        open_issues = [i for i in result["extracted_data"]["issues"] if i["state"] == "open"][:5]
        for issue in open_issues:
            print(f"  - #{issue['number']}: {issue['title']}")
    
    return result


def example_4_diff_inspection():
    """
    Example 4: Inspect specific commit diffs
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 4: Inspect Recent Commit Diffs from golang/go")
    print("=" * 80)
    
    agent = build_agent_graph()
    
    state = AgentState(
        messages=[
            HumanMessage(
                content="Get the most recent commit from golang/go repository and show me "
                        "the changes that were made in that commit."
            )
        ],
        repo_owner="golang",
        repo_name="go",
        extracted_data={"commits": [], "diffs": [], "issues": []}
    )
    
    result = agent.invoke(state)
    
    if result["extracted_data"]["commits"]:
        latest = result["extracted_data"]["commits"][0]
        print(f"\nLatest commit: [{latest['sha']}]")
        print(f"Message: {latest['message']}")
        print(f"Author: {latest['author']}")
    
    if result["extracted_data"]["diffs"]:
        diff = result["extracted_data"]["diffs"][0]
        print(f"\nDiff (truncated to 2000 chars):")
        print(diff["diff"][:500] + "...")
        if diff["truncated"]:
            print("\n[Note: Diff was truncated to prevent token overflow]")
    
    return result


def example_5_comprehensive_analysis():
    """
    Example 5: Comprehensive analysis with all data types
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 5: Comprehensive Analysis of kubernetes/kubernetes")
    print("=" * 80)
    
    agent = build_agent_graph()
    
    state = AgentState(
        messages=[
            HumanMessage(
                content="Give me a comprehensive overview of kubernetes/kubernetes repository. "
                        "I need: the latest 10 commits with their diffs (at least for top 3), "
                        "and all open issues. This will help me understand recent changes and "
                        "what the team is working on."
            )
        ],
        repo_owner="kubernetes",
        repo_name="kubernetes",
        extracted_data={"commits": [], "diffs": [], "issues": []}
    )
    
    result = agent.invoke(state)
    data = result["extracted_data"]
    
    print(f"\n📊 Repository Overview:")
    print(f"   Commits fetched: {len(data['commits'])}")
    print(f"   Diffs captured: {len(data['diffs'])}")
    print(f"   Issues tracked: {len(data['issues'])}")
    
    if data["commits"]:
        print(f"\n📝 Recent Commits:")
        for i, commit in enumerate(data["commits"][:5], 1):
            print(f"   {i}. [{commit['sha']}] {commit['message'][:50]}...")
    
    if data["issues"]:
        open_issues = [i for i in data["issues"] if i["state"] == "open"]
        closed_issues = [i for i in data["issues"] if i["state"] == "closed"]
        print(f"\n🐛 Issues Status:")
        print(f"   Open issues: {len(open_issues)}")
        print(f"   Closed issues: {len(closed_issues)}")
        if open_issues:
            print(f"   Sample open issues:")
            for issue in open_issues[:3]:
                print(f"      - #{issue['number']}: {issue['title'][:60]}...")
    
    return result


def example_6_error_handling():
    """
    Example 6: Demonstrate error handling with invalid repository
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 6: Error Handling with Non-existent Repository")
    print("=" * 80)
    
    agent = build_agent_graph()
    
    state = AgentState(
        messages=[
            HumanMessage(
                content="Fetch commits from totally-fake-user/non-existent-repo"
            )
        ],
        repo_owner="totally-fake-user",
        repo_name="non-existent-repo",
        extracted_data={"commits": [], "diffs": [], "issues": []}
    )
    
    result = agent.invoke(state)
    
    print("\nAgent handled the error gracefully:")
    print(json.dumps(result["extracted_data"], indent=2))
    print("\n[Note: Tool returned error status, agent continues without crashing]")
    
    return result


def main():
    """
    Run all examples
    """
    print("\n" + "=" * 80)
    print("GitHub Crawler Agent - Usage Examples")
    print("=" * 80)
    print("\nThese examples demonstrate different ways to use the GitHub crawler agent.")
    print("Each example shows a different use case and output format.")
    
    try:
        # Uncomment the examples you want to run
        # Be aware: running all examples uses multiple API calls
        
        # example_1_sample_execution()
        # example_2_commits_only()
        # example_3_issues_analysis()
        # example_4_diff_inspection()
        # example_5_comprehensive_analysis()
        example_6_error_handling()
        
        print("\n" + "=" * 80)
        print("✅ Examples completed successfully!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Error during execution: {str(e)}")
        print("\nMake sure you have:")
        print("  1. Set GITHUB_TOKEN environment variable (optional but recommended)")
        print("  2. Set OPENAI_API_KEY environment variable")
        print("  3. Installed all dependencies: pip install -r requirements.txt")


if __name__ == "__main__":
    main()
