"""
main.py
=======
Entry point for NetworkPilot - Autonomous Networking Agent.

Run this script to start the agent. It walks through:
1. Candidate discovery (Apify or curated profiles)
2. Semantic relevance evaluation
3. Calendar availability checking
4. Personalized outreach email drafting
5. Human-in-the-loop review (Approve, Edit, or Reject)
6. Final dispatch or cancellation
"""

import sys
from dotenv import load_dotenv
from graph import create_networking_graph
from state import AgentState


def print_banner():
    banner = r"""
  _   _      _                      _    ____  _ _       _   
 | \ | | ___| |___      _____  _ __| | _|  _ \(_) | ___ | |_ 
 |  \| |/ _ \ __\ \ /\ / / _ \| '__| |/ / |_) | | |/ _ \| __|
 | |\  |  __/ |_ \ V  V / (_) | |  |   <|  __/| | | (_) | |_ 
 |_| \_|\___|\__| \_/\_/ \___/|_|  |_|\_\_|   |_|_|\___/ \__|
          Autonomous LangGraph Networking Agent
    """
    print(banner)


def run_agent():
    # Load environment variables (.env) if present
    load_dotenv()

    print_banner()

    # Define initial inputs
    print("📋 Initializing Agent State...")
    initial_state: AgentState = {
        "user_name": "Jordan Lee",
        "user_role": "AI Engineer & Open Source Builder",
        "user_interests": [
            "AI Agents",
            "Stateful Workflows",
            "Multi-Agent Systems",
            "Specialty Coffee",
        ],
        "user_goal": "Exchange notes on stateful agent architectures and coffee chats",
        "search_query": "LangGraph AI Agent Engineer",
        "discovered_leads": [],
        "current_lead": None,
        "match_score": 0,
        "match_reasoning": "",
        "shared_interests": [],
        "available_slots": [],
        "email_draft": None,
        "human_decision": None,
        "status": "initialized",
    }

    print(f"👤 User:       {initial_state['user_name']} ({initial_state['user_role']})")
    print(f"🎯 Target:     {initial_state['search_query']}")
    print(f"💡 Interests:  {', '.join(initial_state['user_interests'])}")
    print("-" * 60)

    # Check Google status
    from google_service import is_google_connected
    if is_google_connected():
        print("🔑 Google Status: Connected! (Calendar & Gmail Drafts active)")
    else:
        print("🔑 Google Status: Standby (Place credentials.json to auto-sync to Gmail Drafts)")
    print("-" * 60)

    # Build the compiled LangGraph workflow
    app = create_networking_graph()

    from services import SAMPLE_PROFILES
    candidates_to_process = SAMPLE_PROFILES[:3]

    print(f"▶️  Starting LangGraph batch evaluation for {len(candidates_to_process)} candidate profiles...")
    for idx, candidate in enumerate(candidates_to_process, 1):
        print(f"\n[{idx}/{len(candidates_to_process)}] Processing Candidate: {candidate['name']} ({candidate['company']})...")
        candidate_state = dict(initial_state)
        candidate_state["current_lead"] = candidate

        final_state = app.invoke(candidate_state)

        score = final_state.get("match_score", 0)
        decision = final_state.get("human_decision", "N/A")
        print(f"   📊 Final Result: Score {score}/100 | Decision: {decision} | Status: {final_state.get('status')}")

    print("\n" + "=" * 60)
    print("🏁 ALL BATCH OUTREACH EXECUTIONS COMPLETED!")
    print("Check your Gmail 'Drafts' folder: https://mail.google.com/mail/u/0/#drafts")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    run_agent()

