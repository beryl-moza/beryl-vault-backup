#!/usr/bin/env python3
"""
MAILMAN Security Module
Detects phishing, BEC attempts, suspicious senders, and email spoofing.

Usage:
  python3 security.py --scan <account>   # Scan recent emails for threats
  python3 security.py --check <msg_id>   # Check specific message
  python3 security.py --report           # Show security alerts
"""

import json
import re
import argparse
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

MAILMAN_ROOT = Path(__file__).parent.parent
LOGS_DIR = MAILMAN_ROOT / "logs"
RULES_DIR = MAILMAN_ROOT / "rules"
LOGS_DIR.mkdir(exist_ok=True)


# Known suspicious TLD patterns
SUSPICIOUS_TLDS = {
    ".xyz", ".top", ".click", ".link", ".info", ".gq", ".ml", ".cf", ".tk", ".ga",
    ".buzz", ".club", ".work", ".monster", ".cam", ".rest", ".icu",
}

# Common phishing patterns in subjects
PHISHING_SUBJECT_PATTERNS = [
    r"(?i)your account (has been|will be|is) (suspended|locked|deactivated)",
    r"(?i)verify your (account|identity|email|payment)",
    r"(?i)unusual (sign-in|activity|login)",
    r"(?i)(confirm|update) your (payment|billing|information)",
    r"(?i)you have (\d+) unread (message|notification)",
    r"(?i)(invoice|payment|receipt) #?\d+",
    r"(?i)action required.*account",
    r"(?i)congratulations.*(won|winner|selected|prize)",
    r"(?i)(bitcoin|crypto|investment).*(opportunity|profit|guarantee)",
]

# BEC (Business Email Compromise) patterns
BEC_PATTERNS = [
    r"(?i)(wire transfer|bank transfer|urgent payment)",
    r"(?i)please (process|send|transfer|wire).*(\$|USD|payment)",
    r"(?i)(gift cards?|itunes|amazon card)",
    r"(?i)keep this (confidential|private|between us)",
    r"(?i)don't (tell|inform|mention).*(anyone|others)",
    r"(?i)I('m| am) (in a meeting|traveling|unavailable).*need.*favor",
]


class SecurityScanner:
    """
    Multi-signal email security analyzer.
    Checks authentication, content patterns, sender reputation, and link safety.
    """

    def __init__(self):
        self.security_log = LOGS_DIR / "security_log.jsonl"
        self.known_senders_path = RULES_DIR / "vip_contacts.json"

    def scan_email(self, email_data):
        """
        Run full security scan on an email.

        Returns:
            dict with threat_level (safe/suspicious/dangerous), findings list, and score
        """
        findings = []
        score = 0  # Higher = more suspicious (0-100)

        # Check 1: Authentication (SPF/DKIM/DMARC)
        auth_result = self._check_authentication(email_data)
        findings.extend(auth_result["findings"])
        score += auth_result["score"]

        # Check 2: Sender analysis
        sender_result = self._check_sender(email_data)
        findings.extend(sender_result["findings"])
        score += sender_result["score"]

        # Check 3: Subject line patterns
        subject_result = self._check_subject_patterns(email_data)
        findings.extend(subject_result["findings"])
        score += subject_result["score"]

        # Check 4: BEC detection
        bec_result = self._check_bec_patterns(email_data)
        findings.extend(bec_result["findings"])
        score += bec_result["score"]

        # Check 5: Link analysis
        link_result = self._check_links(email_data)
        findings.extend(link_result["findings"])
        score += link_result["score"]

        # Check 6: Reply-to mismatch
        reply_result = self._check_reply_to(email_data)
        findings.extend(reply_result["findings"])
        score += reply_result["score"]

        # Determine threat level
        if score >= 60:
            threat_level = "dangerous"
        elif score >= 30:
            threat_level = "suspicious"
        else:
            threat_level = "safe"

        result = {
            "message_id": email_data.get("id", ""),
            "sender": email_data.get("sender_email", ""),
            "subject": email_data.get("subject", ""),
            "threat_level": threat_level,
            "score": min(score, 100),
            "findings": findings,
            "scanned_at": datetime.utcnow().isoformat(),
        }

        # Log if suspicious or dangerous
        if threat_level != "safe":
            self._log_alert(result)

        return result

    def _check_authentication(self, email_data):
        """Check SPF, DKIM, and DMARC authentication results."""
        auth_header = email_data.get("authentication_results", "").lower()
        findings = []
        score = 0

        if not auth_header:
            findings.append("No authentication results header found")
            score += 10
            return {"findings": findings, "score": score}

        # SPF check
        if "spf=fail" in auth_header or "spf=softfail" in auth_header:
            findings.append("SPF authentication FAILED - sender may be spoofed")
            score += 25
        elif "spf=none" in auth_header:
            findings.append("No SPF record for sender domain")
            score += 10

        # DKIM check
        if "dkim=fail" in auth_header:
            findings.append("DKIM signature FAILED - email may be tampered")
            score += 25
        elif "dkim=none" in auth_header:
            findings.append("No DKIM signature present")
            score += 5

        # DMARC check
        if "dmarc=fail" in auth_header:
            findings.append("DMARC policy FAILED - high spoofing risk")
            score += 30

        return {"findings": findings, "score": score}

    def _check_sender(self, email_data):
        """Analyze sender email and domain for red flags."""
        findings = []
        score = 0
        sender = email_data.get("sender_email", "").lower()
        domain = email_data.get("sender_domain", "").lower()

        if not sender:
            findings.append("No sender email detected")
            score += 15
            return {"findings": findings, "score": score}

        # Suspicious TLD
        for tld in SUSPICIOUS_TLDS:
            if domain.endswith(tld):
                findings.append(f"Suspicious TLD: {tld}")
                score += 15
                break

        # Lookalike domain detection (basic)
        common_domains = ["gmail.com", "google.com", "microsoft.com", "apple.com",
                          "amazon.com", "paypal.com", "chase.com", "bankofamerica.com"]
        for legit in common_domains:
            if domain != legit and self._is_lookalike(domain, legit):
                findings.append(f"Possible lookalike domain: {domain} (looks like {legit})")
                score += 30
                break

        # Unusual characters or patterns
        if re.search(r'\d{3,}', sender.split("@")[0]):
            findings.append("Sender address contains suspicious number sequence")
            score += 5

        return {"findings": findings, "score": score}

    def _check_subject_patterns(self, email_data):
        """Check subject line against known phishing patterns."""
        findings = []
        score = 0
        subject = email_data.get("subject", "")

        for pattern in PHISHING_SUBJECT_PATTERNS:
            if re.search(pattern, subject):
                findings.append(f"Phishing pattern detected in subject: {pattern[:40]}...")
                score += 15
                break  # One match is enough

        return {"findings": findings, "score": score}

    def _check_bec_patterns(self, email_data):
        """Check for Business Email Compromise patterns."""
        findings = []
        score = 0
        body = email_data.get("body_text", "") or email_data.get("snippet", "")

        for pattern in BEC_PATTERNS:
            if re.search(pattern, body):
                findings.append(f"BEC pattern detected: {pattern[:50]}...")
                score += 20
                break

        return {"findings": findings, "score": score}

    def _check_links(self, email_data):
        """Analyze URLs in email body for suspicious patterns."""
        findings = []
        score = 0
        body_html = email_data.get("body_html", "")
        body_text = email_data.get("body_text", "")

        # Extract URLs
        urls = re.findall(r'https?://[^\s<>"\']+', body_html + " " + body_text)
        unique_domains = set()

        for url in urls[:20]:  # Limit analysis
            try:
                parsed = urlparse(url)
                domain = parsed.hostname or ""
                unique_domains.add(domain)

                # IP address URL
                if re.match(r'\d+\.\d+\.\d+\.\d+', domain):
                    findings.append(f"URL uses IP address instead of domain: {domain}")
                    score += 20

                # Suspicious TLD in link
                for tld in SUSPICIOUS_TLDS:
                    if domain.endswith(tld):
                        findings.append(f"Link to suspicious domain: {domain}")
                        score += 10
                        break

                # URL shorteners (potential redirect tricks)
                shorteners = ["bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly", "is.gd"]
                if domain in shorteners:
                    findings.append(f"URL shortener detected: {domain}")
                    score += 5

            except Exception:
                pass

        # Too many different domains is suspicious
        if len(unique_domains) > 5:
            findings.append(f"Email contains links to {len(unique_domains)} different domains")
            score += 5

        return {"findings": findings, "score": score}

    def _check_reply_to(self, email_data):
        """Check if Reply-To differs from From address (common spoof technique)."""
        findings = []
        score = 0

        from_domain = email_data.get("sender_domain", "").lower()
        # Note: reply_to would need to be parsed from headers
        # This is a placeholder for when full header parsing is implemented

        return {"findings": findings, "score": score}

    def _is_lookalike(self, domain, legit_domain):
        """Simple lookalike domain detection using edit distance."""
        if domain == legit_domain:
            return False

        # Check for common substitutions
        # g00gle.com, amaz0n.com, etc.
        normalized = domain.replace("0", "o").replace("1", "l").replace("rn", "m")
        if normalized == legit_domain:
            return True

        # Check Levenshtein distance (simple implementation)
        if len(domain) == len(legit_domain):
            diff = sum(1 for a, b in zip(domain, legit_domain) if a != b)
            if diff <= 2:
                return True

        return False

    def _log_alert(self, result):
        """Log security alert to security log."""
        with open(self.security_log, "a") as f:
            f.write(json.dumps(result) + "\n")


def main():
    parser = argparse.ArgumentParser(description="MAILMAN Security Scanner")
    parser.add_argument("--scan", type=str, help="Scan recent emails for account")
    parser.add_argument("--report", action="store_true", help="Show security alerts")
    args = parser.parse_args()

    scanner = SecurityScanner()

    if args.report:
        if scanner.security_log.exists():
            with open(scanner.security_log) as f:
                alerts = [json.loads(line) for line in f if line.strip()]
            print(f"\nSecurity Alerts ({len(alerts)} total):")
            for a in alerts[-20:]:
                print(f"  [{a['threat_level']:10s}] Score:{a['score']:3d} | {a['sender']:30s} | {a['subject'][:40]}")
        else:
            print("No security alerts logged yet.")

    elif args.scan:
        from gmail_client import GmailClient
        client = GmailClient(args.scan)
        print(f"Scanning '{args.scan}' for security threats...")
        emails = client.fetch_since(hours=48, max_results=100)

        threats = []
        for em in emails:
            result = scanner.scan_email(em)
            if result["threat_level"] != "safe":
                threats.append(result)
                print(f"  [{result['threat_level']:10s}] {em['sender_email']}: {em['subject'][:50]}")

        print(f"\nScan complete: {len(threats)} threats detected out of {len(emails)} emails")


if __name__ == "__main__":
    main()
