"""
nodes.py
========
The core LangGraph Node functions.

In LangGraph:
- A Node is a Python function: `node(state: AgentState) -> dict`
- It receives the graph state as input.
- It returns a dictionary containing ONLY the keys it wants to update in the state.
"""

from typing import Dict, Any
from state import AgentState, EmailDraft
from services import (
    fetch_candidate_profiles,
    get_calendar_slots,
    call_llm_for_relevance,
    call_llm_for_draft,
)


def discover_node(state: AgentState) -> Dict[str, Any]:
    """
    Node 1: Discover relevant professionals.
    Uses Apify (or fallback) based on the search query.
    """
    print("\n" + "=" * 60)
    print("🔍 [Node: discover_node] Searching for candidate professionals...")
    query = state.get("search_query", "AI Agent Engineer")
    leads = fetch_candidate_profiles(
        query=query,
        role=state.get("user_role", ""),
        interests=state.get("user_interests", []),
        count=3,
    )

    if not leads:
        print("   ❌ No candidates found.")
        return {"discovered_leads": [], "current_lead": None, "status": "no_leads"}

    # Pick the candidate to process (or top discovered lead)
    top_lead = state.get("current_lead") or leads[0]
    print(f"   ✅ Discovered {len(leads)} candidates. Selected: {top_lead['name']} ({top_lead['headline']})")

    return {
        "discovered_leads": leads,
        "current_lead": top_lead,
        "status": "leads_discovered",
    }


def evaluate_relevance_node(state: AgentState) -> Dict[str, Any]:
    """
    Node 2: Evaluate synergy & shared interests between user and candidate.
    Computes a match score (0-100), reasoning, and shared topic overlap.
    """
    candidate = state.get("current_lead")
    if not candidate:
        return {"match_score": 0, "match_reasoning": "No candidate to evaluate.", "status": "evaluation_failed"}

    print("\n" + "=" * 60)
    print(f"🧠 [Node: evaluate_relevance_node] Evaluating match with {candidate['name']}...")

    score, reasoning, shared = call_llm_for_relevance(
        user_role=state.get("user_role", ""),
        user_interests=state.get("user_interests", []),
        user_goal=state.get("user_goal", ""),
        candidate=candidate,
    )

    print(f"   📊 Match Score: {score}/100")
    print(f"   💡 Reasoning:   {reasoning}")
    print(f"   🤝 Shared Topics: {', '.join(shared) if shared else 'None detected'}")

    return {
        "match_score": score,
        "match_reasoning": reasoning,
        "shared_interests": shared,
        "status": "evaluated",
    }


def check_calendar_node(state: AgentState) -> Dict[str, Any]:
    """
    Node 3: Fetch open coffee chat availability.
    Finds real upcoming time slots to propose in the outreach.
    """
    print("\n" + "=" * 60)
    print("📅 [Node: check_calendar_node] Checking calendar for open coffee chat windows...")
    slots = get_calendar_slots(num_slots=3)
    for slot in slots:
        print(f"   • Available slot: {slot}")

    return {
        "available_slots": slots,
        "status": "slots_checked",
    }


def draft_email_node(state: AgentState) -> Dict[str, Any]:
    """
    Node 4: Draft a personalized coffee chat outreach email.
    Incorporates candidate background, mutual interests, and calendar slots.
    """
    candidate = state["current_lead"]
    print("\n" + "=" * 60)
    print(f"✍️  [Node: draft_email_node] Drafting personalized outreach for {candidate['name']}...")

    draft = call_llm_for_draft(
        user_name=state.get("user_name", "Developer"),
        user_role=state.get("user_role", "Software Engineer"),
        user_goal=state.get("user_goal", "Discuss AI workflows"),
        candidate=candidate,
        shared_interests=state.get("shared_interests", []),
        available_slots=state.get("available_slots", []),
    )

    print("   ✅ Draft generated successfully!")
    return {
        "email_draft": draft,
        "status": "drafted",
    }


def human_approval_node(state: AgentState) -> Dict[str, Any]:
    """
    Node 5: Human-In-The-Loop (HITL) Review.
    Presents the draft to the user for review:
    - [A] Approve & Send
    - [E] Edit Draft
    - [R] Reject / Cancel
    """
    candidate = state["current_lead"]
    draft = state["email_draft"]

    # If decision was provided via UI (e.g. Streamlit button click)
    pre_decision = state.get("human_decision")
    if pre_decision in ["approved", "rejected"]:
        print(f"\n[Node: human_approval_node] Decision received from UI: {pre_decision}")
        return {
            "human_decision": pre_decision,
            "status": "approved" if pre_decision == "approved" else "rejected_by_human",
        }

    print("\n" + "🛎️  " + "=" * 56)
    print("👤 [Node: human_approval_node] HUMAN-IN-THE-LOOP INTERVENTION")
    print("=" * 60)
    print(f"Recipient: {candidate['name']} <{candidate['company']}>")
    print(f"Subject:   {draft['subject']}")
    print("-" * 60)
    print(draft["body"])
    print("=" * 60)

    # Prompt user for decision
    while True:
        choice = input("\n👉 Choose an action [A]pprove / [E]dit / [R]eject: ").strip().lower()
        if choice in ["a", "approve"]:
            print("   👍 Outreach APPROVED by human.")
            return {"human_decision": "approved", "status": "approved"}
        elif choice in ["e", "edit"]:
            print("\n✏️  Enter updated email body below (press Enter twice when done):")
            lines = []
            while True:
                line = input()
                if not line and lines and not lines[-1]:
                    break
                lines.append(line)
            new_body = "\n".join(lines).strip()
            updated_draft = EmailDraft(subject=draft["subject"], body=new_body)
            print("   ✏️  Draft updated and APPROVED with human edits.")
            return {"email_draft": updated_draft, "human_decision": "approved", "status": "approved_with_edits"}
        elif choice in ["r", "reject"]:
            print("   🚫 Outreach REJECTED by human.")
            return {"human_decision": "rejected", "status": "rejected_by_human"}
        else:
            print("   Invalid option. Please type 'A', 'E', or 'R'.")


def send_outreach_node(state: AgentState) -> Dict[str, Any]:
    """
    Node 6: Final outreach dispatch & Gmail Draft Creation.
    Creates an authentic draft in your Gmail account if Google is authenticated.
    """
    candidate = state["current_lead"]
    draft = state["email_draft"]

    print("\n" + "=" * 60)
    print(f"🚀 [Node: send_outreach_node] Finalizing outreach for {candidate['name']}...")
    print(f"   📬 Recipient: {candidate['name']}")
    print(f"   📌 Subject:   {draft['subject']}")

    # Try creating draft in Gmail
    from google_service import create_gmail_draft
    draft_id = create_gmail_draft(
        to_email="",
        recipient_name=candidate["name"],
        subject=draft["subject"],
        body=draft["body"],
    )

    if draft_id:
        print(f"   ✉️  LIVE: Draft saved to your Gmail 'Drafts' folder! (Draft ID: {draft_id})")
        return {"status": "saved_to_gmail_drafts"}
    else:
        print("   📁 Stored draft locally (Connect Google in credentials.json to sync to Gmail).")
        return {"status": "completed"}

