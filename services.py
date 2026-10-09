"""
services.py
===========
External integrations and data services:
1. Apify discovery (with realistic offline mock fallback)
2. Calendar availability lookup
3. LLM service (OpenAI if API key exists, otherwise smart template fallback)
"""

import os
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from state import CandidateProfile, EmailDraft


# ---------------------------------------------------------------------------
# 1. Profile Discovery Service (Apify + Mock Fallback)
# ---------------------------------------------------------------------------

SAMPLE_PROFILES: List[CandidateProfile] = [
    {
        "name": "Elena Rostova",
        "headline": "Lead AI Agent Engineer @ NextGen Robotics",
        "company": "NextGen Robotics",
        "location": "Berlin, Germany",
        "bio": "Building autonomous multi-agent systems and orchestration graphs using LangGraph and Python. Passionate about AI agents, distributed systems, and specialty coffee.",
        "skills": ["LangGraph", "Python", "Multi-Agent Systems", "FastAPI", "AsyncIO"],
        "interests": ["AI Agents", "Stateful Workflows", "Specialty Coffee", "Open Source"],
        "profile_url": "https://linkedin.com/in/elena-rostova-demo",
    },
    {
        "name": "Marcus Chen",
        "headline": "Senior Staff Architect @ CloudFlow",
        "company": "CloudFlow",
        "location": "Zurich, Switzerland",
        "bio": "Cloud-native infrastructure and distributed messaging. Exploring LLM-based autonomous routing for enterprise workflows.",
        "skills": ["Kubernetes", "Go", "Python", "Kafka", "Cloud Architecture"],
        "interests": ["AI Workflows", "Distributed Systems", "Tech Mentorship", "Cycling"],
        "profile_url": "https://linkedin.com/in/marcus-chen-demo",
    },
    {
        "name": "Sarah Lindqvist",
        "headline": "Talent Partner @ Nordic Fintech",
        "company": "Nordic Fintech",
        "location": "Stockholm, Sweden",
        "bio": "Connecting banking executives with compliance leaders across Scandinavia.",
        "skills": ["Executive Search", "Fintech Recruitment", "HR Operations"],
        "interests": ["Fintech", "HR Tech", "Kayaking"],
        "profile_url": "https://linkedin.com/in/sarah-lindqvist-demo",
    },
]

_DISCOVERY_CYCLE = 0

NAMES_POOL = [
    ("Priya Sharma", "London, UK"),
    ("David Miller", "San Francisco, CA"),
    ("Ananya Patel", "New York, NY"),
    ("Marcus Vance", "Seattle, WA"),
    ("Sophie Laurent", "Paris, France"),
    ("Kevin Zhang", "Toronto, Canada"),
    ("Liam O'Connor", "Dublin, Ireland"),
    ("Carlos Mendez", "Austin, TX"),
    ("Maya Lin", "Chicago, IL"),
    ("Aiden Brooks", "Boston, MA"),
    ("Fatima Al-Zahra", "Amsterdam, Netherlands"),
    ("Rohan Mehta", "Berlin, Germany"),
]

COMPANIES_POOL = [
    "Snowflake", "Databricks", "Stripe", "Netflix", "Spotify",
    "Airbnb", "dbt Labs", "Google", "AWS", "Uber", "Palantir"
]


def generate_dynamic_candidates(role: str, interests: List[str], count: int = 3, cycle: int = 0) -> List[CandidateProfile]:
    """Generates unique, realistic profiles aligned with the specified role and interests."""
    target_role = role.strip() if role else "Engineer"
    role_title = target_role.title()
    clean_interests = [i.strip() for i in interests if i.strip()] or [role_title, "Cloud Architecture", "Python"]

    profiles: List[CandidateProfile] = []
    start_idx = (cycle * count) % len(NAMES_POOL)

    seniorities = ["Senior", "Lead", "Staff", "Principal", "Director of"]

    for i in range(count):
        name_entry = NAMES_POOL[(start_idx + i) % len(NAMES_POOL)]
        company = COMPANIES_POOL[(start_idx + i) % len(COMPANIES_POOL)]
        seniority = seniorities[(start_idx + i) % len(seniorities)]

        cand_headline = f"{seniority} {role_title} @ {company}"
        cand_skills = [role_title] + clean_interests[:3] + ["Python", "Cloud Architecture"]
        cand_bio = f"{seniority} professional at {company} focusing on {clean_interests[0] if clean_interests else role_title} systems, data pipelines, and scalable architectures."

        profiles.append({
            "name": name_entry[0],
            "headline": cand_headline,
            "company": company,
            "location": name_entry[1],
            "bio": cand_bio,
            "skills": cand_skills,
            "interests": clean_interests[:4],
            "profile_url": f"https://linkedin.com/in/{name_entry[0].lower().replace(' ', '-')}-demo",
        })

    return profiles


def fetch_candidate_profiles(
    query: str = "",
    role: str = "",
    interests: Optional[List[str]] = None,
    count: int = 3,
) -> List[CandidateProfile]:
    """
    Discovers professional profiles matching the role and interests.
    1. If APIFY_API_TOKEN is available, attempts to scrape real profiles via Apify.
    2. Dynamically generates fresh, non-repeating candidates aligned with your role every run.
    """
    global _DISCOVERY_CYCLE
    _DISCOVERY_CYCLE += 1

    token = os.getenv("APIFY_API_TOKEN")
    target_role = role or query or "Data Engineer"
    interests_list = interests or []

    # 1. Real Apify Scraping attempt if token exists
    if token:
        try:
            from apify_client import ApifyClient
            client = ApifyClient(token)
            search_query = f'site:linkedin.com/in "{target_role}"'
            if interests_list:
                search_query += f' "{interests_list[0]}"'

            print(f"[Apify Service] 🌐 Launching real Apify scraper for: {search_query}...")
            run = client.actor("apify/google-search-scraper").call(
                run_input={
                    "queries": search_query,
                    "maxPagesPerQuery": 1,
                    "resultsPerPage": count,
                },
                timeout_secs=65,
            )
            dataset_items = client.dataset(run["defaultDatasetId"]).list_items().items
            scraped = []
            for item in dataset_items:
                organic = item.get("organicResults", [])
                for res in organic:
                    title = res.get("title", "")
                    desc = res.get("description", "")
                    url = res.get("url", "")
                    if "linkedin.com/in" in url and title:
                        clean_title = title.replace(" - LinkedIn", "").replace(" | LinkedIn", "")
                        parts = clean_title.split(" - ")
                        name = parts[0].strip()
                        headline = parts[1].strip() if len(parts) > 1 else target_role
                        company = parts[2].strip() if len(parts) > 2 else "Tech"
                        scraped.append({
                            "name": name,
                            "headline": headline,
                            "company": company,
                            "location": "Global",
                            "bio": desc or f"Experienced {target_role} specializing in {', '.join(interests_list)}.",
                            "skills": [target_role] + interests_list,
                            "interests": interests_list,
                            "profile_url": url,
                        })
                        if len(scraped) >= count:
                            break
                if len(scraped) >= count:
                    break

            if scraped:
                print(f"[Apify Service] ✅ Found {len(scraped)} live LinkedIn profiles via Apify!")
                return scraped
        except Exception as err:
            print(f"[Apify Service] Notice: Apify scraping fallback ({err}). Using dynamic matching engine.")

    # 2. Dynamic generation aligned with user's role & interests (changes every cycle!)
    return generate_dynamic_candidates(target_role, interests_list, count=count, cycle=_DISCOVERY_CYCLE)


# ---------------------------------------------------------------------------
# 2. Calendar Service
# ---------------------------------------------------------------------------

def get_calendar_slots(num_slots: int = 3) -> List[str]:
    """
    Returns upcoming available coffee chat slots.
    Uses Google Calendar API if connected, or calculates upcoming weekday slots.
    """
    try:
        from google_service import get_real_calendar_slots
        return get_real_calendar_slots(num_slots)
    except Exception:
        base_date = datetime.now() + timedelta(days=2)
        slots = []
        hour_offsets = [(10, 0), (14, 30), (16, 0)]
        for i in range(num_slots):
            slot_date = base_date + timedelta(days=i)
            if slot_date.weekday() >= 5:
                slot_date += timedelta(days=2)
            hour, minute = hour_offsets[i % len(hour_offsets)]
            slot_time = slot_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
            slots.append(slot_time.strftime("%A, %b %d at %I:%M %p"))
        return slots


# ---------------------------------------------------------------------------
# 3. LLM Service (OpenAI or Rule-Based Fallback)
# ---------------------------------------------------------------------------

def call_llm_for_relevance(
    user_role: str,
    user_interests: List[str],
    user_goal: str,
    candidate: CandidateProfile,
) -> Tuple[int, str, List[str]]:
    """
    Evaluates profile match. Returns (score 0-100, reasoning, shared_interests).
    Uses ChatOpenAI if OPENAI_API_KEY is configured, else smart offline heuristic.
    """
    api_key = os.getenv("OPENAI_API_KEY")

    if api_key:
        try:
            from langchain_openai import ChatOpenAI
            from langchain_core.messages import SystemMessage, HumanMessage
            import json

            llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)
            prompt = f"""
You are an expert networking agent evaluating if two professionals should connect for a coffee chat.

My Profile:
- Role: {user_role}
- Interests: {', '.join(user_interests)}
- Goal: {user_goal}

Candidate Profile:
- Name: {candidate['name']}
- Headline: {candidate['headline']}
- Bio: {candidate['bio']}
- Skills: {', '.join(candidate['skills'])}
- Interests: {', '.join(candidate['interests'])}

Analyze their synergy. Return JSON ONLY with keys:
- "score": integer from 0 to 100
- "reasoning": 1-2 concise sentences explaining why they should or should not connect
- "shared_interests": list of shared topics
"""
            response = llm.invoke([
                SystemMessage(content="You evaluate professional networking fit. Always return valid JSON only."),
                HumanMessage(content=prompt),
            ])
            content = response.content.strip()
            # Clean possible markdown fences
            if content.startswith("```"):
                content = content.strip("`").replace("json\n", "", 1).strip()
            parsed = json.loads(content)
            return int(parsed.get("score", 0)), parsed.get("reasoning", ""), parsed.get("shared_interests", [])
        except Exception as e:
            print(f"[LLM Service] Notice: LLM call returned error ({e}), using offline matcher.")

    # Smart offline heuristic (works without API key)
    # 1. Check direct phrase match
    direct_shared = []
    for u in user_interests:
        clean_u = u.strip()
        if not clean_u:
            continue
        if any(clean_u.lower() in c.lower() or c.lower() in clean_u.lower() for c in candidate["skills"] + candidate["interests"]):
            direct_shared.append(clean_u.title())

    # 2. Check token/word overlap between user and candidate
    user_words = set()
    for item in user_interests + [user_role]:
        for w in item.lower().split():
            if len(w) > 3 and w not in ["and", "with", "from", "for"]:
                user_words.add(w)

    cand_words = set()
    for item in candidate["skills"] + candidate["interests"] + [candidate["headline"]]:
        for w in item.lower().split():
            if len(w) > 3 and w not in ["and", "with", "from", "for"]:
                cand_words.add(w)

    overlap = user_words.intersection(cand_words)

    # 3. Compute score and reasoning
    if len(direct_shared) >= 2 or len(overlap) >= 3:
        score = 90
        shared_str = ", ".join(direct_shared[:2]) if direct_shared else ", ".join(list(overlap)[:2]).title()
        reasoning = f"Strong mutual focus on {shared_str} and complementary engineering backgrounds."
    elif len(direct_shared) == 1 or len(overlap) >= 1:
        score = 75
        topic = direct_shared[0] if direct_shared else list(overlap)[0].title()
        reasoning = f"Relevant overlap in {topic} and aligned technical domain."
    else:
        score = 30
        reasoning = "Limited professional synergy or mutual focus areas for a technical coffee chat."

    display_topics = direct_shared if direct_shared else [w.title() for w in list(overlap)[:3]]
    return score, reasoning, display_topics


def call_llm_for_draft(
    user_name: str,
    user_role: str,
    user_goal: str,
    candidate: CandidateProfile,
    shared_interests: List[str],
    available_slots: List[str],
) -> EmailDraft:
    """
    Drafts a personalized, concise, friendly coffee chat outreach email.
    """
    api_key = os.getenv("OPENAI_API_KEY")

    if api_key:
        try:
            from langchain_openai import ChatOpenAI
            from langchain_core.messages import SystemMessage, HumanMessage
            import json

            llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
            prompt = f"""
Write a warm, non-salesy, professional coffee chat outreach email.

Sender: {user_name} ({user_role})
Recipient: {candidate['name']} ({candidate['headline']})
Mutual topics: {', '.join(shared_interests) if shared_interests else 'AI and tech innovation'}
Purpose: {user_goal}
Proposed Time Slots:
{chr(10).join(f"- {slot}" for slot in available_slots)}

Rules:
- Keep it under 120 words.
- Tone: Genuine, appreciative, respectful of their time.
- Include the suggested time slots naturally.

Return JSON ONLY:
{{
  "subject": "subject line",
  "body": "email body"
}}
"""
            res = llm.invoke([
                SystemMessage(content="You are a warm, authentic networking assistant. Return JSON only."),
                HumanMessage(content=prompt),
            ])
            text = res.content.strip()
            if text.startswith("```"):
                text = text.strip("`").replace("json\n", "", 1).strip()
            parsed = json.loads(text)
            return EmailDraft(subject=parsed["subject"], body=parsed["body"])
        except Exception as e:
            print(f"[LLM Service] Notice: LLM draft failed ({e}), using built-in template.")

    # High quality clean template fallback
    shared_str = ", ".join(shared_interests) if shared_interests else "agentic workflows"
    slots_str = "\n".join(f"  • {slot}" for slot in available_slots)
    
    first_name = candidate["name"].split()[0]
    subject = f"Coffee chat & exchanging notes on {shared_interests[0] if shared_interests else 'AI Agents'}?"
    body = f"""Hi {first_name},

I came across your work at {candidate['company']} around {candidate['headline']}. As someone building in this space as well, I really appreciated your focus on {shared_str}.

I'd love to invite you for a virtual coffee chat to trade insights on {user_goal.lower()}.

If you're open to a 20-minute chat, I have a few open windows next week:
{slots_str}

No pressure at all if your plate is currently full. Either way, keep up the fantastic work!

Warm regards,
{user_name}
{user_role}"""

    return EmailDraft(subject=subject, body=body)

