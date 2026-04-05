#!/usr/bin/env python3
"""
MAILMAN Calendar Scheduler
Google Calendar-aware meeting scheduling module that extends meeting_intel.py.
Detects scheduling intents in emails, checks calendar availability, proposes
times intelligently, and generates natural scheduling replies.

Features:
- Meeting request detection (scheduling_intent, reschedule, cancel, etc.)
- Calendar availability checking (structured queries for gcal MCP tools)
- Smart time proposing based on user preferences and attendee availability
- Natural draft generation for scheduling replies
- Persistent tracking of pending scheduling requests
- AI-powered time reference parsing ("next Tuesday at 2pm", etc.)

Fyxer parity: Smart scheduling + availability coordination
Beyond Fyxer: Preference-aware time selection, async calendar checks,
              structured output for MCP integration

Usage:
  python3 calendar_scheduler.py --detect <message_id>    # Detect intent in email
  python3 calendar_scheduler.py --pending                 # Show pending scheduling
  python3 calendar_scheduler.py --preferences             # Show calendar prefs
  python3 calendar_scheduler.py --parse "<text>"         # Parse time references

Requires:
- config/calendar_config.json with scheduling preferences
- _memory/pending_scheduling.json for request tracking
- anthropic client for AI parsing
"""

import json
import re
import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any

try:
    import anthropic
except ImportError:
    print("Missing: pip install anthropic --break-system-packages")
    sys.exit(1)

MAILMAN_ROOT = Path(__file__).parent.parent
MEMORY_DIR = MAILMAN_ROOT / "_memory"
LOGS_DIR = MAILMAN_ROOT / "logs"
CONFIG_DIR = MAILMAN_ROOT / "config"
MEMORY_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)


class CalendarScheduler:
    """
    Handles meeting scheduling workflows: detecting intent, checking availability,
    proposing times, generating replies, and tracking pending requests.
    Produces structured output for external MCP tool invocation.
    """

    def __init__(self):
        self.client = anthropic.Anthropic()
        self.config = self._load_config()
        self.pending_path = MEMORY_DIR / "pending_scheduling.json"
        self.pending = self._load_json(self.pending_path, {"requests": []})

    def _load_config(self) -> Dict[str, Any]:
        """Load calendar preferences from config file."""
        config_path = CONFIG_DIR / "calendar_config.json"
        if config_path.exists():
            with open(config_path) as f:
                return json.load(f)
        # Default config if not found
        return {
            "timezone": "America/Los_Angeles",
            "preferred_hours": {"start": "10:00", "end": "17:00"},
            "buffer_minutes": 15,
            "max_meetings_per_day": 5,
            "no_meeting_days": ["Sunday"],
            "default_duration": 30,
            "preferred_platforms": ["Google Meet", "Zoom"],
        }

    def _load_json(self, path: Path, default: Dict) -> Dict:
        """Load JSON file or return default if not found."""
        if path.exists():
            try:
                with open(path) as f:
                    return json.load(f)
            except Exception:
                return default
        return default

    def _save_pending(self):
        """Persist pending scheduling requests."""
        with open(self.pending_path, "w") as f:
            json.dump(self.pending, f, indent=2)

    def detect_scheduling_intent(self, email_data: Dict) -> Optional[Dict]:
        """
        Analyze email to detect scheduling intent and extract meeting details.

        Detects: meeting_request, reschedule, cancel, availability_query, time_proposal

        Args:
            email_data: Email dict from GmailClient with subject, body, sender, etc.

        Returns:
            Dict with intent, suggested_times, duration, participants, topic, urgency
            or None if no scheduling intent detected.
        """
        subject = (email_data.get("subject") or "").lower()
        body = (email_data.get("body_text") or email_data.get("snippet") or "").lower()
        text = f"{subject} {body}"

        # Quick intent detection
        intent_patterns = {
            "meeting_request": [
                r"(?:can we|could we|let\'s|shall we)\s+(?:meet|hop on|jump on|sync|chat|talk)",
                r"(?:schedule|set up|book|arrange)\s+(?:a\s+)?(?:meeting|call|sync|chat|time)",
                r"(?:are you|would you be)\s+(?:free|available)\s+(?:for|to)",
                r"(?:do you have time|are you open)",
            ],
            "reschedule": [
                r"(?:move|reschedule|postpone|delay|change)\s+(?:our|the|this)\s+(?:meeting|call|sync)",
                r"(?:can\'t make|unable to make|won\'t be able to make)",
                r"(?:different time|new time|other time)\s+(?:for|to)",
            ],
            "cancel": [
                r"(?:cancel|call off|postpone indefinitely|drop)\s+(?:our|the|this)\s+(?:meeting|call)",
                r"(?:won\'t be able to|can\'t attend)",
            ],
            "availability_query": [
                r"(?:when are you|what time.*available|your availability|when works)",
                r"(?:what\'s your schedule|are you free)",
            ],
            "time_proposal": [
                r"(?:how about|what about|does).*\d{1,2}(?::\d{2})?\s*(?:am|pm)",
                r"(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)\s+(?:at|around)\s+\d",
                r"(?:tomorrow|next week|this week|next month)\s+at\s+",
            ],
        }

        detected_intent = None
        for intent, patterns in intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text):
                    detected_intent = intent
                    break
            if detected_intent:
                break

        if not detected_intent:
            return None

        # Use Claude to extract structured details
        return self._extract_scheduling_details(email_data, detected_intent)

    def _extract_scheduling_details(
        self, email_data: Dict, intent: str
    ) -> Optional[Dict]:
        """Use Claude to extract structured scheduling details from an email."""
        body = (email_data.get("body_text") or email_data.get("snippet") or "")[:3000]

        prompt = f"""Extract scheduling details from this email. Return ONLY valid JSON.

EMAIL:
From: {email_data.get('sender_name', '')} <{email_data.get('sender_email', '')}>
Subject: {email_data.get('subject', '')}
Body: {body}

Detected Intent: {intent}

Return this JSON structure:
{{
  "intent": "{intent}",
  "topic": "<meeting topic/title>",
  "suggested_times": [
    {{"day": "Monday March 17", "time_range": "2:00 PM - 3:00 PM", "raw_text": "how about Monday at 2pm?"}}
  ],
  "duration_minutes": <30, 60, etc. or null if unclear>,
  "participants": ["list of people mentioned as attendees"],
  "required_participants": ["critical attendees who must attend"],
  "optional_participants": ["people who optional"],
  "preferred_platforms": ["Zoom", "Google Meet", "in person", etc.],
  "timezone_mentioned": "<timezone if mentioned, else null>",
  "urgency": "low|normal|high|critical",
  "context_summary": "<1-2 sentence summary of what the meeting is about>"
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

            details = json.loads(result)
            details["id"] = email_data.get("id", "")
            details["source_email_id"] = email_data.get("id", "")
            details["sender_email"] = email_data.get("sender_email", "")
            details["sender_name"] = email_data.get("sender_name", "")
            details["subject"] = email_data.get("subject", "")
            details["detected_at"] = datetime.utcnow().isoformat()

            return details

        except Exception as e:
            print(f"Scheduling detail extraction error: {e}")
            return None

    def check_availability(
        self, date_range: Dict, duration_minutes: int = 30
    ) -> Dict:
        """
        Produce a structured query for gcal_find_my_free_time.

        Args:
            date_range: {"start": "2026-03-16", "end": "2026-03-20"} (ISO dates)
            duration_minutes: Meeting duration in minutes

        Returns:
            Query dict for gcal MCP tool with timeMin, timeMax, calendarId
        """
        start = date_range.get("start", "")
        end = date_range.get("end", "")

        # Convert dates to RFC3339 format for Google Calendar
        time_min = f"{start}T00:00:00" if start else ""
        time_max = f"{end}T23:59:59" if end else ""

        return {
            "timeMin": time_min,
            "timeMax": time_max,
            "calendarId": "primary",
            "minDuration": duration_minutes,
            "timezone": self.config.get("timezone", "America/Los_Angeles"),
        }

    def find_mutual_times(
        self, attendee_emails: List[str], duration_minutes: int = 30, date_range: Optional[Dict] = None
    ) -> Dict:
        """
        Produce a structured query for gcal_find_meeting_times.

        Args:
            attendee_emails: List of attendee email addresses
            duration_minutes: Meeting duration in minutes
            date_range: Optional {"start": "2026-03-16", "end": "2026-03-20"}

        Returns:
            Query dict for gcal_find_meeting_times MCP tool
        """
        if not date_range:
            # Default to next 5 business days
            today = datetime.now()
            date_range = {
                "start": today.strftime("%Y-%m-%d"),
                "end": (today + timedelta(days=5)).strftime("%Y-%m-%d"),
            }

        time_min = f"{date_range['start']}T00:00:00"
        time_max = f"{date_range['end']}T23:59:59"

        prefs = self.config.get("preferred_hours", {})
        start_hour = int(prefs.get("start", "10:00").split(":")[0])
        end_hour = int(prefs.get("end", "17:00").split(":")[0])

        return {
            "attendees": attendee_emails,
            "duration": duration_minutes,
            "timeMin": time_min,
            "timeMax": time_max,
            "timeZone": self.config.get("timezone", "America/Los_Angeles"),
            "preferences": {
                "startHour": start_hour,
                "endHour": end_hour,
                "excludeWeekends": True,
                "maxResults": 3,
            },
        }

    def get_schedule(self, date: str) -> Dict:
        """
        Produce a structured query for gcal_list_events for a specific day.

        Args:
            date: ISO date string "2026-03-16"

        Returns:
            Query dict for gcal_list_events MCP tool
        """
        time_min = f"{date}T00:00:00"
        next_day = (datetime.fromisoformat(date) + timedelta(days=1)).strftime("%Y-%m-%d")
        time_max = f"{next_day}T00:00:00"

        return {
            "calendarId": "primary",
            "timeMin": time_min,
            "timeMax": time_max,
            "timeZone": self.config.get("timezone", "America/Los_Angeles"),
        }

    def propose_times(
        self,
        available_slots: List[Dict],
        preferences: Optional[Dict] = None,
    ) -> List[Dict]:
        """
        Select best meeting times from available slots based on preferences.

        Args:
            available_slots: List of free time slots (from gcal_find_my_free_time or similar)
                Each slot: {"start": "2026-03-16T14:00:00Z", "end": "...", "duration": "60"}
            preferences: Optional override preferences (uses config by default)

        Returns:
            List of 3 best proposed times with reasoning
        """
        if not available_slots:
            return []

        prefs = preferences or self.config

        # Filter slots based on preferences
        filtered = []
        for slot in available_slots:
            # Parse slot time
            try:
                start_str = slot.get("start") or slot.get("startFormatted", "")
                if "T" in start_str:
                    start_dt = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                else:
                    continue

                # Check if day is allowed
                day_name = start_dt.strftime("%A")
                if day_name in prefs.get("no_meeting_days", []):
                    continue

                # Check if time is in preferred hours
                pref_hours = prefs.get("preferred_hours", {})
                pref_start = int(pref_hours.get("start", "10:00").split(":")[0])
                pref_end = int(pref_hours.get("end", "17:00").split(":")[0])

                if not (pref_start <= start_dt.hour < pref_end):
                    continue

                filtered.append({
                    "start": slot.get("start") or slot.get("startFormatted", ""),
                    "end": slot.get("end") or slot.get("endFormatted", ""),
                    "duration": slot.get("duration", "unknown"),
                    "day": day_name,
                    "time": start_dt.strftime("%I:%M %p"),
                })
            except Exception:
                continue

        # Return top 3
        return filtered[:3]

    def draft_scheduling_reply(
        self,
        email_data: Dict,
        proposed_times: List[Dict],
        voice_profile: Optional[Dict] = None,
    ) -> str:
        """
        Generate a natural reply proposing meeting times.

        Args:
            email_data: Original email dict
            proposed_times: List of proposed times (from propose_times)
            voice_profile: Optional voice profile for tone matching

        Returns:
            Draft email reply text
        """
        voice_instruction = ""
        if voice_profile and voice_profile.get("ai_analysis"):
            voice_instruction = f"\nVOICE GUIDANCE:\n{voice_profile['ai_analysis'].get('voice_summary', '')}"

        times_text = ""
        for i, t in enumerate(proposed_times[:3], 1):
            times_text += f"{i}. {t.get('day', '')} at {t.get('time', '')} ({t.get('duration', 'TBD')} min)\n"

        prompt = f"""Generate a natural scheduling reply. This is being sent BY the user.

ORIGINAL EMAIL:
From: {email_data.get('sender_name', '')}
Subject: {email_data.get('subject', '')}
Body snippet: {(email_data.get('body_text') or '')[:500]}

PROPOSED TIMES TO OFFER:
{times_text}

{voice_instruction}

RULES:
- Sound natural, not robotic
- Start with a warm acknowledgment ("Happy to sync...")
- List proposed times clearly
- Ask them to let you know which works
- Keep it short (3-4 sentences)
- Never use em dashes or corporate jargon
- Use Oxford commas
- Do NOT include subject line, just the body

Generate the reply:"""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-5-20250514",
                max_tokens=400,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text.strip()
        except Exception as e:
            return f"Error generating reply: {e}"

    def draft_confirmation_reply(self, email_data: Dict, confirmed_time: Dict) -> str:
        """
        Generate a reply confirming a scheduled meeting.

        Args:
            email_data: Original email dict
            confirmed_time: Confirmed time dict with start, end, etc.

        Returns:
            Confirmation email text
        """
        time_str = confirmed_time.get("start", "TBD")
        if "T" in time_str:
            try:
                dt = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
                time_str = dt.strftime("%A, %B %d at %I:%M %p")
            except Exception:
                pass

        prompt = f"""Generate a brief confirmation email. Being sent BY the user.

Original email from: {email_data.get('sender_name', '')}
Meeting: {email_data.get('subject', '')}
Confirmed time: {time_str}

Keep it very brief (1-2 sentences):
- Confirm the time
- Express enthusiasm
- Mention any platform/details if known

No subject line, just body:"""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-5-20250514",
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text.strip()
        except Exception as e:
            return f"Error: {e}"

    def draft_reschedule_reply(
        self, email_data: Dict, new_times: List[Dict], reason: Optional[str] = None
    ) -> str:
        """
        Generate a reply proposing a reschedule.

        Args:
            email_data: Original email dict
            new_times: List of new proposed times
            reason: Optional reason for rescheduling

        Returns:
            Reschedule proposal email text
        """
        times_text = ""
        for i, t in enumerate(new_times[:3], 1):
            times_text += f"{i}. {t.get('day', '')} at {t.get('time', '')}\n"

        reason_note = f"Unfortunately, {reason}. " if reason else ""

        prompt = f"""Generate a rescheduling request. Being sent BY the user.

Original meeting: {email_data.get('subject', '')}
Sent by: {email_data.get('sender_name', '')}

{reason_note}

New times to propose:
{times_text}

Keep it professional but warm:
- Apologize briefly for the inconvenience
- Mention the reason if provided
- Offer new times
- Suggest making it work soon

Short (3-4 sentences), no subject line:"""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-5-20250514",
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text.strip()
        except Exception as e:
            return f"Error: {e}"

    def draft_decline_reply(self, email_data: Dict, reason: Optional[str] = None) -> str:
        """
        Generate a polite decline for a meeting request.

        Args:
            email_data: Original email dict
            reason: Optional reason for declining

        Returns:
            Decline email text
        """
        reason_note = f"I'm unable to attend due to {reason}. " if reason else ""

        prompt = f"""Generate a polite meeting decline. Being sent BY the user.

Requested by: {email_data.get('sender_name', '')}
Meeting: {email_data.get('subject', '')}

{reason_note}

Keep it warm and professional:
- Thank them for including you
- Briefly explain why (if reason provided)
- Suggest an alternative if appropriate
- Keep door open for future

Short (2-3 sentences), no subject:"""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-5-20250514",
                max_tokens=250,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text.strip()
        except Exception as e:
            return f"Error: {e}"

    def create_event_payload(
        self, email_data: Dict, confirmed_time: Dict, duration_minutes: Optional[int] = None
    ) -> Dict:
        """
        Generate a payload for gcal_create_event.

        Args:
            email_data: Original email dict
            confirmed_time: Confirmed time dict from proposing/scheduling
            duration_minutes: Duration (uses config default if not provided)

        Returns:
            Payload dict for gcal_create_event MCP tool
        """
        if duration_minutes is None:
            duration_minutes = self.config.get("default_duration", 30)

        # Parse time
        start_str = confirmed_time.get("start", "")
        try:
            start_dt = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
        except Exception:
            start_dt = datetime.now()

        end_dt = start_dt + timedelta(minutes=duration_minutes)

        # Build attendees list
        attendees = []
        if email_data.get("sender_email"):
            attendees.append({
                "email": email_data.get("sender_email"),
                "displayName": email_data.get("sender_name", ""),
            })

        return {
            "summary": email_data.get("subject", "Meeting"),
            "description": f"Meeting scheduled from email: {email_data.get('subject', '')}\n\n"
            f"Original sender: {email_data.get('sender_email', '')}\n\n"
            f"Context: {(email_data.get('body_text') or '')[:500]}",
            "start": {
                "dateTime": start_dt.isoformat(),
                "timeZone": self.config.get("timezone", "America/Los_Angeles"),
            },
            "end": {
                "dateTime": end_dt.isoformat(),
                "timeZone": self.config.get("timezone", "America/Los_Angeles"),
            },
            "attendees": attendees,
            "conferenceData": {
                "createRequest": {
                    "conferenceSolutionKey": {"type": "hangoutsMeet"},
                    "requestId": f"meet_{int(datetime.now().timestamp())}",
                }
            } if "Meet" in self.config.get("preferred_platforms", []) else None,
        }

    def track_pending_scheduling(self, email_data: Dict, proposed_times: List[Dict]) -> str:
        """
        Record a pending scheduling request for follow-up.

        Args:
            email_data: Original email dict
            proposed_times: Times proposed to the sender

        Returns:
            Request ID for tracking
        """
        request_id = f"sched_{len(self.pending['requests']) + 1}_{int(datetime.now().timestamp())}"

        request = {
            "id": request_id,
            "email_id": email_data.get("id", ""),
            "sender_email": email_data.get("sender_email", ""),
            "sender_name": email_data.get("sender_name", ""),
            "subject": email_data.get("subject", ""),
            "proposed_times": proposed_times,
            "created_at": datetime.utcnow().isoformat(),
            "status": "awaiting_response",
            "resolution": None,
        }

        self.pending["requests"].append(request)
        self._save_pending()

        return request_id

    def get_pending(self) -> List[Dict]:
        """Get all pending scheduling requests awaiting response."""
        return [r for r in self.pending.get("requests", [])
                if r.get("status") == "awaiting_response"]

    def resolve_pending(self, request_id: str, outcome: str, notes: str = "") -> bool:
        """
        Mark a pending request as resolved.

        Args:
            request_id: Pending request ID
            outcome: "scheduled", "declined", "expired"
            notes: Optional resolution notes

        Returns:
            True if resolved, False if not found
        """
        for req in self.pending.get("requests", []):
            if req["id"] == request_id:
                req["status"] = "resolved"
                req["resolution"] = outcome
                req["resolved_at"] = datetime.utcnow().isoformat()
                req["notes"] = notes
                self._save_pending()
                return True
        return False

    def parse_time_references(self, text: str) -> Optional[Dict]:
        """
        Use Claude to extract structured time references from text.

        Examples: "next Tuesday at 2pm", "sometime this week", "after the holiday"

        Args:
            text: Email text containing time references

        Returns:
            Dict with parsed_references list containing datetime ranges
        """
        prompt = f"""Extract all time references from this text. Return ONLY valid JSON.

TEXT:
{text}

Return this JSON structure:
{{
  "parsed_references": [
    {{"raw_text": "next Tuesday at 2pm", "implied_start": "2026-03-17T14:00:00", "implied_end": "2026-03-17T17:00:00", "confidence": 0.95}},
    {{"raw_text": "this week", "implied_start": "2026-03-16", "implied_end": "2026-03-20", "confidence": 0.8}}
  ],
  "primary_window": {{"start": "2026-03-17", "end": "2026-03-20"}},
  "any_exclusions": ["times/days they mentioned as unavailable"]
}}"""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-5-20250514",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}],
            )
            result = response.content[0].text.strip()
            if result.startswith("```"):
                result = result.split("\n", 1)[1].rsplit("```", 1)[0]
            return json.loads(result)
        except Exception as e:
            print(f"Time parsing error: {e}")
            return None


def main():
    parser = argparse.ArgumentParser(
        description="MAILMAN Calendar Scheduler - Meeting scheduling with calendar awareness"
    )
    parser.add_argument("--detect", type=str, help="Detect scheduling intent in email <message_id>")
    parser.add_argument("--pending", action="store_true", help="Show pending scheduling requests")
    parser.add_argument("--resolve", type=str, help="Resolve pending request <request_id>")
    parser.add_argument(
        "--outcome", type=str, choices=["scheduled", "declined", "expired"],
        help="Outcome for --resolve (scheduled/declined/expired)"
    )
    parser.add_argument("--preferences", action="store_true", help="Show calendar preferences")
    parser.add_argument("--parse", type=str, help="Parse time references in text")
    parser.add_argument("--account", type=str, default="gmail_personal", help="Account name")
    args = parser.parse_args()

    scheduler = CalendarScheduler()

    if args.preferences:
        print("\nCalendar Preferences:")
        print(json.dumps(scheduler.config, indent=2))

    elif args.pending:
        pending = scheduler.get_pending()
        print(f"\nPending Scheduling Requests ({len(pending)}):")
        for req in pending:
            times_str = ", ".join([t.get("time", "TBD") for t in req.get("proposed_times", [])[:2]])
            print(f"  [{req['id']}] {req['sender_name']} - {req['subject']}")
            print(f"    Proposed: {times_str}")
            print(f"    Created: {req['created_at']}")

    elif args.resolve and args.outcome:
        if scheduler.resolve_pending(args.resolve, args.outcome):
            print(f"Resolved {args.resolve} as {args.outcome}")
        else:
            print(f"Request {args.resolve} not found")

    elif args.parse:
        parsed = scheduler.parse_time_references(args.parse)
        if parsed:
            print("\nParsed Time References:")
            print(json.dumps(parsed, indent=2))
        else:
            print("Could not parse time references")

    elif args.detect:
        print(f"Detecting scheduling intent in email {args.detect}")
        print("(requires integration with GmailClient to fetch email data)")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
