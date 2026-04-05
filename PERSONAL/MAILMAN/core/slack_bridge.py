#!/usr/bin/env python3
"""
MAILMAN Slack Integration Bridge
Formats emails and triage data into Slack messages using Block Kit.
Produces structured output (action dicts) for MCP tool execution.

This module does NOT call Slack directly. Instead, it returns formatted
action dictionaries that the orchestrator/caller can use with MCP tools:
  - slack_send_message(channel, text)
  - slack_schedule_message(channel, text, post_at)
  - slack_create_canvas(title, content)

Usage:
  from slack_bridge import SlackBridge
  bridge = SlackBridge()

  # Generate action dict for P0 alert
  action = bridge.format_p0_alert(email_data, classification)
  # Caller then uses: slack_send_message(action['channel'], action['text'])

CLI:
  python3 slack_bridge.py --test-alert     # Sample P0 alert
  python3 slack_bridge.py --test-digest    # Sample digest
  python3 slack_bridge.py --config         # Show Slack config
"""

import json
import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import hashlib

MAILMAN_ROOT = Path(__file__).parent.parent
CONFIG_DIR = MAILMAN_ROOT / "config"
LOGS_DIR = MAILMAN_ROOT / "logs"
MEMORY_DIR = MAILMAN_ROOT / "_memory"

LOGS_DIR.mkdir(exist_ok=True)
MEMORY_DIR.mkdir(exist_ok=True)


class SlackBridge:
    """
    Formats MAILMAN email data into Slack Block Kit messages.
    Returns structured action dicts for external MCP tool execution.
    Respects quiet hours and deduplicates alerts.
    """

    # Default config if slack_config.json doesn't exist
    DEFAULT_CONFIG = {
        "channels": {
            "alerts": "#mailman-alerts",
            "digest": "#mailman-digest",
            "triage": "#mailman-triage",
            "security": "#mailman-security"
        },
        "default_channel": "#mailman",
        "mention_on_p0": True,
        "quiet_hours": {"start": "22:00", "end": "07:00"},
        "timezone": "America/Los_Angeles"
    }

    def __init__(self):
        """Initialize bridge with config and alert tracking."""
        self.config = self._load_config()
        self.alert_log = LOGS_DIR / "slack_alerts.jsonl"
        self.alert_log.touch(exist_ok=True)

    def _load_config(self) -> Dict[str, Any]:
        """Load Slack config from slack_config.json or use defaults."""
        config_file = CONFIG_DIR / "slack_config.json"
        if config_file.exists():
            try:
                with open(config_file) as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Failed to load slack_config.json: {e}", file=sys.stderr)
        return self.DEFAULT_CONFIG

    def _get_current_time(self) -> datetime:
        """Get current time (mockable for testing)."""
        return datetime.now()

    def _is_quiet_hours(self) -> bool:
        """Check if current time is within quiet hours."""
        now = self._get_current_time()
        current_time = now.time()

        quiet = self.config.get("quiet_hours", {})
        start_str = quiet.get("start", "22:00")
        end_str = quiet.get("end", "07:00")

        try:
            start = datetime.strptime(start_str, "%H:%M").time()
            end = datetime.strptime(end_str, "%H:%M").time()

            # Handle case where quiet hours cross midnight
            if start <= end:
                return start <= current_time <= end
            else:
                return current_time >= start or current_time <= end
        except ValueError:
            return False

    def _already_alerted(self, message_id: str) -> bool:
        """Check if we already sent an alert for this message."""
        try:
            with open(self.alert_log) as f:
                for line in f:
                    record = json.loads(line)
                    if record.get("message_id") == message_id:
                        return True
        except FileNotFoundError:
            pass
        return False

    def _record_alert(self, message_id: str, channel: str) -> None:
        """Log that we sent an alert for this message."""
        record = {
            "message_id": message_id,
            "channel": channel,
            "timestamp": self._get_current_time().isoformat(),
        }
        with open(self.alert_log, "a") as f:
            f.write(json.dumps(record) + "\n")

    def get_channel(self, message_type: str) -> str:
        """Get channel name for a message type (alerts, digest, triage, security)."""
        channels = self.config.get("channels", self.DEFAULT_CONFIG["channels"])
        return channels.get(message_type, self.config.get("default_channel", "#mailman"))

    # ===== SLACK BLOCK BUILDERS =====

    def _header_block(self, text: str) -> Dict[str, Any]:
        """Create a header block."""
        return {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": text,
                "emoji": True
            }
        }

    def _section_block(self, text: str, accessory: Optional[Dict] = None) -> Dict[str, Any]:
        """Create a section block with optional accessory."""
        block = {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": text
            }
        }
        if accessory:
            block["accessory"] = accessory
        return block

    def _divider_block(self) -> Dict[str, Any]:
        """Create a divider block."""
        return {"type": "divider"}

    def _context_block(self, elements: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a context block with multiple elements."""
        return {
            "type": "context",
            "elements": elements
        }

    def _actions_block(self, buttons: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create an actions block with buttons."""
        return {
            "type": "actions",
            "elements": buttons
        }

    def _mrkdwn_field(self, text: str) -> Dict[str, Any]:
        """Create a markdown text object."""
        return {
            "type": "mrkdwn",
            "text": text
        }

    # ===== MESSAGE FORMATTERS =====

    def format_p0_alert(self, email_data: Dict[str, Any], classification: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format urgent P0 alert with sender, subject, snippet, and action buttons.
        P0 alerts bypass quiet hours.
        """
        message_id = email_data.get("message_id", "unknown")

        # Check for duplicate alerts (but P0 can override)
        if self._already_alerted(message_id):
            return None

        sender = email_data.get("sender_name", email_data.get("sender_email", "Unknown"))
        subject = email_data.get("subject", "(no subject)")
        snippet = email_data.get("snippet", "")[:100]  # First 100 chars
        category = classification.get("category", "unknown")
        reason = classification.get("p0_reason", "")

        channel = self.get_channel("alerts")
        self._record_alert(message_id, channel)

        # Build blocks
        blocks = [
            self._header_block("🚨 P0 ALERT - IMMEDIATE ACTION REQUIRED"),
            self._section_block(f"*From:* {sender}"),
            self._section_block(f"*Subject:* {subject}"),
            self._section_block(f"*Category:* {category}"),
        ]

        if reason:
            blocks.append(self._section_block(f"*Reason:* {reason}"))

        if snippet:
            blocks.append(self._section_block(f"*Preview:* _{snippet}_"))

        blocks.extend([
            self._divider_block(),
            self._section_block("*Actions:* Check Slack thread or Gmail for full message"),
            self._context_block([
                self._mrkdwn_field(f"Message ID: {message_id}")
            ])
        ])

        text = f"🚨 P0 ALERT from {sender}: {subject}"
        if self.config.get("mention_on_p0"):
            text = "@channel " + text

        return {
            "action": "send_message",
            "channel": channel,
            "text": text,
            "blocks": blocks,
            "scheduled_for": None,
        }

    def format_triage_summary(self, emails_classified: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Daily triage summary: count by priority, top P0/P1 items, security alerts.
        """
        channel = self.get_channel("triage")

        # Count by priority
        p0_count = sum(1 for e in emails_classified if e.get("priority") == "P0")
        p1_count = sum(1 for e in emails_classified if e.get("priority") == "P1")
        p2_count = sum(1 for e in emails_classified if e.get("priority") == "P2")
        p3_count = sum(1 for e in emails_classified if e.get("priority") == "P3")
        p4_count = sum(1 for e in emails_classified if e.get("priority") == "P4")

        # Top P0 items
        p0_items = [e for e in emails_classified if e.get("priority") == "P0"][:5]
        p1_items = [e for e in emails_classified if e.get("priority") == "P1"][:3]

        # Security alerts
        security_items = [e for e in emails_classified if "security" in e.get("categories", [])]

        blocks = [
            self._header_block("📊 Daily Triage Summary"),
            self._divider_block(),
            self._section_block(
                f"*P0:* {p0_count} | *P1:* {p1_count} | *P2:* {p2_count} | *P3:* {p3_count} | *P4:* {p4_count}"
            ),
        ]

        if p0_items:
            blocks.append(self._section_block("*Top P0 Items:*"))
            for item in p0_items:
                sender = item.get("sender_name", item.get("sender_email", "Unknown"))
                subject = item.get("subject", "(no subject)")[:60]
                blocks.append(self._section_block(f"  • {sender}: {subject}"))

        if p1_items:
            blocks.append(self._section_block("*Top P1 Items:*"))
            for item in p1_items:
                sender = item.get("sender_name", item.get("sender_email", "Unknown"))
                subject = item.get("subject", "(no subject)")[:60]
                blocks.append(self._section_block(f"  • {sender}: {subject}"))

        if security_items:
            blocks.append(self._section_block(f"*⚠️ Security Alerts:* {len(security_items)} items"))

        blocks.extend([
            self._divider_block(),
            self._context_block([
                self._mrkdwn_field(f"Generated: {self._get_current_time().strftime('%Y-%m-%d %H:%M')}")
            ])
        ])

        text = f"📊 Triage Summary: {p0_count} P0, {p1_count} P1, {p2_count} P2"

        # Check quiet hours (but triage is usually OK)
        scheduled_for = None
        action = "send_message"
        if self._is_quiet_hours():
            # Schedule for morning
            now = self._get_current_time()
            morning = now.replace(hour=7, minute=0, second=0, microsecond=0)
            if morning <= now:
                morning += timedelta(days=1)
            scheduled_for = morning.isoformat()
            action = "schedule_message"

        return {
            "action": action,
            "channel": channel,
            "text": text,
            "blocks": blocks,
            "scheduled_for": scheduled_for,
        }

    def format_digest(self, digest_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Weekly digest as structured Slack blocks.
        """
        channel = self.get_channel("digest")

        title = digest_data.get("title", "Weekly Digest")
        period = digest_data.get("period", "")
        summary = digest_data.get("summary", {})
        highlights = digest_data.get("highlights", [])
        stats = digest_data.get("stats", {})

        blocks = [
            self._header_block(f"📬 {title}"),
        ]

        if period:
            blocks.append(self._section_block(f"Period: {period}"))

        blocks.append(self._divider_block())

        # Summary stats
        if summary:
            blocks.append(self._section_block("*Summary:*"))
            for key, value in summary.items():
                blocks.append(self._section_block(f"  • {key}: {value}"))

        # Highlights
        if highlights:
            blocks.append(self._section_block("*Highlights:*"))
            for item in highlights[:5]:
                text = item.get("text", item) if isinstance(item, dict) else item
                blocks.append(self._section_block(f"  • {text}"))

        # Stats
        if stats:
            blocks.append(self._divider_block())
            blocks.append(self._section_block("*Statistics:*"))
            for key, value in stats.items():
                blocks.append(self._section_block(f"  {key}: {value}"))

        blocks.append(self._context_block([
            self._mrkdwn_field(f"Generated: {self._get_current_time().strftime('%Y-%m-%d %H:%M')}")
        ]))

        text = f"📬 {title}"

        # Digest respects quiet hours
        scheduled_for = None
        action = "send_message"
        if self._is_quiet_hours():
            now = self._get_current_time()
            morning = now.replace(hour=8, minute=0, second=0, microsecond=0)
            if morning <= now:
                morning += timedelta(days=1)
            scheduled_for = morning.isoformat()
            action = "schedule_message"

        return {
            "action": action,
            "channel": channel,
            "text": text,
            "blocks": blocks,
            "scheduled_for": scheduled_for,
        }

    def format_security_alert(self, email_data: Dict[str, Any], scan_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Phishing/BEC warning with scan results and recommended action.
        """
        message_id = email_data.get("message_id", "unknown")

        if self._already_alerted(message_id):
            return None

        sender = email_data.get("sender_email", "Unknown")
        subject = email_data.get("subject", "(no subject)")
        threat_level = scan_result.get("threat_level", "medium")  # low, medium, high, critical
        threat_type = scan_result.get("threat_type", "unknown")  # phishing, bec, malware, etc.
        details = scan_result.get("details", "")
        recommendation = scan_result.get("recommendation", "Do not click links or open attachments")

        channel = self.get_channel("security")
        self._record_alert(message_id, channel)

        # Emoji by threat level
        emoji_map = {
            "critical": "🚨",
            "high": "⚠️",
            "medium": "⚠️",
            "low": "ℹ️"
        }
        emoji = emoji_map.get(threat_level, "⚠️")

        blocks = [
            self._header_block(f"{emoji} SECURITY ALERT - {threat_type.upper()}"),
            self._section_block(f"*Threat Level:* {threat_level.upper()}"),
            self._section_block(f"*From:* {sender}"),
            self._section_block(f"*Subject:* {subject}"),
        ]

        if details:
            blocks.append(self._section_block(f"*Details:* {details}"))

        blocks.extend([
            self._section_block(f"*Recommendation:* {recommendation}"),
            self._divider_block(),
            self._context_block([
                self._mrkdwn_field(f"Message ID: {message_id}")
            ])
        ])

        text = f"{emoji} SECURITY ALERT: {threat_type} from {sender}"

        return {
            "action": "send_message",
            "channel": channel,
            "text": text,
            "blocks": blocks,
            "scheduled_for": None,
        }

    def format_meeting_reminder(self, meeting_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Upcoming meeting with prep notes and attendees.
        """
        channel = self.get_channel("alerts")

        title = meeting_data.get("title", "Meeting")
        start_time = meeting_data.get("start_time", "")
        location = meeting_data.get("location", "")
        attendees = meeting_data.get("attendees", [])
        prep_notes = meeting_data.get("prep_notes", [])
        organizer = meeting_data.get("organizer", "")

        blocks = [
            self._header_block(f"📅 Meeting Reminder: {title}"),
            self._section_block(f"*When:* {start_time}"),
        ]

        if location:
            blocks.append(self._section_block(f"*Where:* {location}"))

        if organizer:
            blocks.append(self._section_block(f"*Organizer:* {organizer}"))

        if attendees:
            blocks.append(self._section_block(f"*Attendees:* {', '.join(attendees[:5])}"))

        if prep_notes:
            blocks.append(self._section_block("*Prep Notes:*"))
            for note in prep_notes[:5]:
                blocks.append(self._section_block(f"  • {note}"))

        blocks.append(self._context_block([
            self._mrkdwn_field(f"Set reminder in your calendar")
        ]))

        text = f"📅 {title} at {start_time}"

        return {
            "action": "send_message",
            "channel": channel,
            "text": text,
            "blocks": blocks,
            "scheduled_for": None,
        }

    def format_unsubscribe_report(self, unsub_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Report on unsubscribe batch results.
        """
        channel = self.get_channel("digest")

        total = unsub_results.get("total_attempted", 0)
        successful = unsub_results.get("successful", 0)
        failed = unsub_results.get("failed", 0)
        sources = unsub_results.get("sources", {})
        errors = unsub_results.get("errors", [])

        blocks = [
            self._header_block("📤 Unsubscribe Report"),
            self._divider_block(),
            self._section_block(f"*Total:* {total} | *Successful:* {successful} | *Failed:* {failed}"),
        ]

        if successful > 0:
            success_rate = round(100 * successful / total) if total > 0 else 0
            blocks.append(self._section_block(f"Success Rate: {success_rate}%"))

        if sources:
            blocks.append(self._section_block("*By Source:*"))
            for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True)[:5]:
                blocks.append(self._section_block(f"  • {source}: {count}"))

        if errors:
            blocks.append(self._section_block("*Recent Errors:*"))
            for error in errors[:3]:
                blocks.append(self._section_block(f"  • {error}"))

        blocks.append(self._context_block([
            self._mrkdwn_field(f"Generated: {self._get_current_time().strftime('%Y-%m-%d %H:%M')}")
        ]))

        text = f"📤 Unsubscribe Report: {successful}/{total} successful"

        return {
            "action": "send_message",
            "channel": channel,
            "text": text,
            "blocks": blocks,
            "scheduled_for": None,
        }

    # ===== CANVAS METHODS =====

    def format_digest_as_canvas(self, digest_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format digest as a Slack Canvas for detailed view.
        Returns action dict for slack_create_canvas.
        """
        title = digest_data.get("title", "MAILMAN Digest")
        period = digest_data.get("period", "")
        summary = digest_data.get("summary", {})
        highlights = digest_data.get("highlights", [])
        stats = digest_data.get("stats", {})

        # Build markdown content
        lines = [
            f"# {title}",
            ""
        ]

        if period:
            lines.append(f"**Period:** {period}")
            lines.append("")

        if summary:
            lines.append("## Summary")
            for key, value in summary.items():
                lines.append(f"- {key}: {value}")
            lines.append("")

        if highlights:
            lines.append("## Highlights")
            for item in highlights:
                text = item.get("text", item) if isinstance(item, dict) else item
                lines.append(f"- {text}")
            lines.append("")

        if stats:
            lines.append("## Statistics")
            for key, value in stats.items():
                lines.append(f"- {key}: {value}")

        content = "\n".join(lines)

        return {
            "action": "create_canvas",
            "title": title,
            "content": content,
        }


# ===== CLI =====

def main():
    """CLI for testing and configuration."""
    parser = argparse.ArgumentParser(description="MAILMAN Slack Bridge")
    parser.add_argument("--test-alert", action="store_true", help="Generate sample P0 alert")
    parser.add_argument("--test-digest", action="store_true", help="Generate sample digest")
    parser.add_argument("--config", action="store_true", help="Show current Slack config")
    parser.add_argument("--save-default-config", action="store_true", help="Save default config to file")

    args = parser.parse_args()
    bridge = SlackBridge()

    if args.config:
        print(json.dumps(bridge.config, indent=2))
        return

    if args.save_default_config:
        config_file = CONFIG_DIR / "slack_config.json"
        with open(config_file, "w") as f:
            json.dump(SlackBridge.DEFAULT_CONFIG, f, indent=2)
        print(f"Saved default config to {config_file}")
        return

    if args.test_alert:
        test_email = {
            "message_id": "test_123",
            "sender_name": "CEO",
            "sender_email": "ceo@company.com",
            "subject": "URGENT: Wire transfer needed immediately",
            "snippet": "Please wire $50,000 to this account...",
        }
        test_classification = {
            "priority": "P0",
            "category": "suspicious",
            "p0_reason": "BEC attempt - CEO impersonation",
        }
        action = bridge.format_p0_alert(test_email, test_classification)
        if action:
            print(json.dumps(action, indent=2))
        else:
            print("Alert was deduplicated (already sent)")
        return

    if args.test_digest:
        test_digest = {
            "title": "Daily Triage Summary",
            "period": "Today",
            "summary": {
                "Total emails": 47,
                "P0 items": 2,
                "P1 items": 5,
            },
            "highlights": [
                "Client meeting prep required",
                "Financial report due EOD",
                "Security patch released",
            ],
            "stats": {
                "Response needed": 3,
                "FYI only": 12,
                "Unsubscribe candidates": 8,
            }
        }
        action = bridge.format_triage_summary([])
        print(json.dumps(action, indent=2))
        return

    parser.print_help()


if __name__ == "__main__":
    main()
