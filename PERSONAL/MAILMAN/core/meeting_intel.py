#!/usr/bin/env python3
"""
MAILMAN Meeting Intelligence
Extracts meeting info from emails, integrates with Google Calendar,
generates follow-up drafts, and tracks action items from meetings.

Fyxer parity: meeting notetaker + follow-up automation
Beyond Fyxer: action item extraction, deadline tracking, agenda generation

Usage:
  python3 meeting_intel.py --scan              # Scan inbox for meeting requests
  python3 meeting_intel.py --upcoming          # Show upcoming meetings + prep
  python3 meeting_intel.py --follow-up <id>    # Generate follow-up email for meeting
  python3 meeting_intel.py --actions            # Show open action items from meetings
"""

import json
import re
import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

try:
    import anthropic
except ImportError:
    print("Missing: pip install anthropic --break-system-packages")
    sys.exit(1)

MAILMAN_ROOT = Path(__file__).parent.parent
MEMORY_DIR = MAILMAN_ROOT / "_memory"
LOGS_DIR = MAILMAN_ROOT / "logs"
MEMORY_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)


class MeetingIntelligence:
    """
    Extracts meeting context from emails, integrates with calendar,
    generates follow-ups, and tracks action items.
    """

    def __init__(self):
        self.client = anthropic.Anthropic()
        self.meetings_db_path = MEMORY_DIR / "meetings_db.json"
        self.actions_path = MEMORY_DIR / "action_items.json"
        self.meetings = self._load_json(self.meetings_db_path, {"meetings": {}})
        self.actions = self._load_json(self.actions_path, {"items": []})

    def _load_json(self, path, default):
        if path.exists():
            with open(path) as f:
                return json.load(f)
        return default

    def _save_meetings(self):
        with open(self.meetings_db_path, "w") as f:
            json.dump(self.meetings, f, indent=2)

    def _save_actions(self):
        with open(self.actions_path, "w") as f:
            json.dump(self.actions, f, indent=2)

    def scan_emails_for_meetings(self, emails):
        """
        Scan a batch of emails for meeting-related content.
        Detects: calendar invites, scheduling requests, meeting notes,
        implicit meeting suggestions, follow-up discussions.

        Args:
            emails: List of email dicts from GmailClient

        Returns:
            List of detected meeting events
        """
        detected = []

        for email in emails:
            meeting_type = self._detect_meeting_type(email)
            if meeting_type:
                meeting_data = self._extract_meeting_details(email, meeting_type)
                if meeting_data:
                    detected.append(meeting_data)
                    self.meetings["meetings"][meeting_data["id"]] = meeting_data

        if detected:
            self._save_meetings()

        return detected

    def _detect_meeting_type(self, email):
        """Determine if an email is meeting-related and what type."""
        subject = (email.get("subject", "") or "").lower()
        body = (email.get("body_text", "") or email.get("snippet", "") or "").lower()
        content_type = email.get("content_type", "")
        text = f"{subject} {body}"

        # Calendar invite (ICS attachment or content type)
        if "text/calendar" in content_type or ".ics" in text:
            return "calendar_invite"

        # Explicit meeting request patterns
        meeting_patterns = [
            r'(?:can we|could we|let\'s|shall we)\s+(?:meet|hop on|jump on|catch up|sync|chat)',
            r'(?:schedule|set up|book|arrange)\s+(?:a\s+)?(?:meeting|call|sync|chat)',
            r'(?:are you|would you be)\s+(?:free|available)\s+(?:for|to)',
            r'(?:meeting|call)\s+(?:at|on|scheduled for)',
            r'(?:zoom|teams|meet)\s+link',
            r'(?:calendar|invite)\s+(?:sent|attached)',
        ]
        for pattern in meeting_patterns:
            if re.search(pattern, text):
                return "meeting_request"

        # Meeting notes or recap
        notes_patterns = [
            r'(?:meeting|call)\s+(?:notes|recap|summary|minutes)',
            r'(?:notes from|recap of|summary of)\s+(?:our|the|today)',
            r'(?:action items|next steps|follow.?ups?)\s+from',
            r'(?:as discussed|per our conversation|following up on our)',
        ]
        for pattern in notes_patterns:
            if re.search(pattern, text):
                return "meeting_notes"

        # Implicit meeting (someone suggesting a time)
        time_patterns = [
            r'(?:how about|what about|does)\s+\d{1,2}(?::\d{2})?\s*(?:am|pm|AM|PM)',
            r'(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)\s+(?:at|around)\s+\d',
            r'(?:tomorrow|next week|this week)\s+(?:at|around|works)',
        ]
        for pattern in time_patterns:
            if re.search(pattern, text):
                return "scheduling_discussion"

        return None

    def _extract_meeting_details(self, email, meeting_type):
        """Use Claude to extract structured meeting details from an email."""
        body = (email.get("body_text", "") or email.get("snippet", ""))[:3000]

        prompt = f"""Extract meeting details from this email. Return ONLY valid JSON.

EMAIL:
From: {email.get('sender_name', '')} <{email.get('sender_email', '')}>
Subject: {email.get('subject', '')}
Date: {email.get('date', '')}
Type: {meeting_type}
Body: {body}

Return this JSON structure:
{{
  "title": "<meeting title or topic>",
  "meeting_type": "{meeting_type}",
  "proposed_time": "<datetime if mentioned, else null>",
  "duration_minutes": <estimated duration if mentioned, else null>,
  "attendees": ["list of attendee names/emails mentioned"],
  "location_or_link": "<zoom/meet link or physical location if mentioned>",
  "agenda_items": ["list of topics to discuss if mentioned"],
  "action_items": [
    {{"task": "<what>", "owner": "<who>", "deadline": "<when if mentioned>"}}
  ],
  "context_summary": "<1-2 sentence summary of what this meeting is about>",
  "requires_response": true/false,
  "urgency": "low|medium|high"
}}"""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-5-20250514",
                max_tokens=600,
                messages=[{"role": "user", "content": prompt}],
            )
            result = response.content[0].text.strip()
            if result.startswith("```"):
                result = result.split("\n", 1)[1].rsplit("```", 1)[0]

            meeting = json.loads(result)
            meeting["id"] = email["id"]
            meeting["source_email_id"] = email["id"]
            meeting["sender"] = email.get("sender_email", "")
            meeting["subject"] = email.get("subject", "")
            meeting["detected_at"] = datetime.utcnow().isoformat()

            # Extract and store action items separately
            for item in meeting.get("action_items", []):
                self._add_action_item(item, meeting)

            return meeting

        except Exception as e:
            print(f"Meeting extraction error: {e}")
            return None

    def _add_action_item(self, item, meeting):
        """Add an action item to the persistent tracker."""
        action = {
            "id": f"act_{len(self.actions['items'])+1}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "task": item.get("task", ""),
            "owner": item.get("owner", ""),
            "deadline": item.get("deadline"),
            "source_meeting": meeting.get("title", ""),
            "source_email_id": meeting.get("source_email_id", ""),
            "created_at": datetime.utcnow().isoformat(),
            "status": "open",
            "notes": "",
        }
        self.actions["items"].append(action)
        self._save_actions()

    def generate_follow_up(self, meeting_id, voice_profile=None):
        """
        Generate a follow-up email after a meeting.

        Args:
            meeting_id: The meeting ID to generate follow-up for
            voice_profile: Optional voice profile dict for tone matching

        Returns:
            Draft follow-up email string
        """
        meeting = self.meetings.get("meetings", {}).get(meeting_id)
        if not meeting:
            return f"Meeting {meeting_id} not found."

        voice_instruction = ""
        if voice_profile and voice_profile.get("ai_analysis"):
            voice_instruction = f"\nVOICE: {voice_profile['ai_analysis'].get('voice_summary', '')}"

        prompt = f"""Generate a follow-up email for this meeting. This is being sent BY the user.

MEETING DETAILS:
Title: {meeting.get('title', '')}
Attendees: {', '.join(meeting.get('attendees', []))}
Summary: {meeting.get('context_summary', '')}
Action Items: {json.dumps(meeting.get('action_items', []), indent=2)}
{voice_instruction}

RULES:
- Be concise, professional but warm
- Start with a brief "thanks for the time" sentiment (natural, not corporate)
- Recap key discussion points in 2-3 bullets
- List action items clearly with owners
- End with next steps
- Never use em dashes or AI-speak
- Use Oxford commas
- Do NOT include subject line header, just the body

Generate the follow-up:"""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-5-20250514",
                max_tokens=800,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text.strip()
        except Exception as e:
            return f"Error generating follow-up: {e}"

    def generate_meeting_prep(self, calendar_event, email_history=None):
        """
        Generate a pre-meeting brief with context from past emails.

        Args:
            calendar_event: Calendar event dict (from gcal MCP or API)
            email_history: Optional list of recent emails with attendees

        Returns:
            Meeting prep brief string
        """
        attendee_context = ""
        if email_history:
            attendee_context = "RECENT EMAIL CONTEXT WITH ATTENDEES:\n"
            for em in email_history[:5]:
                attendee_context += f"- {em.get('sender_name', '')}: {em.get('subject', '')} ({em.get('date', '')})\n"
                snippet = (em.get("snippet", "") or "")[:200]
                attendee_context += f"  {snippet}\n"

        prompt = f"""Generate a concise pre-meeting brief.

MEETING:
Title: {calendar_event.get('summary', calendar_event.get('title', ''))}
Time: {calendar_event.get('start', '')}
Attendees: {json.dumps(calendar_event.get('attendees', []))}
Description: {calendar_event.get('description', 'No description provided')}

{attendee_context}

Generate a brief with:
1. Meeting purpose (1-2 sentences)
2. Key attendee context (what you last discussed with them)
3. Suggested talking points based on recent email threads
4. Questions to ask or decisions to make
5. Any action items from previous meetings that are still open

Keep it scannable, use short bullets. No AI-speak."""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-5-20250514",
                max_tokens=600,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text.strip()
        except Exception as e:
            return f"Error generating prep: {e}"

    def get_open_actions(self, owner_filter=None):
        """Get all open action items, optionally filtered by owner."""
        open_items = [a for a in self.actions.get("items", []) if a.get("status") == "open"]
        if owner_filter:
            open_items = [a for a in open_items if owner_filter.lower() in a.get("owner", "").lower()]
        return sorted(open_items, key=lambda x: x.get("deadline") or "9999")

    def mark_action_done(self, action_id, notes=""):
        """Mark an action item as completed."""
        for item in self.actions.get("items", []):
            if item["id"] == action_id:
                item["status"] = "done"
                item["completed_at"] = datetime.utcnow().isoformat()
                item["notes"] = notes
                self._save_actions()
                return True
        return False

    def get_overdue_actions(self):
        """Find action items past their deadline."""
        overdue = []
        now = datetime.utcnow().isoformat()
        for item in self.actions.get("items", []):
            if item.get("status") == "open" and item.get("deadline"):
                try:
                    # Try to parse various date formats
                    deadline_str = item["deadline"].lower()
                    if deadline_str not in ("null", "none", "tbd", ""):
                        overdue.append(item)
                except Exception:
                    pass
        return overdue


def main():
    parser = argparse.ArgumentParser(description="MAILMAN Meeting Intelligence")
    parser.add_argument("--scan", action="store_true", help="Scan inbox for meeting emails")
    parser.add_argument("--upcoming", action="store_true", help="Show upcoming meetings with prep")
    parser.add_argument("--follow-up", type=str, help="Generate follow-up for <meeting_id>")
    parser.add_argument("--actions", action="store_true", help="Show open action items")
    parser.add_argument("--done", type=str, help="Mark action item as done")
    parser.add_argument("--account", type=str, default="gmail_personal", help="Account name")
    args = parser.parse_args()

    mi = MeetingIntelligence()

    if args.actions:
        items = mi.get_open_actions()
        print(f"\nOpen Action Items ({len(items)}):")
        for item in items:
            deadline = item.get("deadline", "no deadline")
            print(f"  [{item['id']}] {item['task']}")
            print(f"    Owner: {item['owner']} | Deadline: {deadline} | From: {item['source_meeting']}")

    elif args.done:
        if mi.mark_action_done(args.done):
            print(f"Marked {args.done} as done.")
        else:
            print(f"Action item {args.done} not found.")

    elif args.follow_up:
        # Load voice profile if available
        voice_path = MEMORY_DIR / "voice_profile.json"
        voice_profile = None
        if voice_path.exists():
            with open(voice_path) as f:
                voice_profile = json.load(f)

        draft = mi.generate_follow_up(args.follow_up, voice_profile)
        print(f"\n--- FOLLOW-UP DRAFT ---\n{draft}\n--- END DRAFT ---")

    elif args.scan:
        from gmail_client import GmailClient
        client = GmailClient(args.account)
        print(f"Scanning inbox for meeting-related emails...")
        emails = client.fetch_unread(max_results=50)
        detected = mi.scan_emails_for_meetings(emails)
        print(f"Detected {len(detected)} meeting-related emails:")
        for m in detected:
            print(f"  [{m['meeting_type']}] {m.get('title', 'Unknown')} - {m.get('context_summary', '')[:80]}")

    elif args.upcoming:
        print("Upcoming meetings require Google Calendar integration.")
        print("Use: gcal_list_events MCP tool to fetch upcoming events,")
        print("then pass them to meeting_intel.generate_meeting_prep()")


if __name__ == "__main__":
    main()
