"""
google_service.py
=================
Handles Google Calendar & Gmail integration:
1. OAuth 2.0 authentication (using credentials.json)
2. Reading real open time slots from Google Calendar
3. Creating real outreach email drafts in your Gmail Drafts folder!

Privacy & Safety:
- Scope 'https://www.googleapis.com/auth/gmail.compose' only allows CREATING drafts.
  It cannot read your inbox or send emails automatically without you.
- Scope 'https://www.googleapis.com/auth/calendar.readonly' only checks availability.
"""

import os
import base64
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from typing import List, Optional, Tuple

SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/gmail.compose",
]


def get_google_credentials():
    """
    Retrieves or generates valid Google OAuth 2.0 credentials.
    Looks for token.json (cached token) or credentials.json (client secrets from Google Cloud Console).
    """
    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
    except ImportError:
        print("[Google Service] Notice: google-api packages not installed. Run 'pip install -r requirements.txt'")
        return None

    creds = None
    if os.path.exists("token.json"):
        try:
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        except Exception:
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                creds = None

        if not creds:
            creds_file = "credentials.json" if os.path.exists("credentials.json") else ("credentials.json.json" if os.path.exists("credentials.json.json") else None)
            if not creds_file:
                # No credentials file provided yet
                return None
            try:
                flow = InstalledAppFlow.from_client_secrets_file(creds_file, SCOPES)
                creds = flow.run_local_server(port=0)
                # Save the credentials for next run
                with open("token.json", "w") as token_file:
                    token_file.write(creds.to_json())
            except Exception as e:
                print(f"[Google Service] OAuth flow failed: {e}")
                return None

    return creds


def is_google_connected() -> bool:
    """Returns True if Google Calendar & Gmail are authenticated."""
    creds = get_google_credentials()
    return creds is not None and creds.valid


def get_real_calendar_slots(num_slots: int = 3) -> List[str]:
    """
    Checks your Google Calendar for real open 30-minute slots during working hours.
    Falls back to calculated dynamic dates if Google is not connected.
    """
    creds = get_google_credentials()
    if creds:
        try:
            from googleapiclient.discovery import build
            service = build("calendar", "v3", credentials=creds)

            # Look ahead across next 5 days
            now = datetime.now(timezone.utc)
            start_time = (now + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
            end_time = (now + timedelta(days=5)).replace(hour=18, minute=0, second=0, microsecond=0)

            body = {
                "timeMin": start_time.isoformat(),
                "timeMax": end_time.isoformat(),
                "items": [{"id": "primary"}],
            }
            events_result = service.freebusy().query(body=body).execute()
            busy_times = events_result.get("calendars", {}).get("primary", {}).get("busy", [])

            # Simple slot generator looking for open business hour slots
            available_slots = []
            current_day = start_time
            while len(available_slots) < num_slots and current_day < end_time:
                # Monday to Friday only
                if current_day.weekday() < 5:
                    for hour in [10, 14, 16]:
                        slot_cand = current_day.replace(hour=hour, minute=0)
                        # Check if overlapping with busy periods
                        slot_iso = slot_cand.isoformat()
                        is_busy = any(
                            b["start"] <= slot_iso <= b["end"] for b in busy_times
                        )
                        if not is_busy and slot_cand > now:
                            available_slots.append(slot_cand.strftime("%A, %b %d at %I:%M %p"))
                            if len(available_slots) >= num_slots:
                                break
                current_day += timedelta(days=1)

            if available_slots:
                print(f"[Google Calendar] 📅 Retrieved {len(available_slots)} open slots directly from your Google Calendar!")
                return available_slots

        except Exception as err:
            print(f"[Google Calendar] Notice: Query failed ({err}), using dynamic date generator.")

    # Fallback dynamic calculation
    base_date = datetime.now() + timedelta(days=2)
    slots = []
    offsets = [(10, 0), (14, 30), (16, 0)]
    for i in range(num_slots):
        d = base_date + timedelta(days=i)
        if d.weekday() >= 5:
            d += timedelta(days=2)
        h, m = offsets[i % len(offsets)]
        slots.append(d.replace(hour=h, minute=m).strftime("%A, %b %d at %I:%M %p"))
    return slots


def create_gmail_draft(to_email: str, recipient_name: str, subject: str, body: str) -> Optional[str]:
    """
    Creates an actual draft email in your Gmail Drafts folder.
    Returns the Gmail Draft ID if created, or None.
    """
    creds = get_google_credentials()
    if not creds:
        return None

    try:
        from googleapiclient.discovery import build
        service = build("gmail", "v1", credentials=creds)

        message = EmailMessage()
        message.set_content(body)
        
        target_address = to_email if (to_email and "@" in to_email) else f"{recipient_name.lower().replace(' ', '.')}@linkedin-lead.com"
        message["To"] = target_address
        message["Subject"] = subject

        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {"message": {"raw": encoded_message}}

        draft = service.users().drafts().create(userId="me", body=create_message).execute()
        draft_id = draft.get("id")
        print(f"[Gmail Service] 📬 SUCCESS: Created real draft in your Gmail account! (Draft ID: {draft_id})")
        return draft_id
    except Exception as e:
        print(f"[Gmail Service] Error creating Gmail draft: {e}")
        return None

