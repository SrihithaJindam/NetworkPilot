"""
cockpit.py
==========
Agentic Mission Control Dashboard for NetworkPilot.

A sleek, modern dark-mode AI Agent Cockpit powered by FastAPI.
Runs the LangGraph agent across multiple candidate professionals,
evaluates synergy, discovers calendar slots, and creates authentic drafts
directly in your Gmail account.

Run with:
    python cockpit.py
"""

import os
import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv

from state import AgentState, CandidateProfile
from services import (
    SAMPLE_PROFILES,
    fetch_candidate_profiles,
    call_llm_for_relevance,
    get_calendar_slots,
    call_llm_for_draft,
)
from google_service import is_google_connected, create_gmail_draft

load_dotenv()

app = FastAPI(title="NetworkPilot Cockpit")


HTML_PAGE = """
<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>NetworkPilot | Agent Cockpit</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {
      darkMode: 'class',
      theme: {
        extend: {
          colors: {
            brand: { 500: '#6366f1', 600: '#4f46e5' },
            darkBg: '#0f172a',
            darkCard: '#1e293b',
            darkBorder: '#334155'
          }
        }
      }
    }
  </script>
  <style>
    @keyframes pulse-slow {
      0%, 100% { opacity: 1; transform: scale(1); }
      50% { opacity: 0.6; transform: scale(1.05); }
    }
    .agent-pulse { animation: pulse-slow 2s infinite ease-in-out; }
  </style>
</head>
<body class="bg-darkBg text-slate-100 min-h-screen font-sans flex flex-col antialiased">

  <!-- Header -->
  <header class="border-b border-darkBorder bg-darkCard/80 backdrop-blur px-8 py-4 flex items-center justify-between sticky top-0 z-50">
    <div class="flex items-center space-x-3">
      <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-500 to-purple-500 flex items-center justify-center font-bold text-xl shadow-lg shadow-indigo-500/20">
        🧭
      </div>
      <div>
        <h1 class="text-xl font-bold tracking-tight bg-gradient-to-r from-indigo-200 to-purple-200 bg-clip-text text-transparent">
          NetworkPilot <span class="text-xs uppercase px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-400 font-mono ml-2 border border-indigo-500/30">LangGraph Agent</span>
        </h1>
        <p class="text-xs text-slate-400">Autonomous Professional Discovery, Synergy Matching & Draft Engine</p>
      </div>
    </div>

    <!-- Integrations Badges -->
    <div class="flex items-center space-x-4 text-xs font-mono">
      <div id="badge-google" class="flex items-center space-x-2 px-3 py-1.5 rounded-full bg-slate-800 border border-slate-700">
        <span class="w-2 h-2 rounded-full bg-slate-500"></span>
        <span class="text-slate-300">Google: Checking...</span>
      </div>
      <div id="badge-apify" class="flex items-center space-x-2 px-3 py-1.5 rounded-full bg-slate-800 border border-slate-700">
        <span class="w-2 h-2 rounded-full bg-slate-500"></span>
        <span class="text-slate-300">Apify: Checking...</span>
      </div>
      <a href="https://mail.google.com/mail/u/0/#drafts" target="_blank" class="flex items-center space-x-1.5 px-3 py-1.5 rounded-full bg-indigo-600/30 text-indigo-300 hover:bg-indigo-600/40 border border-indigo-500/40 transition">
        <span>📬 Open Gmail Drafts</span>
        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path></svg>
      </a>
    </div>
  </header>

  <!-- Main Container -->
  <main class="flex-1 max-w-7xl w-full mx-auto p-8 grid grid-cols-1 lg:grid-cols-3 gap-8">
    
    <!-- Left Column: Agent Controls & Parameters -->
    <div class="space-y-6">
      <div class="bg-darkCard border border-darkBorder rounded-2xl p-6 shadow-xl">
        <h2 class="text-lg font-semibold text-slate-200 flex items-center space-x-2 mb-4">
          <span>⚙️</span><span>Agent Configuration</span>
        </h2>
        
        <div class="space-y-4 text-sm">
          <div>
            <label class="block text-slate-400 text-xs mb-1">Your Name & Role</label>
            <input id="userName" type="text" value="Jordan Lee" class="w-full bg-slate-900 border border-darkBorder rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-indigo-500">
            <input id="userRole" type="text" value="AI Systems Engineer" class="w-full bg-slate-900 border border-darkBorder rounded-lg px-3 py-2 text-slate-200 mt-2 focus:outline-none focus:border-indigo-500">
          </div>

          <div>
            <label class="block text-slate-400 text-xs mb-1">Your Focus Areas / Interests</label>
            <textarea id="userInterests" rows="2" class="w-full bg-slate-900 border border-darkBorder rounded-lg px-3 py-2 text-slate-200 text-xs focus:outline-none focus:border-indigo-500">AI Agents, Stateful Workflows, Multi-Agent Systems, Specialty Coffee</textarea>
          </div>

          <div>
            <label class="block text-slate-400 text-xs mb-1">Coffee Chat Objective</label>
            <input id="userGoal" type="text" value="Exchange notes on stateful agent architectures and coffee chats" class="w-full bg-slate-900 border border-darkBorder rounded-lg px-3 py-2 text-slate-200 text-xs focus:outline-none focus:border-indigo-500">
          </div>
        </div>

        <button id="btnRunAgent" onclick="runAutonomousCycle()" class="mt-6 w-full py-3.5 px-4 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white font-medium rounded-xl shadow-lg shadow-indigo-500/25 flex items-center justify-center space-x-2 transition transform active:scale-95">
          <span id="btnIcon">⚡</span>
          <span id="btnText">Execute Batch Outreach Cycle</span>
        </button>
      </div>

      <!-- Agent Activity Terminal -->
      <div class="bg-darkCard border border-darkBorder rounded-2xl p-6 shadow-xl">
        <h2 class="text-sm font-semibold text-slate-300 flex items-center justify-between mb-3">
          <span class="flex items-center space-x-2"><span>🖥️</span><span>Agent Thought Log</span></span>
          <span class="w-2 h-2 rounded-full bg-emerald-400 agent-pulse"></span>
        </h2>
        <div id="terminal" class="bg-black/60 font-mono text-xs text-emerald-400 p-4 rounded-xl h-56 overflow-y-auto space-y-1.5 border border-slate-800">
          <p class="text-slate-500">> NetworkPilot Agent Engine ready.</p>
          <p class="text-slate-500">> Waiting for batch launch command...</p>
        </div>
      </div>
    </div>

    <!-- Right Column: Processed Candidates & Gmail Drafts -->
    <div class="lg:col-span-2 space-y-6">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-xl font-bold text-slate-100">Discovered Prospects & Draft Pipeline</h2>
          <p class="text-xs text-slate-400">The agent discovers candidates, evaluates mutual synergy, and generates drafts directly in Gmail.</p>
        </div>
        <span id="batchCount" class="text-xs font-mono px-3 py-1 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
          0 Candidates Evaluated
        </span>
      </div>

      <!-- Cards Container -->
      <div id="candidateFeed" class="space-y-4">
        <!-- Empty placeholder -->
        <div id="placeholderCard" class="border border-dashed border-darkBorder rounded-2xl p-12 text-center text-slate-500 space-y-3">
          <div class="text-4xl">🤖</div>
          <p class="text-sm">Click "Execute Batch Outreach Cycle" on the left to activate the agent.</p>
          <p class="text-xs text-slate-600">The agent will discover 3 professionals, calculate mutual synergy scores, check calendar availability, and generate drafts directly in your Gmail Drafts folder.</p>
        </div>
      </div>
    </div>

  </main>

  <script>
    // Load Status on startup
    async function loadStatus() {
      try {
        const res = await fetch('/api/status');
        const data = await res.json();
        
        // Google badge
        const gBadge = document.getElementById('badge-google');
        if (data.google_connected) {
          gBadge.innerHTML = '<span class="w-2 h-2 rounded-full bg-emerald-400"></span><span class="text-emerald-300">Google: Connected (Calendar & Gmail)</span>';
        } else {
          gBadge.innerHTML = '<span class="w-2 h-2 rounded-full bg-amber-400"></span><span class="text-amber-300">Google: Standby (credentials.json)</span>';
        }

        // Apify badge
        const aBadge = document.getElementById('badge-apify');
        if (data.apify_connected) {
          aBadge.innerHTML = '<span class="w-2 h-2 rounded-full bg-emerald-400"></span><span class="text-emerald-300">Apify: Authenticated</span>';
        } else {
          aBadge.innerHTML = '<span class="w-2 h-2 rounded-full bg-slate-500"></span><span class="text-slate-400">Apify: Offline Mode</span>';
        }
      } catch (e) {
        console.error(e);
      }
    }
    loadStatus();

    function log(msg) {
      const term = document.getElementById('terminal');
      const p = document.createElement('p');
      p.textContent = '> ' + msg;
      term.appendChild(p);
      term.scrollTop = term.scrollHeight;
    }

    async function runAutonomousCycle() {
      const btn = document.getElementById('btnRunAgent');
      const btnText = document.getElementById('btnText');
      const btnIcon = document.getElementById('btnIcon');
      
      btn.disabled = true;
      btn.classList.add('opacity-75');
      btnText.textContent = "Agent Working...";
      btnIcon.textContent = "⏳";

      log("Initiating autonomous LangGraph workflow cycle...");
      log("Querying candidates across target domain...");

      const payload = {
        user_name: document.getElementById('userName').value,
        user_role: document.getElementById('userRole').value,
        user_interests: document.getElementById('userInterests').value.split(',').map(s => s.trim()),
        user_goal: document.getElementById('userGoal').value,
      };

      try {
        const res = await fetch('/api/run_batch', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify(payload)
        });

        const data = await res.json();
        renderResults(data);
      } catch (err) {
        log("Execution error: " + err);
      } finally {
        btn.disabled = false;
        btn.classList.remove('opacity-75');
        btnText.textContent = "Execute Batch Outreach Cycle";
        btnIcon.textContent = "⚡";
      }
    }

    function renderResults(data) {
      const feed = document.getElementById('candidateFeed');
      feed.innerHTML = '';
      
      document.getElementById('batchCount').textContent = `${data.length} Candidates Processed`;

      data.forEach(item => {
        log(`Candidate: ${item.candidate.name} | Fit Score: ${item.score}% | Decision: ${item.router_decision}`);
        if (item.gmail_draft_id) {
          log(`  📬 Gmail Draft created! ID: ${item.gmail_draft_id}`);
        }

        const isApproved = item.score >= 60;
        const scoreColor = isApproved ? 'text-emerald-400 border-emerald-500/40 bg-emerald-500/10' : 'text-rose-400 border-rose-500/40 bg-rose-500/10';

        const card = document.createElement('div');
        card.className = "bg-darkCard border border-darkBorder rounded-2xl p-6 shadow-xl space-y-5 transition hover:border-slate-600";

        // Shared interest badges
        const sharedHtml = (item.shared_interests || []).map(topic => 
          `<span class="px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">🤝 ${topic}</span>`
        ).join(' ');

        // Calendar slots
        const slotsHtml = (item.available_slots || []).map(slot => 
          `<span class="px-2.5 py-1 rounded-md text-xs bg-slate-800 text-slate-300 border border-slate-700">📅 ${slot}</span>`
        ).join(' ');

        // Gmail draft action badge
        const gmailBadge = item.gmail_draft_id 
          ? `<a href="https://mail.google.com/mail/u/0/#drafts" target="_blank" class="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-emerald-600/30 text-emerald-300 border border-emerald-500/40 text-xs font-medium hover:bg-emerald-600/50 transition"><span>📬 Draft In Gmail</span><svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path></svg></a>`
          : (isApproved ? `<span class="px-3 py-1 rounded-lg bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 text-xs font-mono">Drafted Locally</span>` : `<span class="px-3 py-1 rounded-lg bg-slate-800 text-slate-500 text-xs">Outreach Skipped</span>`);

        card.innerHTML = `
          <div class="flex items-start justify-between">
            <div class="space-y-1">
              <div class="flex items-center space-x-3">
                <h3 class="text-lg font-bold text-slate-100">${item.candidate.name}</h3>
                <span class="text-xs px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-400 border border-slate-700">${item.candidate.company}</span>
              </div>
              <p class="text-xs text-indigo-300">${item.candidate.headline}</p>
              <p class="text-xs text-slate-400 italic">${item.candidate.bio}</p>
            </div>

            <!-- Score Pill -->
            <div class="text-center px-4 py-2 rounded-xl border ${scoreColor}">
              <div class="text-2xl font-black">${item.score}%</div>
              <div class="text-[10px] uppercase font-mono tracking-wider">Synergy Fit</div>
            </div>
          </div>

          <!-- Reasoning & Mutual Interests -->
          <div class="bg-slate-900/80 p-4 rounded-xl border border-slate-800 space-y-2">
            <p class="text-xs text-slate-300"><strong class="text-slate-100">AI Reasoning:</strong> ${item.reasoning}</p>
            <div class="flex flex-wrap gap-2 pt-1">${sharedHtml || '<span class="text-xs text-slate-500">No direct topic overlap</span>'}</div>
          </div>

          ${isApproved && item.email_draft ? `
            <div class="space-y-2">
              <div class="flex items-center justify-between">
                <span class="text-xs font-semibold uppercase tracking-wider text-slate-400">Proposed Coffee Chat Windows</span>
                ${gmailBadge}
              </div>
              <div class="flex flex-wrap gap-2">${slotsHtml}</div>
            </div>

            <!-- Email Draft Box -->
            <div class="bg-black/50 border border-darkBorder rounded-xl p-4 text-xs font-mono space-y-2">
              <div class="text-indigo-400 font-bold">Subject: ${item.email_draft.subject}</div>
              <pre class="text-slate-300 whitespace-pre-wrap font-sans text-xs bg-transparent border-0 p-0">${item.email_draft.body}</pre>
            </div>
          ` : `
            <div class="flex items-center justify-between text-xs text-rose-400 bg-rose-500/10 border border-rose-500/20 p-3 rounded-xl">
              <span>⛔ Low mutual synergy (< 60%). LangGraph conditional router terminated without drafting.</span>
              ${gmailBadge}
            </div>
          `}
        `;

        feed.appendChild(card);
      });

      log("Batch outreach execution finished! Check Gmail Drafts for new drafts.");
    }
  </script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
def index():
    return HTML_PAGE


@app.get("/api/status")
def get_status():
    return {
        "google_connected": is_google_connected(),
        "apify_connected": bool(os.getenv("APIFY_API_TOKEN")),
    }


class BatchRequest(BaseModel):
    user_name: str
    user_role: str
    user_interests: list[str]
    user_goal: str


@app.post("/api/run_batch")
def run_batch(req: BatchRequest):
    """
    Executes the LangGraph evaluation across 3 candidate profiles.
    For matching profiles (>= 60%), creates drafts directly in Gmail!
    """
    # Discover fresh candidates dynamically based on your role and interests
    candidates = fetch_candidate_profiles(
        role=req.user_role,
        interests=req.user_interests,
        count=3,
    )
    results = []

    for candidate in candidates:
        # 1. Relevance evaluation
        score, reasoning, shared = call_llm_for_relevance(
            user_role=req.user_role,
            user_interests=req.user_interests,
            user_goal=req.user_goal,
            candidate=candidate,
        )

        email_draft = None
        available_slots = []
        gmail_draft_id = None
        router_decision = "END"

        # 2. Conditional Edge check
        if score >= 60:
            router_decision = "draft_email"
            available_slots = get_calendar_slots(3)
            email_draft = call_llm_for_draft(
                user_name=req.user_name,
                user_role=req.user_role,
                user_goal=req.user_goal,
                candidate=candidate,
                shared_interests=shared,
                available_slots=available_slots,
            )

            # 3. Create authentic Gmail draft
            gmail_draft_id = create_gmail_draft(
                to_email="",
                recipient_name=candidate["name"],
                subject=email_draft["subject"],
                body=email_draft["body"],
            )

        results.append({
            "candidate": candidate,
            "score": score,
            "reasoning": reasoning,
            "shared_interests": shared,
            "router_decision": router_decision,
            "available_slots": available_slots,
            "email_draft": email_draft,
            "gmail_draft_id": gmail_draft_id,
        })

    return JSONResponse(content=results)


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🧭 Starting NetworkPilot Agent Cockpit at: http://localhost:8000")
    print("=" * 60 + "\n")
    uvicorn.run("cockpit:app", host="127.0.0.1", port=8000, reload=True)

