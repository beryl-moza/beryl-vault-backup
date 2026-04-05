#!/usr/bin/env python3
"""
MAILMAN Digest Generator
Creates daily and weekly email summaries from triage data.

Usage:
  python3 digest.py --today          # Generate today's digest
  python3 digest.py --weekly         # Generate weekly summary
  python3 digest.py --custom 48      # Digest for last 48 hours
"""

import json
import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter

try:
    import anthropic
except ImportError:
    print("Missing: pip install anthropic --break-system-packages")
    sys.exit(1)

MAILMAN_ROOT = Path(__file__).parent.parent
LOGS_DIR = MAILMAN_ROOT / "logs"
MEMORY_DIR = MAILMAN_ROOT / "_memory"
TEMPLATES_DIR = MAILMAN_ROOT / "templates"


class DigestGenerator:
    """
    Generates structured email digests from triage and unsub logs.
    """

    def __init__(self):
        self.client = anthropic.Anthropic()
        self.triage_log = LOGS_DIR / "triage_log.jsonl"
        self.unsub_log = LOGS_DIR / "unsub_log.jsonl"
        self.digests_dir = MEMORY_DIR / "digests"
        self.digests_dir.mkdir(parents=True, exist_ok=True)

    def _load_log_entries(self, log_path, since_hours=24):
        """Load log entries from the last N hours."""
        entries = []
        if not log_path.exists():
            return entries

        cutoff = datetime.utcnow() - timedelta(hours=since_hours)
        with open(log_path) as f:
            for line in f:
                if line.strip():
                    entry = json.loads(line)
                    try:
                        ts = datetime.fromisoformat(entry.get("timestamp", entry.get("attempted_at", "")))
                        if ts >= cutoff:
                            entries.append(entry)
                    except (ValueError, TypeError):
                        entries.append(entry)
        return entries

    def generate_daily_digest(self):
        """Generate a daily email digest."""
        return self._generate_digest(hours=24, period="daily")

    def generate_weekly_digest(self):
        """Generate a weekly email digest."""
        return self._generate_digest(hours=168, period="weekly")

    def _generate_digest(self, hours=24, period="daily"):
        """Core digest generation logic."""
        triage_entries = self._load_log_entries(self.triage_log, hours)
        unsub_entries = self._load_log_entries(self.unsub_log, hours)

        # Build stats
        total = len(triage_entries)
        priority_counts = Counter(e.get("priority", "unknown") for e in triage_entries)
        category_counts = Counter(e.get("category", "unknown") for e in triage_entries)
        needs_response = [e for e in triage_entries if e.get("needs_response")]
        top_senders = Counter(e.get("sender", "") for e in triage_entries).most_common(10)

        # Unsub stats
        unsub_success = len([e for e in unsub_entries if e.get("status") in ("success", "likely_success")])
        unsub_pending = len([e for e in unsub_entries if e.get("status") == "preview"])

        # Build digest content
        digest = []
        digest.append(f"# MAILMAN {period.title()} Digest")
        digest.append(f"**{datetime.utcnow().strftime('%A, %B %d, %Y')}**")
        digest.append(f"Period: Last {hours} hours | Total emails processed: {total}")
        digest.append("")

        # Section 1: Action Required
        p0_emails = [e for e in triage_entries if e.get("priority") == "P0"]
        p1_emails = [e for e in triage_entries if e.get("priority") == "P1"]

        if p0_emails or p1_emails:
            digest.append("## ACTION REQUIRED")
            digest.append("")
            if p0_emails:
                digest.append(f"**FIRE ({len(p0_emails)})** - Needs immediate attention:")
                for e in p0_emails:
                    digest.append(f"- {e.get('sender', 'Unknown')}: {e.get('subject', 'No subject')}")
                digest.append("")
            if p1_emails:
                digest.append(f"**ACTION ({len(p1_emails)})** - Respond today:")
                for e in p1_emails:
                    digest.append(f"- {e.get('sender', 'Unknown')}: {e.get('subject', 'No subject')}")
                digest.append("")

            if needs_response:
                digest.append(f"**Threads awaiting your reply: {len(needs_response)}**")
                digest.append("")

        # Section 2: Inbox Summary
        digest.append("## INBOX SUMMARY")
        digest.append("")
        digest.append(f"| Priority | Count |")
        digest.append(f"|----------|-------|")
        for p in ["P0", "P1", "P2", "P3", "P4"]:
            count = priority_counts.get(p, 0)
            if count > 0:
                digest.append(f"| {p} | {count} |")
        digest.append("")

        if category_counts:
            digest.append("**By category:**")
            for cat, count in category_counts.most_common(8):
                digest.append(f"- {cat}: {count}")
            digest.append("")

        # Section 3: Top Senders
        if top_senders:
            digest.append("## TOP SENDERS")
            digest.append("")
            for sender, count in top_senders:
                digest.append(f"- {sender}: {count} emails")
            digest.append("")

        # Section 4: Unsubscribe Report
        if unsub_entries:
            digest.append("## UNSUBSCRIBE REPORT")
            digest.append("")
            digest.append(f"- Successfully unsubscribed: {unsub_success}")
            digest.append(f"- Pending review: {unsub_pending}")
            digest.append(f"- Total processed: {len(unsub_entries)}")
            digest.append("")

        digest_text = "\n".join(digest)

        # Save digest
        filename = f"digest-{period}-{datetime.utcnow().strftime('%Y-%m-%d')}.md"
        digest_path = self.digests_dir / filename
        with open(digest_path, "w") as f:
            f.write(digest_text)

        print(f"Digest saved: {digest_path}")
        return digest_text

    def generate_ai_summary(self, digest_text):
        """
        Use Claude to create a concise, conversational summary of the digest.
        Follows Antidote writing style - no em dashes, active voice, direct.
        """
        prompt = f"""Summarize this email digest into a brief, conversational paragraph (3-5 sentences).
Write in active voice, direct style. No em dashes, no corporate speak.
Focus on: what needs attention now, what can wait, and any wins (successful unsubscribes).

DIGEST:
{digest_text}

Write the summary as if you're briefing Beryl at the start of the day. Keep it human."""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-5-20250514",
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text.strip()
        except Exception as e:
            return f"(AI summary unavailable: {e})"


def main():
    parser = argparse.ArgumentParser(description="MAILMAN Digest Generator")
    parser.add_argument("--today", action="store_true", help="Generate daily digest")
    parser.add_argument("--weekly", action="store_true", help="Generate weekly digest")
    parser.add_argument("--custom", type=int, help="Digest for last N hours")
    args = parser.parse_args()

    gen = DigestGenerator()

    if args.weekly:
        digest = gen.generate_weekly_digest()
    elif args.custom:
        digest = gen._generate_digest(hours=args.custom, period="custom")
    else:
        digest = gen.generate_daily_digest()

    print("\n" + digest)

    summary = gen.generate_ai_summary(digest)
    print(f"\nTL;DR: {summary}")


if __name__ == "__main__":
    main()
