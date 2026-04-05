#!/usr/bin/env python3
"""
MAILMAN Email Classifier
AI-powered email classification using Claude API + rule-based signals.

Usage:
  python3 classifier.py --triage                    # Classify new emails
  python3 classifier.py --reclassify <message_id>   # Re-classify single email
  python3 classifier.py --stats                     # Show classification stats
"""

import json
import argparse
import sys
from datetime import datetime
from pathlib import Path

try:
    import anthropic
except ImportError:
    print("Missing: pip install anthropic --break-system-packages")
    sys.exit(1)

MAILMAN_ROOT = Path(__file__).parent.parent
RULES_DIR = MAILMAN_ROOT / "rules"
LOGS_DIR = MAILMAN_ROOT / "logs"
LOGS_DIR.mkdir(exist_ok=True)


PRIORITY_TIERS = {
    "P0": "FIRE - Immediate response needed",
    "P1": "ACTION - Respond today",
    "P2": "REVIEW - Read when available",
    "P3": "LOW - Batch process weekly",
    "P4": "JUNK - Unsubscribe candidate",
}

CATEGORIES = [
    "thread_active", "thread_watching", "meeting", "financial",
    "legal", "personal", "work_internal", "work_client",
    "newsletter_wanted", "marketing_unwanted", "automated",
    "security", "suspicious",
]

CLASSIFICATION_PROMPT = """You are MAILMAN, an email classification agent. Analyze this email and return a JSON classification.

SENDER: {sender_name} <{sender_email}>
TO: {to}
CC: {cc}
SUBJECT: {subject}
DATE: {date}
SNIPPET: {snippet}
BODY (first 2000 chars): {body_preview}

THREAD CONTEXT:
- Thread message count: {thread_count}
- Has List-Unsubscribe header: {has_unsub}
- Authentication (SPF/DKIM): {auth_status}

VIP STATUS: {vip_status}
SENDER FREQUENCY (last 30 days): {sender_freq} emails

Classify this email. Return ONLY valid JSON with these fields:
{{
  "priority": "P0|P1|P2|P3|P4",
  "category": "<one of: {categories}>",
  "needs_response": true/false,
  "action_items": ["list of action items if any"],
  "urgency_keywords": ["detected urgency words"],
  "sentiment": "positive|neutral|negative|urgent",
  "summary": "1-2 sentence summary of the email",
  "reasoning": "Brief explanation of classification decision"
}}

Rules:
- VIP senders start at P1 minimum
- Emails with List-Unsubscribe from non-VIP senders with high frequency are likely P4
- Active threads where I'm in TO field and a question was asked = P1
- Financial/legal/security emails are minimum P2
- New unknown senders: default P2 unless clearly marketing (P4)
- Meeting requests: P1 if from VIP, P2 otherwise
"""


class EmailClassifier:
    """
    Multi-signal email classifier combining rules, patterns, and AI.
    """

    def __init__(self):
        self.client = anthropic.Anthropic()
        self.vip_contacts = self._load_json("vip_contacts.json", {"contacts": []})
        self.category_rules = self._load_json("categories.json", {"rules": []})
        self.urgency_keywords = self._load_json("urgency_keywords.json", {"keywords": []})
        self.triage_log = LOGS_DIR / "triage_log.jsonl"

    def _load_json(self, filename, default):
        filepath = RULES_DIR / filename
        if filepath.exists():
            with open(filepath) as f:
                return json.load(f)
        return default

    def classify_email(self, email_data, thread_count=1, sender_freq=0):
        """
        Classify a single email using multi-signal analysis.

        Args:
            email_data: Parsed email dict from GmailClient
            thread_count: Number of messages in the thread
            sender_freq: How many emails from this sender in last 30 days

        Returns:
            Classification dict with priority, category, actions
        """
        # Step 1: Rule-based pre-classification
        pre_class = self._rule_based_classify(email_data, sender_freq)

        # Step 2: AI classification for nuanced analysis
        ai_class = self._ai_classify(email_data, thread_count, sender_freq)

        # Step 3: Merge signals (rules override AI for certain conditions)
        final = self._merge_classifications(pre_class, ai_class, email_data)

        # Step 4: Log the classification
        self._log_classification(email_data, final)

        return final

    def _rule_based_classify(self, email_data, sender_freq):
        """Fast rule-based classification using local signals."""
        signals = {
            "is_vip": self._is_vip(email_data["sender_email"]),
            "has_unsub": bool(email_data.get("list_unsubscribe", "")),
            "is_in_to": self._am_i_in_to(email_data),
            "high_freq_sender": sender_freq > 10,
            "has_urgency": self._detect_urgency(email_data),
            "is_security": self._is_security_email(email_data),
            "is_financial": self._is_financial_email(email_data),
        }

        # Direct rule matches
        if signals["is_security"]:
            return {"priority": "P2", "category": "security", "confidence": 0.9}
        if signals["is_financial"]:
            return {"priority": "P2", "category": "financial", "confidence": 0.85}
        if signals["has_unsub"] and signals["high_freq_sender"] and not signals["is_vip"]:
            return {"priority": "P4", "category": "marketing_unwanted", "confidence": 0.8}
        if signals["is_vip"] and signals["is_in_to"]:
            return {"priority": "P1", "category": "work_client", "confidence": 0.75}

        return {"priority": None, "category": None, "confidence": 0}

    def _ai_classify(self, email_data, thread_count, sender_freq):
        """Use Claude API for nuanced email classification."""
        body_preview = (email_data.get("body_text", "") or email_data.get("snippet", ""))[:2000]

        prompt = CLASSIFICATION_PROMPT.format(
            sender_name=email_data.get("sender_name", ""),
            sender_email=email_data.get("sender_email", ""),
            to=email_data.get("to", ""),
            cc=email_data.get("cc", ""),
            subject=email_data.get("subject", ""),
            date=email_data.get("date", ""),
            snippet=email_data.get("snippet", ""),
            body_preview=body_preview,
            thread_count=thread_count,
            has_unsub=bool(email_data.get("list_unsubscribe", "")),
            auth_status=email_data.get("authentication_results", "unknown")[:200],
            vip_status="VIP" if self._is_vip(email_data["sender_email"]) else "Not VIP",
            sender_freq=sender_freq,
            categories=", ".join(CATEGORIES),
        )

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-5-20250514",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}],
            )
            result_text = response.content[0].text.strip()

            # Parse JSON from response (handle markdown code blocks)
            if result_text.startswith("```"):
                result_text = result_text.split("\n", 1)[1].rsplit("```", 1)[0]

            return json.loads(result_text)
        except Exception as e:
            print(f"AI classification error: {e}")
            return {"priority": "P2", "category": "automated", "needs_response": False,
                    "action_items": [], "urgency_keywords": [], "sentiment": "neutral",
                    "summary": "Classification failed, defaulting to P2",
                    "reasoning": f"Error: {str(e)}"}

    def _merge_classifications(self, rule_class, ai_class, email_data):
        """Merge rule-based and AI classifications. Rules win on high-confidence matches."""
        final = dict(ai_class)

        # Rule-based overrides when confidence is high
        if rule_class["confidence"] >= 0.8:
            final["priority"] = rule_class["priority"]
            final["category"] = rule_class["category"]
            final["rule_override"] = True
        elif rule_class["confidence"] >= 0.5 and rule_class["priority"]:
            # Use rule priority if it's more urgent than AI's
            priority_order = ["P0", "P1", "P2", "P3", "P4"]
            rule_idx = priority_order.index(rule_class["priority"])
            ai_idx = priority_order.index(final.get("priority", "P3"))
            if rule_idx < ai_idx:
                final["priority"] = rule_class["priority"]

        # Always add metadata
        final["message_id"] = email_data["id"]
        final["account"] = email_data.get("account", "")
        final["sender_email"] = email_data.get("sender_email", "")
        final["subject"] = email_data.get("subject", "")
        final["classified_at"] = datetime.utcnow().isoformat()

        return final

    def _is_vip(self, sender_email):
        """Check if sender is in VIP contacts list."""
        vip_emails = [c.get("email", "").lower() for c in self.vip_contacts.get("contacts", [])]
        return sender_email.lower() in vip_emails

    def _am_i_in_to(self, email_data):
        """Check if the user is in the TO field (not just CC)."""
        to_field = email_data.get("to", "").lower()
        # Check against all configured account emails
        # For now, basic check
        return bool(to_field)

    def _detect_urgency(self, email_data):
        """Check for urgency keywords in subject and snippet."""
        text = f"{email_data.get('subject', '')} {email_data.get('snippet', '')}".lower()
        keywords = self.urgency_keywords.get("keywords", [
            "urgent", "asap", "immediately", "deadline", "eod", "end of day",
            "time sensitive", "critical", "emergency", "by tomorrow", "by friday",
            "by monday", "overdue", "past due", "final notice",
        ])
        return any(kw.lower() in text for kw in keywords)

    def _is_security_email(self, email_data):
        """Check if email is security-related."""
        text = f"{email_data.get('subject', '')} {email_data.get('snippet', '')}".lower()
        patterns = ["password reset", "2fa", "two-factor", "login alert", "sign-in",
                     "security alert", "verify your", "suspicious activity", "account locked"]
        return any(p in text for p in patterns)

    def _is_financial_email(self, email_data):
        """Check if email is financial."""
        text = f"{email_data.get('subject', '')} {email_data.get('snippet', '')}".lower()
        patterns = ["invoice", "receipt", "payment", "bank", "wire transfer",
                     "statement", "billing", "subscription renewed", "charge"]
        return any(p in text for p in patterns)

    def _log_classification(self, email_data, classification):
        """Append classification to triage log."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "message_id": email_data["id"],
            "sender": email_data.get("sender_email", ""),
            "subject": email_data.get("subject", ""),
            "priority": classification.get("priority"),
            "category": classification.get("category"),
            "needs_response": classification.get("needs_response"),
        }
        with open(self.triage_log, "a") as f:
            f.write(json.dumps(log_entry) + "\n")


def main():
    parser = argparse.ArgumentParser(description="MAILMAN Email Classifier")
    parser.add_argument("--triage", action="store_true", help="Run triage on unread emails")
    parser.add_argument("--reclassify", type=str, help="Re-classify a specific message ID")
    parser.add_argument("--stats", action="store_true", help="Show classification statistics")
    parser.add_argument("--account", type=str, default="gmail_personal", help="Account to triage")
    args = parser.parse_args()

    classifier = EmailClassifier()

    if args.stats:
        if LOGS_DIR.joinpath("triage_log.jsonl").exists():
            with open(LOGS_DIR / "triage_log.jsonl") as f:
                entries = [json.loads(line) for line in f if line.strip()]
            print(f"\nTotal classified: {len(entries)}")
            priorities = {}
            for e in entries:
                p = e.get("priority", "unknown")
                priorities[p] = priorities.get(p, 0) + 1
            for p in sorted(priorities.keys()):
                print(f"  {p}: {priorities[p]}")
        else:
            print("No triage log found. Run --triage first.")

    elif args.triage:
        from gmail_client import GmailClient
        client = GmailClient(args.account)
        print(f"Fetching unread emails from '{args.account}'...")
        emails = client.fetch_unread(max_results=50)
        print(f"Found {len(emails)} unread emails. Classifying...")

        results = {"P0": [], "P1": [], "P2": [], "P3": [], "P4": []}
        for em in emails:
            thread_count = client.get_thread_count(em["thread_id"])
            sender_freq = client.get_sender_frequency(em["sender_email"])
            classification = classifier.classify_email(em, thread_count, sender_freq)
            priority = classification.get("priority", "P3")
            results[priority].append(classification)
            print(f"  [{priority}] {em['sender_email']}: {em['subject'][:60]}")

        print(f"\nTriage complete:")
        for p in ["P0", "P1", "P2", "P3", "P4"]:
            print(f"  {p}: {len(results[p])} emails")


if __name__ == "__main__":
    main()
