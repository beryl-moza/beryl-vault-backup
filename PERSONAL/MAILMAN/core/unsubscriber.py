#!/usr/bin/env python3
"""
MAILMAN Unsubscribe Engine
Parses List-Unsubscribe headers and executes automated unsubscribes.

Usage:
  python3 unsubscriber.py --scan                    # Scan for unsubscribe candidates
  python3 unsubscriber.py --preview                 # Show what would be unsubscribed
  python3 unsubscriber.py --execute                 # Execute pending unsubscribes
  python3 unsubscriber.py --status                  # Show unsubscribe history
"""

import json
import re
import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse

try:
    import requests
except ImportError:
    print("Missing: pip install requests --break-system-packages")
    sys.exit(1)

MAILMAN_ROOT = Path(__file__).parent.parent
LOGS_DIR = MAILMAN_ROOT / "logs"
RULES_DIR = MAILMAN_ROOT / "rules"
LOGS_DIR.mkdir(exist_ok=True)


class UnsubscribeEngine:
    """
    Multi-method unsubscribe processor.
    Parses headers, follows links, and tracks results.
    """

    def __init__(self):
        self.unsub_log_path = LOGS_DIR / "unsub_log.jsonl"
        self.pending_path = LOGS_DIR / "unsub_pending.json"
        self.vip_contacts = self._load_json(RULES_DIR / "vip_contacts.json", {"contacts": []})
        self.protected_categories = {"financial", "legal", "security", "personal"}
        self._history = self._load_history()

    def _load_json(self, path, default):
        if path.exists():
            with open(path) as f:
                return json.load(f)
        return default

    def _load_history(self):
        history = {}
        if self.unsub_log_path.exists():
            with open(self.unsub_log_path) as f:
                for line in f:
                    if line.strip():
                        entry = json.loads(line)
                        history[entry.get("sender", "")] = entry
        return history

    def parse_unsubscribe_header(self, list_unsub_header, list_unsub_post_header=""):
        """
        Parse List-Unsubscribe and List-Unsubscribe-Post headers.

        Returns dict with:
            https_url: URL for HTTP unsubscribe (preferred)
            mailto: Email address for mailto unsubscribe
            one_click: Whether RFC 8058 one-click is supported
        """
        result = {"https_url": None, "mailto": None, "one_click": False}

        if not list_unsub_header:
            return result

        # Extract URLs and mailto addresses
        parts = re.findall(r'<(.+?)>', list_unsub_header)
        for part in parts:
            if part.startswith("http://") or part.startswith("https://"):
                result["https_url"] = part
            elif part.startswith("mailto:"):
                result["mailto"] = part.replace("mailto:", "")

        # Check for one-click support
        if list_unsub_post_header and "List-Unsubscribe=One-Click" in list_unsub_post_header:
            result["one_click"] = True

        return result

    def can_unsubscribe(self, email_data, classification=None):
        """
        Check if we should attempt to unsubscribe from this sender.

        Safety checks:
        - Not a VIP contact
        - Not in a protected category
        - Has a parseable unsubscribe mechanism
        - Hasn't been recently processed
        """
        sender = email_data.get("sender_email", "").lower()

        # VIP check
        vip_emails = [c.get("email", "").lower() for c in self.vip_contacts.get("contacts", [])]
        if sender in vip_emails:
            return False, "Sender is VIP - protected"

        # Category check
        if classification and classification.get("category") in self.protected_categories:
            return False, f"Category '{classification['category']}' is protected"

        # Priority check - only P3+ gets unsubscribed
        if classification and classification.get("priority") in ("P0", "P1", "P2"):
            return False, f"Priority {classification['priority']} too high for unsubscribe"

        # Already processed recently
        if sender in self._history:
            last_attempt = self._history[sender].get("attempted_at", "")
            if last_attempt:
                try:
                    last_dt = datetime.fromisoformat(last_attempt)
                    if datetime.utcnow() - last_dt < timedelta(days=7):
                        return False, "Already processed within last 7 days"
                except ValueError:
                    pass

        # Must have unsubscribe mechanism
        unsub_info = self.parse_unsubscribe_header(
            email_data.get("list_unsubscribe", ""),
            email_data.get("list_unsubscribe_post", ""),
        )
        if not unsub_info["https_url"] and not unsub_info["mailto"]:
            return False, "No unsubscribe mechanism found in headers"

        return True, "OK"

    def execute_unsubscribe(self, email_data, dry_run=False):
        """
        Execute unsubscribe for a single email sender.

        Tries methods in order: one-click POST, HTTPS GET, mailto.
        """
        unsub_info = self.parse_unsubscribe_header(
            email_data.get("list_unsubscribe", ""),
            email_data.get("list_unsubscribe_post", ""),
        )

        result = {
            "sender": email_data.get("sender_email", ""),
            "domain": email_data.get("sender_domain", ""),
            "subject": email_data.get("subject", ""),
            "method_attempted": None,
            "method_used": None,
            "status": "pending",
            "attempted_at": datetime.utcnow().isoformat(),
            "dry_run": dry_run,
            "url": unsub_info.get("https_url", ""),
        }

        if dry_run:
            result["status"] = "preview"
            result["method_attempted"] = "dry_run"
            return result

        # Method 1: RFC 8058 One-Click POST
        if unsub_info["one_click"] and unsub_info["https_url"]:
            result["method_attempted"] = "rfc8058_oneclick"
            try:
                resp = requests.post(
                    unsub_info["https_url"],
                    data="List-Unsubscribe=One-Click",
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    timeout=15,
                    allow_redirects=True,
                )
                if resp.status_code < 400:
                    result["status"] = "success"
                    result["method_used"] = "rfc8058_oneclick"
                    result["http_status"] = resp.status_code
                    self._log_result(result)
                    return result
                else:
                    result["http_status"] = resp.status_code
            except requests.RequestException as e:
                result["error"] = str(e)

        # Method 2: HTTPS GET (follow the link)
        if unsub_info["https_url"]:
            result["method_attempted"] = "https_get"
            try:
                resp = requests.get(
                    unsub_info["https_url"],
                    timeout=15,
                    allow_redirects=True,
                    headers={"User-Agent": "MAILMAN-Unsubscribe/1.0"},
                )
                if resp.status_code < 400:
                    result["status"] = "likely_success"
                    result["method_used"] = "https_get"
                    result["http_status"] = resp.status_code
                    self._log_result(result)
                    return result
                else:
                    result["http_status"] = resp.status_code
            except requests.RequestException as e:
                result["error"] = str(e)

        # Method 3: Mailto (log for manual or SMTP send)
        if unsub_info["mailto"]:
            result["method_attempted"] = "mailto"
            result["status"] = "mailto_pending"
            result["mailto_address"] = unsub_info["mailto"]
            self._log_result(result)
            return result

        result["status"] = "failed"
        result["error"] = "All methods exhausted"
        self._log_result(result)
        return result

    def _log_result(self, result):
        """Append unsubscribe result to log."""
        with open(self.unsub_log_path, "a") as f:
            f.write(json.dumps(result) + "\n")

    def get_stats(self):
        """Return unsubscribe statistics."""
        if not self.unsub_log_path.exists():
            return {"total": 0, "success": 0, "failed": 0, "pending": 0}

        stats = {"total": 0, "success": 0, "failed": 0, "pending": 0, "preview": 0}
        with open(self.unsub_log_path) as f:
            for line in f:
                if line.strip():
                    entry = json.loads(line)
                    stats["total"] += 1
                    status = entry.get("status", "unknown")
                    if status in ("success", "likely_success"):
                        stats["success"] += 1
                    elif status == "failed":
                        stats["failed"] += 1
                    elif status == "preview":
                        stats["preview"] += 1
                    else:
                        stats["pending"] += 1
        return stats


def main():
    parser = argparse.ArgumentParser(description="MAILMAN Unsubscribe Engine")
    parser.add_argument("--scan", action="store_true", help="Scan for unsubscribe candidates")
    parser.add_argument("--preview", action="store_true", help="Preview pending unsubscribes")
    parser.add_argument("--execute", action="store_true", help="Execute pending unsubscribes")
    parser.add_argument("--status", action="store_true", help="Show unsubscribe history")
    parser.add_argument("--account", type=str, default="gmail_personal")
    args = parser.parse_args()

    engine = UnsubscribeEngine()

    if args.status:
        stats = engine.get_stats()
        print(f"\nUnsubscribe Stats:")
        print(f"  Total processed: {stats['total']}")
        print(f"  Successful: {stats['success']}")
        print(f"  Failed: {stats['failed']}")
        print(f"  Pending: {stats['pending']}")
        print(f"  Previewed: {stats['preview']}")

    elif args.scan or args.preview:
        from gmail_client import GmailClient
        from classifier import EmailClassifier

        client = GmailClient(args.account)
        classifier = EmailClassifier()

        print(f"Scanning '{args.account}' for unsubscribe candidates...")
        emails = client.fetch_since(hours=168, max_results=200)  # Last week

        candidates = []
        for em in emails:
            if em.get("list_unsubscribe"):
                can_unsub, reason = engine.can_unsubscribe(em)
                if can_unsub:
                    unsub_info = engine.parse_unsubscribe_header(
                        em["list_unsubscribe"], em.get("list_unsubscribe_post", "")
                    )
                    candidates.append({
                        "sender": em["sender_email"],
                        "domain": em["sender_domain"],
                        "subject": em["subject"],
                        "method": "one_click" if unsub_info["one_click"] else
                                  "https" if unsub_info["https_url"] else "mailto",
                    })

        print(f"\nFound {len(candidates)} unsubscribe candidates:")
        for c in candidates:
            print(f"  [{c['method']:10s}] {c['sender']:40s} - {c['subject'][:50]}")

        if args.preview:
            # Save preview for review
            with open(engine.pending_path, "w") as f:
                json.dump({"candidates": candidates, "generated_at": datetime.utcnow().isoformat()}, f, indent=2)
            print(f"\nPreview saved to {engine.pending_path}")

    elif args.execute:
        if not engine.pending_path.exists():
            print("No pending unsubscribes. Run --preview first.")
            return

        with open(engine.pending_path) as f:
            pending = json.load(f)

        print(f"Executing {len(pending['candidates'])} unsubscribes...")
        # In production, this would fetch the actual emails and execute
        print("Execute mode requires active Gmail connection. Use --preview to review candidates first.")


if __name__ == "__main__":
    main()
