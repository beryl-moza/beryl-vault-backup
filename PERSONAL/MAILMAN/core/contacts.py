#!/usr/bin/env python3
"""
MAILMAN Contact Intelligence
Tracks communication patterns, relationship health, and contact metadata.

Usage:
  python3 contacts.py --build <account>    # Build contact database from email history
  python3 contacts.py --vip                # Show VIP contact activity
  python3 contacts.py --dormant 14         # Contacts silent for 14+ days
  python3 contacts.py --frequent           # Most frequent communicators
"""

import json
import argparse
import re
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter, defaultdict

MAILMAN_ROOT = Path(__file__).parent.parent
RULES_DIR = MAILMAN_ROOT / "rules"
MEMORY_DIR = MAILMAN_ROOT / "_memory"


class ContactIntelligence:
    """
    Builds and maintains a contact database from email patterns.
    Tracks frequency, last contact date, relationship direction, and topics.
    """

    def __init__(self):
        self.contacts_db_path = MEMORY_DIR / "contacts_db.json"
        self.vip_path = RULES_DIR / "vip_contacts.json"
        self.contacts = self._load_contacts()
        self.vips = self._load_json(self.vip_path, {"contacts": []})

    def _load_contacts(self):
        if self.contacts_db_path.exists():
            with open(self.contacts_db_path) as f:
                return json.load(f)
        return {"contacts": {}, "updated_at": None}

    def _load_json(self, path, default):
        if path.exists():
            with open(path) as f:
                return json.load(f)
        return default

    def _save_contacts(self):
        self.contacts["updated_at"] = datetime.utcnow().isoformat()
        with open(self.contacts_db_path, "w") as f:
            json.dump(self.contacts, f, indent=2)

    def update_contact(self, email_data, direction="inbound"):
        """
        Update contact record from an email interaction.

        Args:
            email_data: Parsed email dict
            direction: "inbound" (they emailed you) or "outbound" (you emailed them)
        """
        sender = email_data.get("sender_email", "").lower()
        if not sender or sender == "noreply" or "noreply" in sender:
            return

        if sender not in self.contacts["contacts"]:
            self.contacts["contacts"][sender] = {
                "email": sender,
                "name": email_data.get("sender_name", ""),
                "domain": email_data.get("sender_domain", ""),
                "first_seen": datetime.utcnow().isoformat(),
                "last_inbound": None,
                "last_outbound": None,
                "inbound_count": 0,
                "outbound_count": 0,
                "total_threads": 0,
                "subjects": [],
                "is_vip": False,
                "tags": [],
                "notes": "",
            }

        contact = self.contacts["contacts"][sender]

        # Update timestamps and counts
        now = datetime.utcnow().isoformat()
        if direction == "inbound":
            contact["last_inbound"] = now
            contact["inbound_count"] += 1
        else:
            contact["last_outbound"] = now
            contact["outbound_count"] += 1

        # Update name if we got a better one
        name = email_data.get("sender_name", "")
        if name and (not contact["name"] or len(name) > len(contact["name"])):
            contact["name"] = name

        # Track recent subjects (keep last 10)
        subject = email_data.get("subject", "")
        if subject and subject not in contact["subjects"]:
            contact["subjects"] = (contact["subjects"] + [subject])[-10:]

        # Check VIP status
        vip_emails = [c.get("email", "").lower() for c in self.vips.get("contacts", [])]
        contact["is_vip"] = sender in vip_emails

        self._save_contacts()

    def get_dormant_contacts(self, days=14, vip_only=False):
        """Find contacts who haven't communicated in N days."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        dormant = []

        for email, contact in self.contacts.get("contacts", {}).items():
            if vip_only and not contact.get("is_vip"):
                continue

            last_contact = contact.get("last_inbound") or contact.get("last_outbound")
            if last_contact:
                try:
                    last_dt = datetime.fromisoformat(last_contact)
                    if last_dt < cutoff:
                        days_silent = (datetime.utcnow() - last_dt).days
                        dormant.append({
                            "email": email,
                            "name": contact.get("name", ""),
                            "days_silent": days_silent,
                            "last_contact": last_contact,
                            "is_vip": contact.get("is_vip", False),
                        })
                except (ValueError, TypeError):
                    pass

        return sorted(dormant, key=lambda x: x["days_silent"], reverse=True)

    def get_frequent_contacts(self, top_n=20):
        """Get most frequent communicators."""
        freq = []
        for email, contact in self.contacts.get("contacts", {}).items():
            total = contact.get("inbound_count", 0) + contact.get("outbound_count", 0)
            if total > 0:
                freq.append({
                    "email": email,
                    "name": contact.get("name", ""),
                    "total": total,
                    "inbound": contact.get("inbound_count", 0),
                    "outbound": contact.get("outbound_count", 0),
                    "is_vip": contact.get("is_vip", False),
                })
        return sorted(freq, key=lambda x: x["total"], reverse=True)[:top_n]

    def get_new_contacts(self, days=7):
        """Find contacts seen for the first time in the last N days."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        new_contacts = []

        for email, contact in self.contacts.get("contacts", {}).items():
            try:
                first_seen = datetime.fromisoformat(contact.get("first_seen", ""))
                if first_seen >= cutoff:
                    new_contacts.append({
                        "email": email,
                        "name": contact.get("name", ""),
                        "first_seen": contact["first_seen"],
                        "domain": contact.get("domain", ""),
                    })
            except (ValueError, TypeError):
                pass

        return sorted(new_contacts, key=lambda x: x["first_seen"], reverse=True)

    def extract_signature_info(self, body_text):
        """
        Attempt to extract contact info from email signature.
        Looks for phone numbers, titles, company names.
        """
        info = {"phone": None, "title": None, "company": None}

        if not body_text:
            return info

        # Look in last 20 lines (likely signature area)
        lines = body_text.strip().split("\n")[-20:]
        sig_text = "\n".join(lines)

        # Phone number
        phone_match = re.search(r'[\+]?[(]?\d{1,3}[)]?[-\s.]?\d{3}[-\s.]?\d{4}', sig_text)
        if phone_match:
            info["phone"] = phone_match.group()

        return info

    def get_relationship_score(self, email_address):
        """
        Calculate relationship health score (0-100) based on communication patterns.
        """
        contact = self.contacts.get("contacts", {}).get(email_address.lower())
        if not contact:
            return 0

        score = 0

        # Bidirectional communication is healthier
        if contact.get("inbound_count", 0) > 0 and contact.get("outbound_count", 0) > 0:
            score += 30

        # Recency
        last_contact = contact.get("last_inbound") or contact.get("last_outbound")
        if last_contact:
            try:
                days_ago = (datetime.utcnow() - datetime.fromisoformat(last_contact)).days
                if days_ago <= 7:
                    score += 30
                elif days_ago <= 30:
                    score += 20
                elif days_ago <= 90:
                    score += 10
            except (ValueError, TypeError):
                pass

        # Frequency
        total = contact.get("inbound_count", 0) + contact.get("outbound_count", 0)
        if total >= 20:
            score += 20
        elif total >= 10:
            score += 15
        elif total >= 5:
            score += 10
        elif total >= 1:
            score += 5

        # VIP bonus
        if contact.get("is_vip"):
            score += 20

        return min(score, 100)


def main():
    parser = argparse.ArgumentParser(description="MAILMAN Contact Intelligence")
    parser.add_argument("--build", type=str, help="Build contact DB from account")
    parser.add_argument("--vip", action="store_true", help="Show VIP contact activity")
    parser.add_argument("--dormant", type=int, help="Show contacts dormant for N days")
    parser.add_argument("--frequent", action="store_true", help="Show most frequent contacts")
    parser.add_argument("--new", action="store_true", help="Show new contacts this week")
    args = parser.parse_args()

    ci = ContactIntelligence()

    if args.frequent:
        contacts = ci.get_frequent_contacts()
        print(f"\nTop {len(contacts)} communicators:")
        for c in contacts:
            vip = " [VIP]" if c["is_vip"] else ""
            print(f"  {c['name'] or c['email']:30s} | In:{c['inbound']:4d} Out:{c['outbound']:4d} | Total:{c['total']}{vip}")

    elif args.dormant:
        dormant = ci.get_dormant_contacts(days=args.dormant)
        print(f"\nContacts silent for {args.dormant}+ days ({len(dormant)} found):")
        for c in dormant[:20]:
            vip = " [VIP]" if c["is_vip"] else ""
            print(f"  {c['name'] or c['email']:30s} | {c['days_silent']} days silent{vip}")

    elif args.vip:
        dormant_vips = ci.get_dormant_contacts(days=7, vip_only=True)
        if dormant_vips:
            print(f"\nVIP contacts needing attention:")
            for c in dormant_vips:
                print(f"  {c['name'] or c['email']:30s} | {c['days_silent']} days since last contact")
        else:
            print("All VIP contacts are active within the last 7 days.")

    elif args.new:
        new = ci.get_new_contacts()
        print(f"\nNew contacts this week ({len(new)}):")
        for c in new:
            print(f"  {c['name'] or c['email']:30s} | {c['domain']:20s} | First seen: {c['first_seen'][:10]}")

    elif args.build:
        from gmail_client import GmailClient
        client = GmailClient(args.build)
        print(f"Building contact database from '{args.build}'...")
        emails = client.fetch_since(hours=720, max_results=500)  # Last 30 days
        for em in emails:
            ci.update_contact(em, direction="inbound")
        print(f"Processed {len(emails)} emails. Contact database updated.")


if __name__ == "__main__":
    main()
