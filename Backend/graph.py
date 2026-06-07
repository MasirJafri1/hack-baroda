from langgraph.graph import StateGraph, START, END
from state import SharedGraphState
from agents.github_crawler_node import github_crawler_node
from agents.context_agent import context_agent
from agents.reviewer_v1 import reviewer_v1
from agents.reviewer_v2 import reviewer_v2
from agents.retrieval_agent import retrieval_agent
from agents.git_expert import git_expert
from agents.cloud_expert import cloud_expert
from agents.code_expert import code_expert
from agents.big_boss import big_boss

def increment_loop(state: SharedGraphState):
    """Intermediate node to increment loop counter before repeating context analysis."""
    current_loop = state.get("loop_count", 0)
    print(f"\n--- Graph State Transition: Incrementing Loop Count ({current_loop} -> {current_loop + 1}) ---")
    return {"loop_count": current_loop + 1}

# Initialize State Graph
workflow = StateGraph(SharedGraphState)

# Register Nodes
workflow.add_node("github_crawler", github_crawler_node)
workflow.add_node("context_agent", context_agent)
workflow.add_node("reviewer_v1", reviewer_v1)
workflow.add_node("reviewer_v2", reviewer_v2)
workflow.add_node("retrieval_agent", retrieval_agent)
workflow.add_node("git_expert", git_expert)
workflow.add_node("cloud_expert", cloud_expert)
workflow.add_node("code_expert", code_expert)
workflow.add_node("big_boss", big_boss)
workflow.add_node("increment_loop", increment_loop)

# Register Static Edges
workflow.add_edge(START, "github_crawler")
workflow.add_edge("github_crawler", "context_agent")
workflow.add_edge("context_agent", "reviewer_v1")

workflow.add_edge("reviewer_v2", "retrieval_agent")

# Parallel Fan-Out
workflow.add_edge("retrieval_agent", "git_expert")
workflow.add_edge("retrieval_agent", "cloud_expert")
workflow.add_edge("retrieval_agent", "code_expert")

# Parallel Fan-In (Join)
workflow.add_edge("git_expert", "big_boss")
workflow.add_edge("cloud_expert", "big_boss")
workflow.add_edge("code_expert", "big_boss")

# Loopback Edge
workflow.add_edge("increment_loop", "context_agent")

# Conditional Router: Post Reviewer V1 Triage
def route_post_v1(state: SharedGraphState):
    risk_flag = state.get("risk_flag", False)
    if risk_flag:
        print(">>> Router V1: Risk detected. Routing to Reviewer V2 (Deep Dive).")
        return "reviewer_v2"
    else:
        print(">>> Router V1: No risk detected. Routing directly to END (Cleared).")
        return END

workflow.add_conditional_edges(
    "reviewer_v1",
    route_post_v1,
    {
        "reviewer_v2": "reviewer_v2",
        END: END
    }
)

# Conditional Router: Post Big Boss Guardrail
def route_post_big_boss(state: SharedGraphState):
    metadata = state.get("metadata", {})
    needs_rereview = metadata.get("needs_rereview", False)
    loop_count = state.get("loop_count", 0)

    if needs_rereview and loop_count < 1:
        print(">>> Guardrail Router: Big Boss requested reflection pass. Looping back.")
        return "increment_loop"
    else:
        print(">>> Guardrail Router: Approved / Final pass complete. Routing to END.")
        return END

workflow.add_conditional_edges(
    "big_boss",
    route_post_big_boss,
    {
        "increment_loop": "increment_loop",
        END: END
    }
)

# Compile the Workflow
app = workflow.compile()
