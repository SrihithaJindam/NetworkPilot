"""
graph.py
========
Constructs the LangGraph StateGraph workflow for NetworkPilot.

Core LangGraph concepts demonstrated here:
1. StateGraph(AgentState): The graph structure tracking state.
2. add_node(): Attaching Python functions as executable steps.
3. add_edge(): Deterministic transitions between steps.
4. add_conditional_edges(): Dynamic routing based on runtime state (e.g. relevance score and human decision).
5. compile(): Producing the runnable agent graph.
"""

from langgraph.graph import StateGraph, END
from state import AgentState
from nodes import (
    discover_node,
    evaluate_relevance_node,
    check_calendar_node,
    draft_email_node,
    human_approval_node,
    send_outreach_node,
)


# ---------------------------------------------------------------------------
# Conditional Routing Functions
# ---------------------------------------------------------------------------

def route_by_relevance(state: AgentState) -> str:
    """
    Conditional Edge Router 1:
    Decides whether the match is high enough to warrant drafting outreach.
    - If match_score >= 60 -> Proceed to check calendar & draft email.
    - If match_score < 60  -> Skip candidate and terminate.
    """
    score = state.get("match_score", 0)
    if score >= 60:
        print(f"\n[Router] Match score {score} >= 60 -> Routing to 'check_calendar'.")
        return "check_calendar"
    else:
        print(f"\n[Router] Match score {score} < 60 -> Low relevance. Terminating workflow.")
        return END


def route_by_human_decision(state: AgentState) -> str:
    """
    Conditional Edge Router 2:
    Inspects human approval decision:
    - If 'approved' -> Proceed to 'send_outreach'.
    - If 'rejected' -> Discard and terminate (END).
    """
    decision = state.get("human_decision")
    if decision == "approved":
        print("\n[Router] Human approved -> Routing to 'send_outreach'.")
        return "send_outreach"
    else:
        print("\n[Router] Human rejected -> Terminating workflow without sending.")
        return END


# ---------------------------------------------------------------------------
# Graph Builder
# ---------------------------------------------------------------------------

def create_networking_graph():
    """
    Assembles and compiles the LangGraph StateGraph.
    """
    # 1. Initialize StateGraph with the schema
    workflow = StateGraph(AgentState)

    # 2. Register all Nodes
    workflow.add_node("discover", discover_node)
    workflow.add_node("evaluate_relevance", evaluate_relevance_node)
    workflow.add_node("check_calendar", check_calendar_node)
    workflow.add_node("draft_email", draft_email_node)
    workflow.add_node("human_approval", human_approval_node)
    workflow.add_node("send_outreach", send_outreach_node)

    # 3. Set the Entry Point
    workflow.set_entry_point("discover")

    # 4. Add Edges & Conditional Routing
    # discover -> evaluate_relevance
    workflow.add_edge("discover", "evaluate_relevance")

    # evaluate_relevance -> (check_calendar OR END)
    workflow.add_conditional_edges(
        "evaluate_relevance",
        route_by_relevance,
        {
            "check_calendar": "check_calendar",
            END: END,
        },
    )

    # check_calendar -> draft_email -> human_approval
    workflow.add_edge("check_calendar", "draft_email")
    workflow.add_edge("draft_email", "human_approval")

    # human_approval -> (send_outreach OR END)
    workflow.add_conditional_edges(
        "human_approval",
        route_by_human_decision,
        {
            "send_outreach": "send_outreach",
            END: END,
        },
    )

    # send_outreach -> END
    workflow.add_edge("send_outreach", END)

    # 5. Compile into an executable graph app
    return workflow.compile()

