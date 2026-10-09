"""
state.py
========
Defines the shared state for the LangGraph networking agent.

In LangGraph:
- State is the central data contract flowing through every node in the graph.
- Every node receives the current state and returns a dictionary with state updates.
- LangGraph automatically merges the returned updates back into the central state.
"""

from typing import List, Optional, TypedDict


class CandidateProfile(TypedDict):
    """Represents a discovered professional's profile."""
    name: str
    headline: str
    company: str
    location: str
    bio: str
    skills: List[str]
    interests: List[str]
    profile_url: str


class EmailDraft(TypedDict):
    """Represents the drafted coffee chat outreach email."""
    subject: str
    body: str


class AgentState(TypedDict):
    """
    The complete state schema for NetworkPilot.
    
    Fields:
    - user_name: Your name
    - user_role: Your current job title / role
    - user_interests: Topics, technologies, or subjects you care about
    - user_goal: Why you want to network (e.g. coffee chat to discuss AI agents)
    - search_query: Search criteria used for discovery
    - discovered_leads: List of candidate profiles found
    - current_lead: The candidate profile currently being evaluated
    - match_score: 0-100 score indicating compatibility
    - match_reasoning: Explanation of why this candidate is relevant
    - shared_interests: List of mutual topics identified
    - available_slots: List of proposed open coffee chat calendar slots
    - email_draft: The generated outreach email draft
    - human_decision: "approved", "edited", or "rejected"
    - status: Current lifecycle status of the workflow
    """
    user_name: str
    user_role: str
    user_interests: List[str]
    user_goal: str
    search_query: str
    discovered_leads: List[CandidateProfile]
    current_lead: Optional[CandidateProfile]
    match_score: int
    match_reasoning: str
    shared_interests: List[str]
    available_slots: List[str]
    email_draft: Optional[EmailDraft]
    human_decision: Optional[str]
    status: str

