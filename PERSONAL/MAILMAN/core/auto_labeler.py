#!/usr/bin/env python3
"""
MAILMAN Auto-Labeler
Automatically creates and applies Gmail labels based on classification results.
Maps MAILMAN priority tiers and categories to Gmail's label system.

Fyxer parity: "Every email automatically organized into actionable labels"
Beyond Fyxer: Priority-based labels, security labels, meeting labels,
              VIP labels, and smart auto-archive for P4 junk

Label Hierarchy:
  MAILMAN/
    Priority/
      P0-FIRE
      P1-ACTION
      P2-REVIEW
      P3-LOW
      P4-JUNK
    Category/
      Work-Internal
      Work-Client
      Personal
      Financial
      Legal
      Security
      Meeting
      Newsletter-Wanted
      Marketing-Unwanted
      Automated
    Status/
      Needs-Response
      Awaiting-Reply
      Follow-Up
      Unsubscribe-Queued
    VIP/
      (auto-created per VIP contact)

Usage:
  python3 auto_labeler.py --setup <account>     # Create label hierarchy in Gmail
  python3 auto_labeler.py --apply <account>     # Apply labels to unread emails
  python3 auto_labeler.py --clean <account>     # Archive P4 junk older than 48h
  python3 auto_labeler.py --stats               # Show label distribution
"""

import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path

MAILMAN_ROOT = Path(__file__).parent.parent
RULES_DIR = MAILMAN_ROOT / "rules"
LOGS_DIR = MAILMAN_ROOT / "logs"
LOGS_DIR.mkdir(exist_ok=True)


# Label definitions with Gmail API label properties
LABEL_TREE = {
    "MAILMAN": {
        "Priority": {
            "P0-FIRE": {"color": {"textColor": "#ffffff", "backgroundColor": "#cc3a21"}},
            "P1-ACTION": {"color": {"textColor": "#ffffff", "backgroundColor": "#fb4c2f"}},
            "P2-REVIEW": {"color": {"textColor": "#000000", "backgroundColor": "#ffad47"}},
            "P3-LOW": {"color": {"textColor": "#000000", "backgroundColor": "#b9e4d0"}},
            "P4-JUNK": {"color": {"textColor": "#666666", "backgroundColor": "#efefef"}},
        },
        "Category": {
            "Work-Internal": {"color": {"textColor": "#ffffff", "backgroundColor": "#285bac"}},
            "Work-Client": {"color": {"textColor": "#ffffff", "backgroundColor": "#0d3472"}},
            "Personal": {"color": {"textColor": "#ffffff", "backgroundColor": "#a46a21"}},
            "Financial": {"color": {"textColor": "#ffffff", "backgroundColor": "#094228"}},
            "Legal": {"color": {"textColor": "#ffffff", "backgroundColor": "#711a36"}},
            "Security": {"color": {"textColor": "#ffffff", "backgroundColor": "#cc3a21"}},
            "Meeting": {"color": {"textColor": "#ffffff", "backgroundColor": "#653e9b"}},
            "Newsletter-Wanted": {"color": {"textColor": "#000000", "backgroundColor": "#c9daf8"}},
            "Marketing-Unwanted": {"color": {"textColor": "#666666", "backgroundColor": "#efefef"}},
            "Automated": {"color": {"textColor": "#666666", "backgroundColor": "#e3d7ff"}},
        },
        "Status": {
            "Needs-Response": {"color": {"textColor": "#ffffff", "backgroundColor": "#fb4c2f"}},
            "Awaiting-Reply": {"color": {"textColor": "#000000", "backgroundColor": "#fce8b3"}},
            "Follow-Up": {"color": {"textColor": "#000000", "backgroundColor": "#b9e4d0"}},
            "Unsubscribe-Queued": {"color": {"textColor": "#666666", "backgroundColor": "#efefef"}},
        },
        "VIP": {},
    },
}

# Map MAILMAN categories to Gmail label paths
CATEGORY_TO_LABEL = {
    "thread_active": "MAILMAN/Status/Needs-Response",
    "thread_watching": "MAILMAN/Status/Awaiting-Reply",
    "meeting": "MAILMAN/Category/Meeting",
    "financial": "MAILMAN/Category/Financial",
    "legal": "MAILMAN/Category/Legal",
    "personal": "MAILMAN/Category/Personal",
    "work_internal": "MAILMAN/Category/Work-Internal",
    "work_client": "MAILMAN/Category/Work-Client",
    "newsletter_wanted": "MAILMAN/Category/Newsletter-Wanted",
    "marketing_unwanted": "MAILMAN/Category/Marketing-Unwanted",
    "automated": "MAILMAN/Category/Automated",
    "security": "MAILMAN/Category/Security",
    "suspicious": "MAILMAN/Category/Security",
}

PRIORITY_TO_LABEL = {
    "P0": "MAILMAN/Priority/P0-FIRE",
    "P1": "MAILMAN/Priority/P1-ACTION",
    "P2": "MAILMAN/Priority/P2-REVIEW",
    "P3": "MAILMAN/Priority/P3-LOW",
    "P4": "MAILMAN/Priority/P4-JUNK",
}


class AutoLabeler:
    """
    Manages Gmail label creation and application based on MAILMAN classifications.
    """

    def __init__(self):
        self.label_cache = {}  # {label_name: label_id}
        self.log_path = LOGS_DIR / "labeling_log.jsonl"

    def setup_labels(self, gmail_client):
        """
        Create the full MAILMAN label hierarchy in Gmail.
        Idempotent: skips labels that already exist.

        Args:
            gmail_client: Authenticated GmailClient instance
        """
        print("Setting up MAILMAN label hierarchy in Gmail...")
        existing = gmail_client.list_labels()
        existing_names = {l["name"]: l["id"] for l in existing}

        created = 0
        skipped = 0

        def create_tree(tree, prefix=""):
            nonlocal created, skipped
            for name, children in tree.items():
                full_name = f"{prefix}/{name}" if prefix else name
                if full_name in existing_names:
                    self.label_cache[full_name] = existing_names[full_name]
                    skipped += 1
                else:
                    color = None
                    if isinstance(children, dict) and "color" in children:
                        color = children["color"]
                        children = {}

                    label_id = gmail_client.create_label(full_name, color=color)
                    if label_id:
                        self.label_cache[full_name] = label_id
                        created += 1
                        print(f"  Created: {full_name}")
                    else:
                        print(f"  Failed: {full_name}")

                if isinstance(children, dict) and "color" not in children:
                    create_tree(children, full_name)

        create_tree(LABEL_TREE)
        print(f"\nLabel setup complete: {created} created, {skipped} already existed.")
        return created

    def apply_labels(self, classified_emails, gmail_client):
        """
        Apply Gmail labels to emails based on their MAILMAN classification.

        Args:
            classified_emails: List of email dicts with _classification attached
            gmail_client: Authenticated GmailClient instance

        Returns:
            Number of emails labeled
        """
        if not self.label_cache:
            # Build cache from existing labels
            existing = gmail_client.list_labels()
            self.label_cache = {l["name"]: l["id"] for l in existing}

        labeled = 0
        for email in classified_emails:
            cl = email.get("_classification", {})
            if not cl:
                continue

            labels_to_add = []

            # Priority label
            priority = cl.get("priority", "P3")
            priority_label = PRIORITY_TO_LABEL.get(priority)
            if priority_label and priority_label in self.label_cache:
                labels_to_add.append(self.label_cache[priority_label])

            # Category label
            category = cl.get("category", "")
            category_label = CATEGORY_TO_LABEL.get(category)
            if category_label and category_label in self.label_cache:
                labels_to_add.append(self.label_cache[category_label])

            # Status labels
            if cl.get("needs_response"):
                needs_label = "MAILMAN/Status/Needs-Response"
                if needs_label in self.label_cache:
                    labels_to_add.append(self.label_cache[needs_label])

            # VIP label
            sec = email.get("_security", {})
            if cl.get("rule_override") and "vip" in str(cl).lower():
                sender = email.get("sender_name", email.get("sender_email", ""))
                vip_label = f"MAILMAN/VIP/{sender}"
                if vip_label not in self.label_cache:
                    label_id = gmail_client.create_label(vip_label)
                    if label_id:
                        self.label_cache[vip_label] = label_id
                if vip_label in self.label_cache:
                    labels_to_add.append(self.label_cache[vip_label])

            # Apply labels
            if labels_to_add:
                message_id = email.get("id", "")
                gmail_client.apply_labels(message_id, labels_to_add)
                labeled += 1

                # Log
                self._log_labeling(email, labels_to_add)

            # Auto-archive P4 junk (remove from inbox, keep labeled)
            if priority == "P4":
                gmail_client.archive_message(email.get("id", ""))

        return labeled

    def auto_clean(self, gmail_client, days_old=2):
        """
        Clean up old P4 junk: archive anything labeled P4 older than N days.
        Does NOT delete, just removes from inbox.
        """
        p4_label = PRIORITY_TO_LABEL.get("P4")
        if not p4_label or p4_label not in self.label_cache:
            print("P4 label not found. Run --setup first.")
            return 0

        label_id = self.label_cache[p4_label]
        cutoff = datetime.utcnow() - timedelta(days=days_old)

        # Fetch P4-labeled emails
        messages = gmail_client.search(f"label:MAILMAN-Priority-P4-JUNK older_than:{days_old}d")
        archived = 0
        for msg in messages:
            gmail_client.archive_message(msg["id"])
            archived += 1

        print(f"Auto-cleaned: archived {archived} P4 emails older than {days_old} days.")
        return archived

    def _log_labeling(self, email, label_ids):
        """Log labeling actions."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "message_id": email.get("id", ""),
            "sender": email.get("sender_email", ""),
            "subject": email.get("subject", ""),
            "labels_applied": label_ids,
        }
        with open(self.log_path, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def get_label_stats(self, gmail_client):
        """Get distribution of emails across MAILMAN labels."""
        stats = {}
        existing = gmail_client.list_labels()
        for label in existing:
            if label["name"].startswith("MAILMAN/"):
                count = gmail_client.get_label_count(label["id"])
                stats[label["name"]] = count
        return stats


def main():
    parser = argparse.ArgumentParser(description="MAILMAN Auto-Labeler")
    parser.add_argument("--setup", type=str, help="Create label hierarchy for <account>")
    parser.add_argument("--apply", type=str, help="Apply labels to unread emails in <account>")
    parser.add_argument("--clean", type=str, help="Auto-archive old P4 junk in <account>")
    parser.add_argument("--stats", type=str, help="Show label distribution for <account>")
    args = parser.parse_args()

    labeler = AutoLabeler()

    if args.setup:
        from gmail_client import GmailClient
        client = GmailClient(args.setup)
        labeler.setup_labels(client)

    elif args.apply:
        from gmail_client import GmailClient
        from classifier import EmailClassifier
        client = GmailClient(args.apply)
        classifier = EmailClassifier()

        emails = client.fetch_unread(max_results=50)
        for email in emails:
            thread_count = client.get_thread_count(email.get("thread_id", ""))
            sender_freq = client.get_sender_frequency(email.get("sender_email", ""))
            cl = classifier.classify_email(email, thread_count, sender_freq)
            email["_classification"] = cl

        labeled = labeler.apply_labels(emails, client)
        print(f"Applied labels to {labeled} emails.")

    elif args.clean:
        from gmail_client import GmailClient
        client = GmailClient(args.clean)
        labeler.auto_clean(client)

    elif args.stats:
        from gmail_client import GmailClient
        client = GmailClient(args.stats)
        stats = labeler.get_label_stats(client)
        print("\nMAILMAN Label Distribution:")
        for label, count in sorted(stats.items()):
            print(f"  {label}: {count}")


if __name__ == "__main__":
    main()
