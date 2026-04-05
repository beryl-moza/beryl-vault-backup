#!/usr/bin/env python3
"""
MAILMAN Orchestrator v2
The master controller that wires together all MAILMAN modules
AND the existing ARC agent ecosystem.

This is the single entry point for running MAILMAN operations.
It routes work to the right module or ARC agent based on the task.

Phase 1-2 Modules (13):
  auth, gmail_client, classifier, unsubscriber, digest, security,
  contacts, voice_learner, meeting_intel, mailman_chat, orchestrator,
  auto_labeler, email_analytics

Phase 4 Modules (7):
  rules_engine, slack_bridge, calendar_scheduler, task_extractor,
  smart_replies, vip_gatekeeper, templates

ARC Agents Integrated:
- arc-inbox        -> Inbound email triage methodology
- arc-email-crafter -> Brand-voice email drafting (Antidote, ZYVA, etc.)
- arc-email-reviewer -> Pre-send validation (compliance, brand, CAN-SPAM)
- arc-outreach      -> Campaign management, sequences, lists
- arc-telegram      -> Delivery notifications, escalations
- arc-slack          -> Team channel updates
- arc-coordinator   -> Complex multi-agent workflows
- arc-nightwatch    -> Scheduled overnight runs

Usage:
  python3 orchestrator.py triage [--account <name>]
  python3 orchestrator.py unsubscribe [--preview] [--account <name>]
  python3 orchestrator.py digest [--period daily|weekly]
  python3 orchestrator.py draft-reply <message_id> [--tone <override>]
  python3 orchestrator.py draft-new "<prompt>" [--brand <voice>]
  python3 orchestrator.py smart-reply <message_id>
  python3 orchestrator.py chat "<question>"
  python3 orchestrator.py meetings [--scan|--upcoming|--follow-up <id>]
  python3 orchestrator.py schedule-meeting <message_id>
  python3 orchestrator.py tasks [--list|--today|--overdue]
  python3 orchestrator.py rules [--list|--stats]
  python3 orchestrator.py focus [--mode normal|focus|dnd]
  python3 orchestrator.py templates [--list|--suggest <message_id>]
  python3 orchestrator.py analytics [--period 7|30|90]
  python3 orchestrator.py train-voice [--account <name>]
  python3 orchestrator.py security-scan [--account <name>]
  python3 orchestrator.py full-cycle [--account <name>]
"""

import json
import argparse
import sys
from datetime import datetime
from pathlib import Path

MAILMAN_ROOT = Path(__file__).parent.parent
CORE_DIR = Path(__file__).parent
MEMORY_DIR = MAILMAN_ROOT / "_memory"
LOGS_DIR = MAILMAN_ROOT / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# ARC agent paths (resolved dynamically)
# These point to the shared agent definitions in the ARC ecosystem
ARC_AGENTS = {
    "inbox": "CLAUDE_MASTER/ANTIDOTE SHARED/.claude/agents/arc-inbox.md",
    "email_crafter": "CLAUDE_MASTER/ANTIDOTE SHARED/.claude/agents/arc-email-crafter.md",
    "email_reviewer": "CLAUDE_MASTER/ANTIDOTE SHARED/.claude/agents/arc-email-reviewer.md",
    "outreach": "CLAUDE_MASTER/ANTIDOTE SHARED/.claude/agents/arc-outreach.md",
    "telegram": "CLAUDE_MASTER/ANTIDOTE SHARED/.claude/agents/arc-telegram.md",
    "slack": "CLAUDE_MASTER/ANTIDOTE SHARED/.claude/agents/arc-slack.md",
    "coordinator": "ARC_BRAIN/.claude/agents/arc-coordinator.md",
}

# Nightwatch integration
NIGHTWATCH_PATH = "ARC_BRAIN/_SKILLS/scripts/arc-nightwatch.py"


def _resolve_dropbox():
    """Find the Dropbox root, handling both local and Cowork session paths."""
    candidates = [
        Path.home() / "Dropbox",
        Path("/sessions") / "magical-sharp-brahmagupta" / "mnt" / "Dropbox",
    ]
    # Also try parent directories of MAILMAN_ROOT
    p = MAILMAN_ROOT
    while p != p.parent:
        if (p / "ARC_BRAIN").exists():
            return p
        p = p.parent
    for c in candidates:
        if c.exists():
            return c
    return None


DROPBOX_ROOT = _resolve_dropbox()


class MailmanOrchestrator:
    """
    Central orchestrator for all MAILMAN operations.
    Routes work to internal modules and external ARC agents.
    """

    def __init__(self, account="gmail_personal"):
        self.account = account
        self.log_path = LOGS_DIR / "orchestrator_log.jsonl"

        # Lazy-load modules to avoid import overhead for unused features
        # Phase 1-2
        self._gmail = None
        self._classifier = None
        self._unsubscriber = None
        self._digest = None
        self._security = None
        self._contacts = None
        self._voice = None
        self._meetings = None
        self._chat = None
        self._auto_label = None
        self._analytics = None
        # Phase 4
        self._rules = None
        self._slack = None
        self._calendar = None
        self._tasks = None
        self._smart_replies = None
        self._gatekeeper = None
        self._templates = None

    def _log(self, action, details=None):
        """Log orchestrator actions."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "account": self.account,
            "details": details or {},
        }
        with open(self.log_path, "a") as f:
            f.write(json.dumps(entry) + "\n")

    # --- Module Loaders (lazy) ---

    @property
    def gmail(self):
        if not self._gmail:
            from gmail_client import GmailClient
            self._gmail = GmailClient(self.account)
        return self._gmail

    @property
    def classifier(self):
        if not self._classifier:
            from classifier import EmailClassifier
            self._classifier = EmailClassifier()
        return self._classifier

    @property
    def unsubscriber(self):
        if not self._unsubscriber:
            from unsubscriber import UnsubscribeEngine
            self._unsubscriber = UnsubscribeEngine()
        return self._unsubscriber

    @property
    def digest_engine(self):
        if not self._digest:
            from digest import DigestGenerator
            self._digest = DigestGenerator()
        return self._digest

    @property
    def security(self):
        if not self._security:
            from security import SecurityScanner
            self._security = SecurityScanner()
        return self._security

    @property
    def contacts(self):
        if not self._contacts:
            from contacts import ContactIntelligence
            self._contacts = ContactIntelligence()
        return self._contacts

    @property
    def voice(self):
        if not self._voice:
            from voice_learner import VoiceLearner
            self._voice = VoiceLearner()
        return self._voice

    @property
    def meetings(self):
        if not self._meetings:
            from meeting_intel import MeetingIntelligence
            self._meetings = MeetingIntelligence()
        return self._meetings

    @property
    def chat(self):
        if not self._chat:
            from mailman_chat import MailmanChat
            self._chat = MailmanChat()
        return self._chat

    @property
    def auto_label(self):
        if not self._auto_label:
            from auto_labeler import AutoLabeler
            self._auto_label = AutoLabeler()
        return self._auto_label

    @property
    def analytics(self):
        if not self._analytics:
            from email_analytics import EmailAnalytics
            self._analytics = EmailAnalytics()
        return self._analytics

    # --- Phase 4 Module Loaders ---

    @property
    def rules(self):
        if not self._rules:
            from rules_engine import RulesEngine
            self._rules = RulesEngine()
        return self._rules

    @property
    def slack_bridge(self):
        if not self._slack:
            from slack_bridge import SlackBridge
            self._slack = SlackBridge()
        return self._slack

    @property
    def calendar(self):
        if not self._calendar:
            from calendar_scheduler import CalendarScheduler
            self._calendar = CalendarScheduler()
        return self._calendar

    @property
    def tasks(self):
        if not self._tasks:
            from task_extractor import TaskExtractor
            self._tasks = TaskExtractor()
        return self._tasks

    @property
    def smart_reply(self):
        if not self._smart_replies:
            from smart_replies import SmartReplies
            self._smart_replies = SmartReplies()
        return self._smart_replies

    @property
    def gatekeeper(self):
        if not self._gatekeeper:
            from vip_gatekeeper import VIPGatekeeper
            self._gatekeeper = VIPGatekeeper()
        return self._gatekeeper

    @property
    def template_lib(self):
        if not self._templates:
            from templates import TemplateLibrary
            self._templates = TemplateLibrary()
        return self._templates

    # --- Core Operations ---

    def full_cycle(self, max_emails=50):
        """
        Run a complete MAILMAN v2 cycle:
         1. Fetch unread emails
         2. Security scan all of them
         3. Classify and prioritize
         4. Run automation rules engine
         5. Auto-label in Gmail
         6. VIP Gatekeeper filter
         7. Extract tasks from P1 ACTION emails
         8. Detect meeting scheduling requests
         9. Flag unsubscribe candidates
        10. Update contact intelligence
        11. Scan for meeting content
        12. Index for semantic search
        13. Generate Slack triage summary
        14. Log everything

        This is what nightwatch runs overnight.
        """
        print(f"\n{'='*60}")
        print(f"  MAILMAN FULL CYCLE v2 - {self.account}")
        print(f"  {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
        print(f"{'='*60}\n")

        self._log("full_cycle_start", {"max_emails": max_emails})

        # 1. Fetch
        print("[1/14] Fetching unread emails...")
        emails = self.gmail.fetch_unread(max_results=max_emails)
        print(f"       Found {len(emails)} unread emails.\n")

        if not emails:
            print("No unread emails. Cycle complete.")
            self._log("full_cycle_end", {"total": 0})
            return

        results = {
            "total": len(emails),
            "security_alerts": 0,
            "classified": {"P0": 0, "P1": 0, "P2": 0, "P3": 0, "P4": 0},
            "rules_triggered": 0,
            "tasks_extracted": 0,
            "scheduling_detected": 0,
            "unsub_candidates": 0,
            "meetings_detected": 0,
            "contacts_updated": 0,
            "indexed": 0,
            "surfaced": 0,
            "deferred": 0,
            "slack_actions": [],
        }

        # 2. Security scan
        print("[2/14] Running security scan...")
        for email in emails:
            scan = self.security.scan_email(email)
            email["_security"] = scan
            if scan.get("risk_score", 0) >= 70:
                results["security_alerts"] += 1
                print(f"       ALERT: {email.get('sender_email', '')} - {scan.get('risk_factors', [])}")
                # Generate Slack security alert
                try:
                    alert = self.slack_bridge.format_security_alert(email, scan)
                    results["slack_actions"].append(alert)
                except Exception:
                    pass
        print(f"       Security alerts: {results['security_alerts']}\n")

        # 3. Classify
        print("[3/14] Classifying emails...")
        for email in emails:
            thread_count = self.gmail.get_thread_count(email.get("thread_id", ""))
            sender_freq = self.gmail.get_sender_frequency(email.get("sender_email", ""))
            classification = self.classifier.classify_email(email, thread_count, sender_freq)
            email["_classification"] = classification
            priority = classification.get("priority", "P3")
            results["classified"][priority] = results["classified"].get(priority, 0) + 1
        for p in ["P0", "P1", "P2", "P3", "P4"]:
            print(f"       {p}: {results['classified'][p]}")
        print()

        # 4. Run automation rules
        print("[4/14] Running automation rules...")
        for email in emails:
            cl = email.get("_classification", {})
            try:
                triggered = self.rules.evaluate(email, cl)
                if triggered:
                    actions = []
                    for rule_match in triggered:
                        actions.extend(rule_match.get("actions", []))
                    self.rules.execute_actions(email, actions, self.gmail)
                    results["rules_triggered"] += len(triggered)
                    email["_rules_applied"] = [r.get("rule_id") for r in triggered]
            except Exception as e:
                print(f"       Rules error: {e}")
        print(f"       {results['rules_triggered']} rules triggered.\n")

        # 5. Auto-label
        print("[5/14] Applying Gmail labels...")
        try:
            labeled = self.auto_label.apply_labels(emails, self.gmail)
            print(f"       Applied labels to {labeled} emails.\n")
        except Exception as e:
            print(f"       Auto-label skipped: {e}\n")

        # 6. VIP Gatekeeper filter
        print("[6/14] Running VIP Gatekeeper...")
        try:
            classifications = {e["id"]: e.get("_classification", {}) for e in emails}
            surfaced, deferred = self.gatekeeper.filter_inbox(emails, classifications)
            results["surfaced"] = len(surfaced)
            results["deferred"] = len(deferred)
            print(f"       Surfaced: {len(surfaced)}, Deferred: {len(deferred)}\n")
        except Exception as e:
            print(f"       Gatekeeper skipped: {e}\n")

        # 7. Extract tasks from P1 ACTION emails
        print("[7/14] Extracting tasks from actionable emails...")
        for email in emails:
            cl = email.get("_classification", {})
            if cl.get("priority") in ["P0", "P1"] and cl.get("needs_response"):
                try:
                    extracted = self.tasks.extract_tasks(email, cl)
                    if extracted:
                        for task in extracted:
                            self.tasks.create_task(task)
                        results["tasks_extracted"] += len(extracted)
                except Exception as e:
                    print(f"       Task extraction error: {e}")
        print(f"       {results['tasks_extracted']} tasks extracted.\n")

        # 8. Detect meeting scheduling requests
        print("[8/14] Detecting scheduling requests...")
        for email in emails:
            try:
                intent = self.calendar.detect_scheduling_intent(email)
                if intent and intent.get("intent") in ["meeting_request", "reschedule", "availability_query"]:
                    results["scheduling_detected"] += 1
                    self.calendar.track_pending_scheduling(email, intent.get("suggested_times", []))
                    print(f"       [{intent['intent']}] {email.get('subject', '')[:50]}")
            except Exception as e:
                pass
        print(f"       {results['scheduling_detected']} scheduling requests detected.\n")

        # 9. Unsubscribe candidates
        print("[9/14] Flagging unsubscribe candidates...")
        unsub_candidates = []
        for email in emails:
            cl = email.get("_classification", {})
            if cl.get("priority") == "P4" and email.get("list_unsubscribe"):
                unsub_candidates.append(email)
        results["unsub_candidates"] = len(unsub_candidates)
        if unsub_candidates:
            self.unsubscriber.queue_for_review(unsub_candidates)
        print(f"       {len(unsub_candidates)} new unsubscribe candidates queued.\n")

        # 10. Contact intelligence
        print("[10/14] Updating contact database...")
        for email in emails:
            self.contacts.update_contact(email, direction="inbound")
            results["contacts_updated"] += 1
        print(f"        Updated {results['contacts_updated']} contact records.\n")

        # 11. Meeting scan
        print("[11/14] Scanning for meeting content...")
        meeting_emails = self.meetings.scan_emails_for_meetings(emails)
        results["meetings_detected"] = len(meeting_emails)
        for m in meeting_emails:
            print(f"        [{m.get('meeting_type', '')}] {m.get('title', 'Unknown')}")
        print(f"        {len(meeting_emails)} meeting-related emails detected.\n")

        # 12. Index for search
        print("[12/14] Indexing for semantic search...")
        indexed = self.chat.index_emails(emails, self.account)
        results["indexed"] = indexed
        print()

        # 13. Generate Slack triage summary
        print("[13/14] Preparing Slack triage summary...")
        try:
            triage_msg = self.slack_bridge.format_triage_summary(emails)
            results["slack_actions"].append(triage_msg)
            print(f"        Triage summary ready for Slack.\n")
        except Exception as e:
            print(f"        Slack summary skipped: {e}\n")

        # 14. Summary
        print("[14/14] Cycle complete.\n")
        print(f"{'='*60}")
        print(f"  MAILMAN v2 CYCLE SUMMARY")
        print(f"{'='*60}")
        print(f"  Emails processed:    {results['total']}")
        print(f"  Security alerts:     {results['security_alerts']}")
        print(f"  P0 (FIRE):           {results['classified']['P0']}")
        print(f"  P1 (ACTION):         {results['classified']['P1']}")
        print(f"  P2 (REVIEW):         {results['classified']['P2']}")
        print(f"  P3 (LOW):            {results['classified']['P3']}")
        print(f"  P4 (JUNK):           {results['classified']['P4']}")
        print(f"  Rules triggered:     {results['rules_triggered']}")
        print(f"  Tasks extracted:     {results['tasks_extracted']}")
        print(f"  Scheduling requests: {results['scheduling_detected']}")
        print(f"  Surfaced / Deferred: {results['surfaced']} / {results['deferred']}")
        print(f"  Unsub candidates:    {results['unsub_candidates']}")
        print(f"  Meetings detected:   {results['meetings_detected']}")
        print(f"  Contacts updated:    {results['contacts_updated']}")
        print(f"  Emails indexed:      {results['indexed']}")
        print(f"  Slack actions queued:{len(results['slack_actions'])}")
        print(f"{'='*60}\n")

        self._log("full_cycle_end", results)
        return results

    def triage(self, max_emails=50):
        """Quick triage: classify + security scan only."""
        print(f"Running triage on '{self.account}'...")
        emails = self.gmail.fetch_unread(max_results=max_emails)

        for email in emails:
            # Security first
            scan = self.security.scan_email(email)
            if scan.get("risk_score", 0) >= 70:
                print(f"  SECURITY ALERT: {email.get('sender_email', '')} (score: {scan['risk_score']})")

            # Classify
            thread_count = self.gmail.get_thread_count(email.get("thread_id", ""))
            sender_freq = self.gmail.get_sender_frequency(email.get("sender_email", ""))
            cl = self.classifier.classify_email(email, thread_count, sender_freq)
            priority = cl.get("priority", "P3")
            print(f"  [{priority}] {email.get('sender_email', '')}: {email.get('subject', '')[:60]}")

        self._log("triage", {"count": len(emails)})

    def draft_reply(self, message_id, tone=None, use_arc_crafter=False, brand=None):
        """
        Draft a reply to an email.

        Routes to:
        - voice_learner for personal emails (matches your voice)
        - arc-email-crafter for brand emails (Antidote, ZYVA, etc.)
        """
        email = self.gmail.get_message(message_id)
        if not email:
            print(f"Message {message_id} not found.")
            return None

        if use_arc_crafter or brand:
            # Route to arc-email-crafter for brand-voice emails
            print(f"Routing to arc-email-crafter (brand: {brand or 'Antidote'})...")
            return self._route_to_arc_crafter(email, brand or "Antidote")
        else:
            # Use voice learner for personal emails
            draft = self.voice.draft_reply(email, self.gmail, tone_override=tone)
            self._log("draft_reply", {"message_id": message_id, "method": "voice_learner"})
            return draft

    def _route_to_arc_crafter(self, email, brand):
        """
        Prepare context for arc-email-crafter agent.
        Returns a structured brief that arc-email-crafter can consume.
        """
        brief = {
            "task": "draft_reply",
            "brand_voice": brand,
            "original_email": {
                "sender": email.get("sender_email", ""),
                "sender_name": email.get("sender_name", ""),
                "subject": email.get("subject", ""),
                "body": (email.get("body_text", "") or "")[:2000],
                "date": email.get("date", ""),
            },
            "instructions": f"Draft a reply in {brand} brand voice. "
                            "Follow all brand guidelines. Never auto-send.",
        }
        # Save brief for arc-email-crafter to pick up
        brief_path = MAILMAN_ROOT / "_incoming" / f"crafter_brief_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        with open(brief_path, "w") as f:
            json.dump(brief, f, indent=2)
        print(f"Brief saved for arc-email-crafter: {brief_path}")
        self._log("route_to_crafter", {"brand": brand, "brief_path": str(brief_path)})
        return brief

    def route_to_reviewer(self, draft_text, email_type="personal"):
        """
        Send a draft through arc-email-reviewer for quality check.
        Returns validation results.
        """
        review_brief = {
            "task": "review_email",
            "email_type": email_type,
            "draft": draft_text,
            "timestamp": datetime.utcnow().isoformat(),
        }
        brief_path = MAILMAN_ROOT / "_incoming" / f"review_brief_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        with open(brief_path, "w") as f:
            json.dump(review_brief, f, indent=2)
        print(f"Draft sent for review: {brief_path}")
        self._log("route_to_reviewer", {"brief_path": str(brief_path)})
        return review_brief

    def notify_telegram(self, message, priority="normal"):
        """
        Send a notification via arc-telegram.
        Used for P0 email alerts, security warnings, digest delivery.
        """
        notification = {
            "task": "send_notification",
            "channel": "beryl",
            "message": message,
            "priority": priority,
            "source": "MAILMAN",
            "timestamp": datetime.utcnow().isoformat(),
        }
        brief_path = MAILMAN_ROOT / "_incoming" / f"telegram_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        with open(brief_path, "w") as f:
            json.dump(notification, f, indent=2)
        self._log("notify_telegram", {"priority": priority})
        return notification

    def notify_slack(self, message, channel="general"):
        """Post an update to Slack via arc-slack."""
        notification = {
            "task": "post_message",
            "channel": channel,
            "message": message,
            "source": "MAILMAN",
            "timestamp": datetime.utcnow().isoformat(),
        }
        brief_path = MAILMAN_ROOT / "_incoming" / f"slack_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        with open(brief_path, "w") as f:
            json.dump(notification, f, indent=2)
        self._log("notify_slack", {"channel": channel})
        return notification

    def generate_digest(self, period="daily"):
        """Generate and optionally deliver a digest."""
        result = self.digest_engine.generate(
            gmail_client=self.gmail,
            classifier=self.classifier,
            contacts=self.contacts,
            period=period,
        )
        self._log("digest", {"period": period})
        return result

    def chat_query(self, question, account_filter=None):
        """Ask MAILMAN Chat a question about your emails."""
        result = self.chat.query(question, account_filter=account_filter)
        self._log("chat_query", {"question": question[:100]})
        return result

    # --- Phase 4 Operations ---

    def smart_reply_options(self, message_id):
        """Generate 3 smart reply options for an email."""
        email = self.gmail.get_message(message_id)
        if not email:
            print(f"Message {message_id} not found.")
            return None
        classification = self.classifier.classify_email(email, 1, 0)
        options = self.smart_reply.generate_options(email, classification)
        self._log("smart_reply", {"message_id": message_id, "options": len(options)})
        return options

    def schedule_meeting_from_email(self, message_id):
        """Detect scheduling intent and propose times for an email."""
        email = self.gmail.get_message(message_id)
        if not email:
            print(f"Message {message_id} not found.")
            return None
        intent = self.calendar.detect_scheduling_intent(email)
        if not intent or intent.get("intent") == "none":
            print("No scheduling intent detected in this email.")
            return None
        self.calendar.track_pending_scheduling(email, intent.get("suggested_times", []))
        self._log("schedule_meeting", {"message_id": message_id, "intent": intent.get("intent")})
        return intent

    def get_tasks_summary(self, filter_type="today"):
        """Get task summary: today, overdue, or all open."""
        if filter_type == "today":
            return self.tasks.get_today()
        elif filter_type == "overdue":
            return self.tasks.get_overdue()
        else:
            return self.tasks.list_tasks(status="open")

    def set_focus_mode(self, mode):
        """Set VIP Gatekeeper mode: normal, focus, or dnd."""
        self.gatekeeper.set_mode(mode)
        self._log("focus_mode", {"mode": mode})
        print(f"Focus mode set to: {mode}")

    def suggest_template(self, message_id):
        """Suggest a reply template for an email."""
        email = self.gmail.get_message(message_id)
        if not email:
            print(f"Message {message_id} not found.")
            return None
        classification = self.classifier.classify_email(email, 1, 0)
        return self.template_lib.suggest_template(email, classification)


def main():
    parser = argparse.ArgumentParser(
        description="MAILMAN Orchestrator - Central Command",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Full cycle
    p_full = subparsers.add_parser("full-cycle", help="Run complete MAILMAN cycle")
    p_full.add_argument("--account", default="gmail_personal")
    p_full.add_argument("--max-emails", type=int, default=50)

    # Triage
    p_triage = subparsers.add_parser("triage", help="Quick email triage")
    p_triage.add_argument("--account", default="gmail_personal")

    # Unsubscribe
    p_unsub = subparsers.add_parser("unsubscribe", help="Process unsubscribe queue")
    p_unsub.add_argument("--preview", action="store_true")
    p_unsub.add_argument("--execute", action="store_true")
    p_unsub.add_argument("--account", default="gmail_personal")

    # Digest
    p_digest = subparsers.add_parser("digest", help="Generate email digest")
    p_digest.add_argument("--period", choices=["daily", "weekly"], default="daily")
    p_digest.add_argument("--account", default="gmail_personal")

    # Draft reply
    p_draft = subparsers.add_parser("draft-reply", help="Draft reply to email")
    p_draft.add_argument("message_id", help="Gmail message ID")
    p_draft.add_argument("--tone", help="Tone override")
    p_draft.add_argument("--brand", help="Brand voice (routes to arc-email-crafter)")
    p_draft.add_argument("--account", default="gmail_personal")

    # Draft new
    p_new = subparsers.add_parser("draft-new", help="Draft new email from prompt")
    p_new.add_argument("prompt", help="What you want to say")
    p_new.add_argument("--brand", help="Brand voice")

    # Chat
    p_chat = subparsers.add_parser("chat", help="Ask MAILMAN a question")
    p_chat.add_argument("question", help="Your question")
    p_chat.add_argument("--account-filter", help="Restrict to account")

    # Meetings
    p_meet = subparsers.add_parser("meetings", help="Meeting intelligence")
    p_meet.add_argument("--scan", action="store_true")
    p_meet.add_argument("--actions", action="store_true")
    p_meet.add_argument("--follow-up", type=str)
    p_meet.add_argument("--account", default="gmail_personal")

    # Analytics
    p_analytics = subparsers.add_parser("analytics", help="Email analytics")
    p_analytics.add_argument("--period", type=int, default=7, help="Days to analyze")
    p_analytics.add_argument("--account", default="gmail_personal")

    # Train voice
    p_voice = subparsers.add_parser("train-voice", help="Train voice profile from sent emails")
    p_voice.add_argument("--account", default="gmail_personal")

    # Security
    p_sec = subparsers.add_parser("security-scan", help="Run security scan on inbox")
    p_sec.add_argument("--account", default="gmail_personal")

    # Smart reply (Phase 4)
    p_sr = subparsers.add_parser("smart-reply", help="Generate 3 smart reply options")
    p_sr.add_argument("message_id", help="Gmail message ID")
    p_sr.add_argument("--account", default="gmail_personal")

    # Schedule meeting (Phase 4)
    p_sched = subparsers.add_parser("schedule-meeting", help="Detect scheduling intent + propose times")
    p_sched.add_argument("message_id", help="Gmail message ID")
    p_sched.add_argument("--account", default="gmail_personal")

    # Tasks (Phase 4)
    p_tasks = subparsers.add_parser("tasks", help="Email-to-task management")
    p_tasks.add_argument("--list", action="store_true", help="List all open tasks")
    p_tasks.add_argument("--today", action="store_true", help="Tasks due today")
    p_tasks.add_argument("--overdue", action="store_true", help="Overdue tasks")
    p_tasks.add_argument("--complete", type=str, help="Complete a task by ID")

    # Rules (Phase 4)
    p_rules = subparsers.add_parser("rules", help="Automation rules engine")
    p_rules.add_argument("--list", action="store_true", help="List all rules")
    p_rules.add_argument("--stats", action="store_true", help="Rule trigger stats")
    p_rules.add_argument("--enable", type=str, help="Enable a rule by ID")
    p_rules.add_argument("--disable", type=str, help="Disable a rule by ID")

    # Focus mode (Phase 4)
    p_focus = subparsers.add_parser("focus", help="VIP Gatekeeper focus mode")
    p_focus.add_argument("--mode", choices=["normal", "focus", "dnd"], required=True)

    # Templates (Phase 4)
    p_tmpl = subparsers.add_parser("templates", help="Email template library")
    p_tmpl.add_argument("--list", action="store_true", help="List all templates")
    p_tmpl.add_argument("--suggest", type=str, help="Suggest template for message ID")
    p_tmpl.add_argument("--account", default="gmail_personal")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    orch = MailmanOrchestrator(account=getattr(args, "account", "gmail_personal"))

    if args.command == "full-cycle":
        orch.full_cycle(max_emails=args.max_emails)

    elif args.command == "triage":
        orch.triage()

    elif args.command == "digest":
        result = orch.generate_digest(period=args.period)
        if result:
            print(result)

    elif args.command == "draft-reply":
        draft = orch.draft_reply(args.message_id, tone=args.tone, brand=args.brand)
        if draft and isinstance(draft, str):
            print(f"\n--- DRAFT ---\n{draft}\n--- END ---")

    elif args.command == "draft-new":
        draft = orch.voice.draft_from_prompt(args.prompt)
        print(f"\n--- DRAFT ---\n{draft}\n--- END ---")

    elif args.command == "chat":
        result = orch.chat_query(args.question)
        print(f"\n{result['answer']}")
        if result.get("sources"):
            print(f"\nSources:")
            for s in result["sources"][:5]:
                print(f"  - {s['sender']}: {s['subject']}")

    elif args.command == "meetings":
        if args.scan:
            emails = orch.gmail.fetch_unread(max_results=50)
            detected = orch.meetings.scan_emails_for_meetings(emails)
            for m in detected:
                print(f"  [{m['meeting_type']}] {m.get('title', 'Unknown')}")
        elif args.actions:
            items = orch.meetings.get_open_actions()
            for item in items:
                print(f"  [{item['id']}] {item['task']} (Owner: {item['owner']})")
        elif args.follow_up:
            draft = orch.meetings.generate_follow_up(args.follow_up)
            print(f"\n--- FOLLOW-UP ---\n{draft}\n--- END ---")

    elif args.command == "train-voice":
        orch.voice.train(orch.gmail)

    elif args.command == "security-scan":
        emails = orch.gmail.fetch_unread(max_results=50)
        for email in emails:
            scan = orch.security.scan_email(email)
            if scan.get("risk_score", 0) >= 50:
                print(f"  RISK {scan['risk_score']}: {email.get('sender_email', '')} - {scan.get('risk_factors', [])}")

    # --- Phase 4 commands ---

    elif args.command == "smart-reply":
        options = orch.smart_reply_options(args.message_id)
        if options:
            for opt in options:
                print(f"\n--- Option {opt.get('id', '?')} ({opt.get('type', 'unknown')}) ---")
                print(f"Subject: {opt.get('subject', '')}")
                print(f"{opt.get('body', '')}")
                print("---")

    elif args.command == "schedule-meeting":
        intent = orch.schedule_meeting_from_email(args.message_id)
        if intent:
            print(f"\nIntent: {intent.get('intent')}")
            print(f"Duration: {intent.get('duration_minutes', 30)} min")
            print(f"Participants: {', '.join(intent.get('participants', []))}")
            print(f"Topic: {intent.get('topic', 'N/A')}")
            times = intent.get("suggested_times", [])
            if times:
                print(f"Suggested times:")
                for t in times:
                    print(f"  - {t}")

    elif args.command == "tasks":
        if getattr(args, "complete", None):
            orch.tasks.complete_task(args.complete)
            print(f"Task {args.complete} completed.")
        elif args.overdue:
            tasks = orch.get_tasks_summary("overdue")
            for t in tasks:
                print(f"  [{t['id']}] {t['priority']} - {t['title']} (due: {t.get('deadline', 'N/A')})")
        elif args.today:
            tasks = orch.get_tasks_summary("today")
            for t in tasks:
                print(f"  [{t['id']}] {t['priority']} - {t['title']} (due: {t.get('deadline', 'N/A')})")
        else:
            tasks = orch.get_tasks_summary("all")
            for t in tasks:
                print(f"  [{t['id']}] {t['priority']} {t['status']} - {t['title']}")

    elif args.command == "rules":
        if getattr(args, "enable", None):
            orch.rules.toggle_rule(args.enable, True)
            print(f"Rule {args.enable} enabled.")
        elif getattr(args, "disable", None):
            orch.rules.toggle_rule(args.disable, False)
            print(f"Rule {args.disable} disabled.")
        elif args.stats:
            stats = orch.rules.get_rule_stats()
            for rule_id, count in sorted(stats.items(), key=lambda x: -x[1]):
                print(f"  {rule_id}: {count} triggers")
        else:
            rules = orch.rules.get_rules()
            for r in rules:
                status = "ON" if r.get("enabled") else "OFF"
                print(f"  [{status}] {r['id']}: {r['name']}")

    elif args.command == "focus":
        orch.set_focus_mode(args.mode)

    elif args.command == "templates":
        if getattr(args, "suggest", None):
            tmpl = orch.suggest_template(args.suggest)
            if tmpl:
                print(f"\nSuggested: {tmpl.get('name', 'Unknown')}")
                print(f"Subject: {tmpl.get('subject', '')}")
                print(f"Body:\n{tmpl.get('body', '')}")
        else:
            templates = orch.template_lib.list_templates()
            for t in templates:
                print(f"  [{t['id']}] {t.get('category', '')} - {t['name']}")


if __name__ == "__main__":
    main()
