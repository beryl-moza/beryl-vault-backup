#!/usr/bin/env python3
"""
MAILMAN Smart Replies
Generates 3 reply options for emails that need responses.

Usage:
  python3 smart_replies.py --suggest <message_id>  # Generate reply options
  python3 smart_replies.py --quick-replies          # Show quick reply templates
  python3 smart_replies.py --refine                 # Refine a draft reply
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
LOGS_DIR = MAILMAN_ROOT / "logs"
MEMORY_DIR = MAILMAN_ROOT / "_memory"
LOGS_DIR.mkdir(exist_ok=True)
MEMORY_DIR.mkdir(exist_ok=True)


REPLY_GENERATION_PROMPT = """You are MAILMAN's smart reply generator. Generate 3 reply options for this email.

EMAIL METADATA:
From: {sender_name} <{sender_email}>
Subject: {subject}
Date: {date}
Body (first 2000 chars): {body_preview}

CLASSIFICATION:
Priority: {priority}
Category: {category}
Needs Response: {needs_response}
Summary: {summary}

VOICE PROFILE (Beryl's style):
{voice_profile}

Generate 3 reply options. Return ONLY valid JSON:
{{
  "options": [
    {{
      "id": 1,
      "type": "quick",
      "subject": "Re: {original_subject}",
      "body": "Brief acknowledgment or quick response (1-2 sentences)",
      "confidence": 0.9
    }},
    {{
      "id": 2,
      "type": "full",
      "subject": "Re: {original_subject}",
      "body": "Substantive reply matching Beryl's voice and addressing all points",
      "confidence": 0.85
    }},
    {{
      "id": 3,
      "type": "delegate",
      "subject": "Re: {original_subject}",
      "body": "Delegating, deferring, or looping in someone else",
      "confidence": 0.8
    }}
  ]
}}

Rules:
- Quick option: "Got it, will handle by EOD" or "Thanks for this, reviewing now"
- Full option: 2-4 paragraphs addressing all points in the email
- Delegate option: "Looping in [person]" or "I'll get back to you by [date]"
- Match Beryl's tone from voice profile (or default to professional, clear, direct)
- Keep body under 500 chars for quick, under 1500 for full
- All replies should feel natural, not robotic
- If no voice profile: use professional, concise, action-oriented tone
"""

REFINE_PROMPT = """Refine this email reply draft based on the instruction.

ORIGINAL DRAFT:
{draft}

INSTRUCTION:
{instruction}

Return ONLY the refined reply text (no JSON, no markdown):"""


class SmartReplies:
    """
    Generates contextual reply options using AI and voice profile.
    """

    def __init__(self):
        self.client = anthropic.Anthropic()
        self.voice_profile = self._load_voice_profile()
        self.suggestions_log = LOGS_DIR / "smart_replies_log.jsonl"

    def _load_voice_profile(self):
        """Load Beryl's voice profile if it exists."""
        voice_file = MEMORY_DIR / "voice_profile.json"
        if voice_file.exists():
            try:
                with open(voice_file) as f:
                    data = json.load(f)
                    return data.get("profile", "")
            except (json.JSONDecodeError, FileNotFoundError):
                return ""
        return ""

    def generate_options(self, email_data, classification, voice_profile=None):
        """
        Generate 3 reply options for an email.

        Args:
            email_data: Parsed email dict from GmailClient
            classification: Classification result from EmailClassifier
            voice_profile: Optional override for voice profile

        Returns:
            List of reply option dicts with id, type, subject, body, confidence
        """
        voice = voice_profile or self.voice_profile or "Professional, direct, and action-oriented tone"
        body_preview = (email_data.get("body_text", "") or email_data.get("snippet", ""))[:2000]

        prompt = REPLY_GENERATION_PROMPT.format(
            sender_name=email_data.get("sender_name", ""),
            sender_email=email_data.get("sender_email", ""),
            subject=email_data.get("subject", ""),
            date=email_data.get("date", ""),
            body_preview=body_preview,
            priority=classification.get("priority", "P3"),
            category=classification.get("category", ""),
            needs_response=classification.get("needs_response", False),
            summary=classification.get("summary", ""),
            voice_profile=voice,
            original_subject=email_data.get("subject", ""),
        )

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-5-20250514",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}],
            )
            result_text = response.content[0].text.strip()

            # Parse JSON from response (handle markdown code blocks)
            if result_text.startswith("```"):
                result_text = result_text.split("\n", 1)[1].rsplit("```", 1)[0]

            generated = json.loads(result_text)
            options = generated.get("options", [])

            # Log suggestions
            self._log_suggestion(email_data, options)

            return options

        except Exception as e:
            print(f"Reply generation error: {e}")
            self._log_suggestion(email_data, [], error=str(e))
            return []

    def generate_custom(self, email_data, instruction, voice_profile=None):
        """
        Generate a custom reply with specific instruction.

        Args:
            email_data: Parsed email dict
            instruction: Instruction for reply (e.g., "make it shorter", "ask for clarification")
            voice_profile: Optional voice profile override

        Returns:
            Generated reply text
        """
        voice = voice_profile or self.voice_profile or "Professional tone"
        body_preview = (email_data.get("body_text", "") or email_data.get("snippet", ""))[:2000]

        # First, generate a base reply
        base_prompt = REPLY_GENERATION_PROMPT.format(
            sender_name=email_data.get("sender_name", ""),
            sender_email=email_data.get("sender_email", ""),
            subject=email_data.get("subject", ""),
            date=email_data.get("date", ""),
            body_preview=body_preview,
            priority="P1",
            category="",
            needs_response=True,
            summary="",
            voice_profile=voice,
            original_subject=email_data.get("subject", ""),
        )

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-5-20250514",
                max_tokens=2000,
                messages=[{"role": "user", "content": base_prompt}],
            )
            result_text = response.content[0].text.strip()

            if result_text.startswith("```"):
                result_text = result_text.split("\n", 1)[1].rsplit("```", 1)[0]

            generated = json.loads(result_text)
            base_reply = generated["options"][1]["body"] if len(generated["options"]) > 1 else ""

            # Now refine based on instruction
            return self.refine(base_reply, instruction)

        except Exception as e:
            print(f"Custom reply generation error: {e}")
            return ""

    def refine(self, draft, instruction):
        """
        Refine a reply draft based on an instruction.

        Args:
            draft: Current draft text
            instruction: Refinement instruction (e.g., "make it shorter", "more formal")

        Returns:
            Refined reply text
        """
        prompt = REFINE_PROMPT.format(
            draft=draft,
            instruction=instruction,
        )

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-5-20250514",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text.strip()
        except Exception as e:
            print(f"Refinement error: {e}")
            return draft

    def get_quick_replies(self):
        """
        Get quick reply templates for common situations.

        Returns:
            List of quick reply templates
        """
        return [
            {"id": "ack_quick", "text": "Got it, will review and get back to you by EOD."},
            {"id": "ack_seen", "text": "Thanks for this. I've seen it and will prioritize it."},
            {"id": "confirm_meeting", "text": "Confirmed for [TIME] on [DATE]. Looking forward to it."},
            {"id": "defer_later", "text": "I'll get back to you on this by [DATE]. Thanks for your patience."},
            {"id": "defer_person", "text": "Looping in [PERSON] who can help with this."},
            {"id": "thanks_brief", "text": "Thanks for the update. Appreciate you keeping me in the loop."},
            {"id": "will_do", "text": "Will do. I'll have this done by [DATE]."},
            {"id": "clarify_please", "text": "Quick clarification: [QUESTION]? Then I can move forward."},
        ]

    def _log_suggestion(self, email_data, options, error=None):
        """Log reply suggestion generation."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "message_id": email_data.get("id", ""),
            "sender": email_data.get("sender_email", ""),
            "subject": email_data.get("subject", ""),
            "options_generated": len(options),
            "error": error,
        }
        with open(self.suggestions_log, "a") as f:
            f.write(json.dumps(log_entry) + "\n")


def main():
    parser = argparse.ArgumentParser(description="MAILMAN Smart Replies")
    parser.add_argument("--suggest", type=str, help="Generate reply options for message ID")
    parser.add_argument("--quick-replies", action="store_true", help="Show quick reply templates")
    parser.add_argument("--refine", action="store_true", help="Refine a draft (use stdin)")
    args = parser.parse_args()

    replies = SmartReplies()

    if args.quick_replies:
        quick = replies.get_quick_replies()
        print("QUICK REPLY TEMPLATES:\n")
        for q in quick:
            print(f"  [{q['id']}]")
            print(f"    {q['text']}\n")

    elif args.suggest:
        print(f"To suggest replies for {args.suggest}, use:")
        print("  replies.generate_options(email_data, classification)")

    elif args.refine:
        print("Refine mode: reads draft from stdin")
        print("Usage: cat draft.txt | python3 smart_replies.py --refine 'make it shorter'")
        # Note: would need to extend argument parsing for this

    else:
        print("Use --help for options")


if __name__ == "__main__":
    main()
