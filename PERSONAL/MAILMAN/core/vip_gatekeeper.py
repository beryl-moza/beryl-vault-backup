#!/usr/bin/env python3
"""
MAILMAN VIP Gatekeeper
Focus mode filtering for VIP contacts and priority emails only.

Usage:
  python3 vip_gatekeeper.py --mode <normal|focus|dnd>  # Set gatekeeper mode
  python3 vip_gatekeeper.py --filter                    # Filter inbox
  python3 vip_gatekeeper.py --add-vip <email>           # Add VIP contact
  python3 vip_gatekeeper.py --remove-vip <email>        # Remove VIP contact
  python3 vip_gatekeeper.py --list-vips                 # Show all VIPs
"""

import json
import argparse
import sys
from datetime import datetime
from pathlib import Path

MAILMAN_ROOT = Path(__file__).parent.parent
RULES_DIR = MAILMAN_ROOT / "rules"
CONFIG_DIR = MAILMAN_ROOT / "config"
LOGS_DIR = MAILMAN_ROOT / "logs"
LOGS_DIR.mkdir(exist_ok=True)
CONFIG_DIR.mkdir(exist_ok=True)


DEFAULT_CONFIG = {
    "mode": "normal",
    "surface_priorities": ["P0", "P1"],
    "surface_categories": ["security", "financial", "legal"],
    "always_surface_threads": True,
    "defer_digest_interval_hours": 4,
    "auto_focus_hours": {"start": "09:00", "end": "12:00"},
}


class VIPGatekeeper:
    """
    Filters inbox to show only important emails (VIPs and P0/P1).
    Supports normal, focus (VIP+P0/P1 only), and DND (P0 only) modes.
    """

    def __init__(self):
        self.vip_contacts = self._load_json("vip_contacts.json", {"contacts": []})
        self.config = self._load_config()
        self.gatekeeper_log = LOGS_DIR / "gatekeeper_log.jsonl"

    def _load_json(self, filename, default):
        """Load JSON file from rules directory."""
        filepath = RULES_DIR / filename
        if filepath.exists():
            try:
                with open(filepath) as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return default
        return default

    def _load_config(self):
        """Load gatekeeper configuration."""
        config_file = CONFIG_DIR / "gatekeeper_config.json"
        if config_file.exists():
            try:
                with open(config_file) as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return DEFAULT_CONFIG.copy()
        return DEFAULT_CONFIG.copy()

    def _save_config(self):
        """Save gatekeeper configuration to disk."""
        config_file = CONFIG_DIR / "gatekeeper_config.json"
        with open(config_file, "w") as f:
            json.dump(self.config, f, indent=2)

    def _save_vips(self):
        """Save VIP contacts to disk."""
        vip_file = RULES_DIR / "vip_contacts.json"
        with open(vip_file, "w") as f:
            json.dump(self.vip_contacts, f, indent=2)

    def filter_inbox(self, emails, classifications):
        """
        Filter inbox into surfaced and deferred lists based on current mode.

        Args:
            emails: List of email dicts from GmailClient
            classifications: List of classification dicts from EmailClassifier

        Returns:
            Tuple of (surfaced_emails, deferred_emails)
        """
        surfaced = []
        deferred = []

        for email in emails:
            # Find corresponding classification
            classification = next(
                (c for c in classifications if c.get("message_id") == email.get("id")),
                {"priority": "P3", "category": "unknown"},
            )

            if self.is_surfaced(email, classification):
                surfaced.append(email)
            else:
                deferred.append(email)

        self._log_filtering(len(emails), len(surfaced), len(deferred))
        return surfaced, deferred

    def is_surfaced(self, email_data, classification):
        """
        Determine if email should surface in current gatekeeper mode.

        Args:
            email_data: Email dict
            classification: Classification dict

        Returns:
            True if email should be shown, False if deferred
        """
        mode = self.config.get("mode", "normal")
        sender_email = email_data.get("sender_email", "").lower()
        priority = classification.get("priority", "P3")
        category = classification.get("category", "")

        # Check if sender is VIP
        is_vip = self._is_vip(sender_email)

        # Check if it's an active thread (and we're in TO field)
        is_active_thread = (
            self.config.get("always_surface_threads", True)
            and self._is_in_to(email_data)
            and email_data.get("thread_count", 1) > 1
        )

        # Rule: Always surface P0 (emergency)
        if priority == "P0":
            return True

        # Rule: Always surface security/financial/legal
        if category in self.config.get("surface_categories", ["security", "financial", "legal"]):
            return True

        # Apply mode-specific rules
        if mode == "normal":
            # Everything surfaces in normal mode
            return True

        elif mode == "focus":
            # Only VIP, P1, and important categories
            if is_vip or priority == "P1" or is_active_thread:
                return True
            return False

        elif mode == "dnd":
            # Only P0 (emergencies)
            return priority == "P0"

        return False

    def _is_vip(self, sender_email):
        """Check if sender is VIP."""
        vip_emails = [
            c.get("email", "").lower()
            for c in self.vip_contacts.get("contacts", [])
        ]
        return sender_email.lower() in vip_emails

    def _is_in_to(self, email_data):
        """Check if user is in TO field (not just CC)."""
        to_field = email_data.get("to", "").lower()
        # Basic check - assumes TO field contains email(s)
        return bool(to_field)

    def get_deferred_digest(self, deferred_emails, classifications):
        """
        Format deferred emails into a batch digest.

        Args:
            deferred_emails: List of deferred email dicts
            classifications: List of classification dicts

        Returns:
            Formatted digest string
        """
        if not deferred_emails:
            return "No deferred emails."

        lines = [f"DEFERRED EMAIL DIGEST ({len(deferred_emails)} emails)\n" + "=" * 60]

        # Group by priority
        for priority in ["P3", "P2", "P1"]:  # Already filtered out P0
            matching = []
            for email in deferred_emails:
                classification = next(
                    (c for c in classifications if c.get("message_id") == email.get("id")),
                    {"priority": "P3"},
                )
                if classification.get("priority") == priority:
                    matching.append((email, classification))

            if matching:
                lines.append(f"\n{priority}:")
                for email, classification in matching:
                    sender = email.get("sender_name", email.get("sender_email", "Unknown"))
                    subject = email.get("subject", "[No subject]")[:50]
                    summary = classification.get("summary", "")[:60]
                    lines.append(f"  • {sender}: {subject}")
                    if summary:
                        lines.append(f"    → {summary}")

        return "\n".join(lines)

    def set_mode(self, mode):
        """
        Set gatekeeper mode: normal, focus, or dnd.

        Args:
            mode: "normal", "focus", or "dnd"

        Returns:
            Updated config dict
        """
        if mode not in ["normal", "focus", "dnd"]:
            raise ValueError(f"Invalid mode: {mode}. Use 'normal', 'focus', or 'dnd'")

        self.config["mode"] = mode
        self._save_config()
        self._log_mode_change(mode)

        return self.config

    def add_vip(self, email, name=None, priority="high"):
        """
        Add email to VIP contacts list.

        Args:
            email: Email address
            name: Full name (optional)
            priority: "high" or "medium"

        Returns:
            Updated VIP contacts
        """
        email = email.lower()

        # Check if already in list
        for contact in self.vip_contacts.get("contacts", []):
            if contact.get("email", "").lower() == email:
                return self.vip_contacts

        contact = {
            "email": email,
            "name": name or email,
            "priority": priority,
            "added_at": datetime.utcnow().isoformat(),
        }

        if "contacts" not in self.vip_contacts:
            self.vip_contacts["contacts"] = []

        self.vip_contacts["contacts"].append(contact)
        self._save_vips()
        self._log_vip_change("added", email)

        return self.vip_contacts

    def remove_vip(self, email):
        """
        Remove email from VIP contacts list.

        Args:
            email: Email address to remove

        Returns:
            Updated VIP contacts
        """
        email = email.lower()
        original_count = len(self.vip_contacts.get("contacts", []))

        self.vip_contacts["contacts"] = [
            c for c in self.vip_contacts.get("contacts", [])
            if c.get("email", "").lower() != email
        ]

        if len(self.vip_contacts["contacts"]) < original_count:
            self._save_vips()
            self._log_vip_change("removed", email)

        return self.vip_contacts

    def list_vips(self):
        """
        Get list of all VIP contacts.

        Returns:
            List of VIP contact dicts
        """
        return self.vip_contacts.get("contacts", [])

    def _log_filtering(self, total, surfaced, deferred):
        """Log filtering operation."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "mode": self.config.get("mode", "normal"),
            "total_emails": total,
            "surfaced": surfaced,
            "deferred": deferred,
        }
        with open(self.gatekeeper_log, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

    def _log_mode_change(self, new_mode):
        """Log mode change."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": "mode_changed",
            "new_mode": new_mode,
        }
        with open(self.gatekeeper_log, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

    def _log_vip_change(self, action, email):
        """Log VIP contact change."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "email": email,
        }
        with open(self.gatekeeper_log, "a") as f:
            f.write(json.dumps(log_entry) + "\n")


def main():
    parser = argparse.ArgumentParser(description="MAILMAN VIP Gatekeeper")
    parser.add_argument(
        "--mode",
        type=str,
        choices=["normal", "focus", "dnd"],
        help="Set gatekeeper mode",
    )
    parser.add_argument("--filter", action="store_true", help="Show filtering status")
    parser.add_argument("--add-vip", type=str, help="Add email to VIP list")
    parser.add_argument("--remove-vip", type=str, help="Remove email from VIP list")
    parser.add_argument("--list-vips", action="store_true", help="Show all VIP contacts")
    args = parser.parse_args()

    gatekeeper = VIPGatekeeper()

    if args.mode:
        gatekeeper.set_mode(args.mode)
        print(f"✓ Gatekeeper mode set to: {args.mode}")

    elif args.filter:
        current_mode = gatekeeper.config.get("mode", "normal")
        vip_count = len(gatekeeper.list_vips())
        print(f"Gatekeeper Status:")
        print(f"  Mode: {current_mode}")
        print(f"  VIPs in list: {vip_count}")
        print(f"  Surface priorities: {', '.join(gatekeeper.config.get('surface_priorities', []))}")
        print(f"  Surface categories: {', '.join(gatekeeper.config.get('surface_categories', []))}")

    elif args.add_vip:
        gatekeeper.add_vip(args.add_vip)
        print(f"✓ Added to VIP list: {args.add_vip}")

    elif args.remove_vip:
        gatekeeper.remove_vip(args.remove_vip)
        print(f"✓ Removed from VIP list: {args.remove_vip}")

    elif args.list_vips:
        vips = gatekeeper.list_vips()
        if not vips:
            print("No VIP contacts configured.")
        else:
            print(f"VIP CONTACTS ({len(vips)}):\n")
            for vip in vips:
                print(f"  {vip['email']}")
                print(f"    Name: {vip.get('name', 'N/A')}")
                print(f"    Priority: {vip.get('priority', 'N/A')}\n")

    else:
        print("Use --help for options")


if __name__ == "__main__":
    main()
