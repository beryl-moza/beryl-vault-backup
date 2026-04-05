#!/usr/bin/env python3
"""
MAILMAN Voice Learner
Analyzes your sent emails to learn your writing style, then generates
draft replies that sound like you. Fyxer parity + more.

How it works:
1. Pulls your sent mail via Gmail API
2. Builds a style profile: sentence length, vocabulary, greeting patterns,
   sign-off patterns, formality level, emoji usage, punctuation habits
3. Stores the profile in _memory/voice_profile.json
4. When drafting replies, feeds the profile + context to Claude for
   tone-matched output
5. Can also route to arc-email-crafter for brand-voice emails (Antidote, etc.)

Usage:
  python3 voice_learner.py --train <account>          # Learn from sent emails
  python3 voice_learner.py --profile                  # Show current voice profile
  python3 voice_learner.py --draft <message_id>       # Draft reply to an email
  python3 voice_learner.py --draft-custom "<prompt>"  # Draft from a prompt
"""

import json
import argparse
import re
import sys
from datetime import datetime
from pathlib import Path
from collections import Counter

try:
    import anthropic
except ImportError:
    print("Missing: pip install anthropic --break-system-packages")
    sys.exit(1)

MAILMAN_ROOT = Path(__file__).parent.parent
MEMORY_DIR = MAILMAN_ROOT / "_memory"
MEMORY_DIR.mkdir(exist_ok=True)


class VoiceLearner:
    """
    Learns your writing style from sent emails and generates
    tone-matched draft replies.
    """

    def __init__(self):
        self.client = anthropic.Anthropic()
        self.profile_path = MEMORY_DIR / "voice_profile.json"
        self.profile = self._load_profile()

    def _load_profile(self):
        if self.profile_path.exists():
            with open(self.profile_path) as f:
                return json.load(f)
        return self._default_profile()

    def _default_profile(self):
        return {
            "trained_on": 0,
            "last_trained": None,
            "accounts_trained": [],
            "style": {
                "avg_sentence_length": 0,
                "avg_email_length_words": 0,
                "formality_score": 0.5,
                "emoji_frequency": 0.0,
                "exclamation_frequency": 0.0,
                "question_frequency": 0.0,
                "contraction_rate": 0.0,
                "paragraph_count_avg": 0,
            },
            "patterns": {
                "greetings": [],
                "signoffs": [],
                "filler_phrases": [],
                "favorite_words": [],
                "avoided_words": [],
                "punctuation_habits": {},
            },
            "context_styles": {
                "to_vip": {"formality": 0, "avg_length": 0, "sample_count": 0},
                "to_team": {"formality": 0, "avg_length": 0, "sample_count": 0},
                "to_client": {"formality": 0, "avg_length": 0, "sample_count": 0},
                "to_stranger": {"formality": 0, "avg_length": 0, "sample_count": 0},
                "quick_reply": {"formality": 0, "avg_length": 0, "sample_count": 0},
                "long_form": {"formality": 0, "avg_length": 0, "sample_count": 0},
            },
            "ai_analysis": None,
        }

    def _save_profile(self):
        with open(self.profile_path, "w") as f:
            json.dump(self.profile, f, indent=2)

    def train(self, gmail_client, max_emails=200):
        """
        Analyze sent emails to build a voice profile.

        Args:
            gmail_client: Authenticated GmailClient instance
            max_emails: Maximum sent emails to analyze
        """
        print(f"Fetching up to {max_emails} sent emails for voice training...")
        sent_emails = gmail_client.fetch_sent(max_results=max_emails)
        print(f"Analyzing {len(sent_emails)} sent emails...")

        if not sent_emails:
            print("No sent emails found. Cannot train voice profile.")
            return

        # Collect raw metrics
        all_bodies = []
        greetings = Counter()
        signoffs = Counter()
        word_freq = Counter()
        sentence_lengths = []
        email_lengths = []
        emoji_count = 0
        exclamation_count = 0
        question_count = 0
        contraction_count = 0
        total_words = 0
        paragraph_counts = []

        for email in sent_emails:
            body = email.get("body_text", "")
            if not body or len(body) < 20:
                continue

            all_bodies.append(body)

            # Word count
            words = body.split()
            word_count = len(words)
            email_lengths.append(word_count)
            total_words += word_count

            # Word frequency (skip very common words)
            stopwords = {"the", "a", "an", "is", "are", "was", "were", "be", "been",
                         "being", "have", "has", "had", "do", "does", "did", "will",
                         "would", "could", "should", "may", "might", "shall", "can",
                         "to", "of", "in", "for", "on", "with", "at", "by", "from",
                         "it", "its", "this", "that", "these", "those", "i", "you",
                         "we", "they", "he", "she", "my", "your", "our", "and", "or",
                         "but", "not", "no", "if", "so", "as", "me", "him", "her",
                         "us", "them", "what", "which", "who", "when", "where", "how"}
            clean_words = [w.lower().strip(".,!?;:\"'()") for w in words
                           if w.lower().strip(".,!?;:\"'()") not in stopwords and len(w) > 2]
            word_freq.update(clean_words)

            # Sentence analysis
            sentences = re.split(r'[.!?]+', body)
            for s in sentences:
                s = s.strip()
                if s:
                    sentence_lengths.append(len(s.split()))

            # Paragraph count
            paragraphs = [p.strip() for p in body.split("\n\n") if p.strip()]
            paragraph_counts.append(len(paragraphs))

            # Greeting detection (first line patterns)
            first_line = body.strip().split("\n")[0].strip()
            greeting_patterns = [
                r'^(hey|hi|hello|howdy|yo|sup|good morning|good afternoon|good evening)',
                r'^(dear|greetings|hola|what\'s up|hope)',
            ]
            for pat in greeting_patterns:
                match = re.match(pat, first_line, re.IGNORECASE)
                if match:
                    # Capture greeting up to first comma or period
                    greeting = re.split(r'[,.]', first_line)[0].strip()
                    if len(greeting) < 50:
                        greetings[greeting.lower()] += 1
                    break

            # Sign-off detection (last few lines)
            lines = [l.strip() for l in body.strip().split("\n") if l.strip()]
            if len(lines) >= 2:
                signoff_patterns = [
                    r'^(best|regards|thanks|thank you|cheers|warmly|peace|love)',
                    r'^(sincerely|respectfully|all the best|take care|talk soon)',
                    r'^(sent from|--|___)',
                ]
                for line in lines[-3:]:
                    for pat in signoff_patterns:
                        if re.match(pat, line, re.IGNORECASE):
                            signoff = line[:60]
                            signoffs[signoff.lower()] += 1
                            break

            # Emoji detection
            emoji_pattern = re.compile(
                "[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF"
                "\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF"
                "\U00002702-\U000027B0\U000024C2-\U0001F251]+",
                flags=re.UNICODE
            )
            emoji_count += len(emoji_pattern.findall(body))

            # Punctuation habits
            exclamation_count += body.count("!")
            question_count += body.count("?")

            # Contraction detection
            contraction_pattern = r"\b\w+'\w+\b"
            contraction_count += len(re.findall(contraction_pattern, body))

        # Build statistical profile
        n = len(all_bodies)
        if n == 0:
            print("No usable email bodies found.")
            return

        self.profile["trained_on"] = n
        self.profile["last_trained"] = datetime.utcnow().isoformat()
        self.profile["style"]["avg_sentence_length"] = round(
            sum(sentence_lengths) / max(len(sentence_lengths), 1), 1
        )
        self.profile["style"]["avg_email_length_words"] = round(
            sum(email_lengths) / n, 1
        )
        self.profile["style"]["emoji_frequency"] = round(emoji_count / n, 3)
        self.profile["style"]["exclamation_frequency"] = round(exclamation_count / max(total_words, 1), 4)
        self.profile["style"]["question_frequency"] = round(question_count / max(total_words, 1), 4)
        self.profile["style"]["contraction_rate"] = round(contraction_count / max(total_words, 1), 4)
        self.profile["style"]["paragraph_count_avg"] = round(
            sum(paragraph_counts) / max(len(paragraph_counts), 1), 1
        )

        # Top patterns
        self.profile["patterns"]["greetings"] = [g for g, _ in greetings.most_common(5)]
        self.profile["patterns"]["signoffs"] = [s for s, _ in signoffs.most_common(5)]
        self.profile["patterns"]["favorite_words"] = [w for w, _ in word_freq.most_common(30)]

        # AI-powered deep style analysis
        print("Running AI-powered style analysis...")
        self._ai_style_analysis(all_bodies[:30])

        self._save_profile()
        print(f"Voice profile trained on {n} emails. Saved to {self.profile_path}")

    def _ai_style_analysis(self, sample_bodies):
        """Use Claude to do a deeper qualitative analysis of writing style."""
        combined = "\n---EMAIL BREAK---\n".join(sample_bodies[:15])
        if len(combined) > 8000:
            combined = combined[:8000]

        prompt = f"""Analyze the writing style across these email samples from ONE person.
Return a JSON object with these fields:

{{
  "formality_score": <0.0 to 1.0, where 0 is very casual and 1 is very formal>,
  "tone_description": "<2-3 word description like 'warm and direct' or 'professional but friendly'>",
  "vocabulary_level": "<simple|moderate|sophisticated>",
  "humor_usage": "<none|occasional|frequent>",
  "directness": "<indirect|balanced|direct|very_direct>",
  "emotional_warmth": "<cool|neutral|warm|very_warm>",
  "typical_structure": "<description of how they structure emails>",
  "notable_habits": ["list of 3-5 distinctive writing habits"],
  "words_to_avoid": ["words this person never uses based on the samples"],
  "voice_summary": "<A 2-3 sentence description of this person's email voice that could be used as instructions for an AI to mimic their style>"
}}

Return ONLY valid JSON, no other text.

EMAIL SAMPLES:
{combined}"""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-5-20250514",
                max_tokens=800,
                messages=[{"role": "user", "content": prompt}],
            )
            result_text = response.content[0].text.strip()
            if result_text.startswith("```"):
                result_text = result_text.split("\n", 1)[1].rsplit("```", 1)[0]

            analysis = json.loads(result_text)
            self.profile["ai_analysis"] = analysis
            self.profile["style"]["formality_score"] = analysis.get("formality_score", 0.5)

        except Exception as e:
            print(f"AI style analysis error: {e}")
            self.profile["ai_analysis"] = {"error": str(e)}

    def draft_reply(self, original_email, gmail_client=None, tone_override=None):
        """
        Generate a draft reply matching the user's voice profile.

        Args:
            original_email: The email dict to reply to
            gmail_client: Optional, for thread context
            tone_override: Optional, e.g. "more formal" or "keep it brief"

        Returns:
            Draft reply string
        """
        voice = self.profile.get("ai_analysis", {})
        voice_summary = voice.get("voice_summary", "Write in a natural, human tone.")
        habits = voice.get("notable_habits", [])
        greetings = self.profile.get("patterns", {}).get("greetings", [])
        signoffs = self.profile.get("patterns", {}).get("signoffs", [])
        avg_length = self.profile.get("style", {}).get("avg_email_length_words", 100)

        # Build thread context if available
        thread_context = ""
        if gmail_client and original_email.get("thread_id"):
            thread = gmail_client.get_thread(original_email["thread_id"])
            if thread and len(thread) > 1:
                recent = thread[-3:]  # Last 3 messages
                thread_context = "RECENT THREAD MESSAGES:\n"
                for msg in recent:
                    thread_context += f"From: {msg.get('sender_name', '')} <{msg.get('sender_email', '')}>\n"
                    thread_context += f"Date: {msg.get('date', '')}\n"
                    thread_context += f"Body: {(msg.get('body_text', '') or '')[:500]}\n---\n"

        prompt = f"""You are drafting an email reply AS the user. Match their voice exactly.

VOICE PROFILE:
{voice_summary}

WRITING HABITS:
{chr(10).join(f'- {h}' for h in habits) if habits else '- No specific habits detected yet'}

COMMON GREETINGS: {', '.join(greetings[:3]) if greetings else 'varies'}
COMMON SIGN-OFFS: {', '.join(signoffs[:3]) if signoffs else 'varies'}
TARGET LENGTH: ~{avg_length} words (adjust based on context)

{thread_context}

EMAIL TO REPLY TO:
From: {original_email.get('sender_name', '')} <{original_email.get('sender_email', '')}>
Subject: {original_email.get('subject', '')}
Date: {original_email.get('date', '')}
Body:
{(original_email.get('body_text', '') or original_email.get('snippet', ''))[:2000]}

{f'TONE ADJUSTMENT: {tone_override}' if tone_override else ''}

RULES:
- Write as if you ARE the user, not as an AI assistant
- Match their greeting and sign-off style
- Match their sentence length and formality level
- Never use em dashes, en dashes, or triple dashes
- Never use AI-speak (delve, tapestry, leverage, synergy, robust, seamless, holistic)
- Use Oxford commas
- If the email needs a quick response, keep it short
- If it needs a detailed response, be thorough but match their natural voice
- Do NOT include subject line, just the body

Draft the reply:"""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-5-20250514",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text.strip()
        except Exception as e:
            return f"Error generating draft: {e}"

    def draft_from_prompt(self, prompt_text, recipient_context=None):
        """
        Draft a fresh email (not a reply) from a prompt, in the user's voice.

        Args:
            prompt_text: What the user wants to say
            recipient_context: Optional dict with 'name', 'email', 'relationship'
        """
        voice = self.profile.get("ai_analysis", {})
        voice_summary = voice.get("voice_summary", "Write in a natural, human tone.")

        ctx = ""
        if recipient_context:
            ctx = f"\nRECIPIENT: {recipient_context.get('name', 'Unknown')} ({recipient_context.get('relationship', 'unknown relationship')})"

        prompt = f"""You are drafting an email AS the user. Match their voice exactly.

VOICE PROFILE:
{voice_summary}

FORMALITY: {voice.get('directness', 'direct')}, {voice.get('emotional_warmth', 'warm')}
{ctx}

WHAT THE USER WANTS TO SAY:
{prompt_text}

RULES:
- Write as if you ARE the user
- Never use em dashes, en dashes, or triple dashes
- Never use AI-speak
- Use Oxford commas
- Include a subject line suggestion at the top: "Subject: ..."
- Then the email body

Draft the email:"""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-5-20250514",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text.strip()
        except Exception as e:
            return f"Error generating draft: {e}"

    def show_profile(self):
        """Display the current voice profile."""
        if not self.profile.get("last_trained"):
            print("No voice profile trained yet. Run --train first.")
            return

        print(f"\nVoice Profile (trained on {self.profile['trained_on']} emails)")
        print(f"Last trained: {self.profile['last_trained']}")
        print(f"\nStyle Metrics:")
        for k, v in self.profile["style"].items():
            print(f"  {k}: {v}")

        print(f"\nTop Greetings: {', '.join(self.profile['patterns'].get('greetings', []))}")
        print(f"Top Sign-offs: {', '.join(self.profile['patterns'].get('signoffs', []))}")
        print(f"Favorite Words: {', '.join(self.profile['patterns'].get('favorite_words', [])[:10])}")

        ai = self.profile.get("ai_analysis", {})
        if ai and "voice_summary" in ai:
            print(f"\nAI Voice Summary:")
            print(f"  {ai['voice_summary']}")
            print(f"  Tone: {ai.get('tone_description', 'N/A')}")
            print(f"  Directness: {ai.get('directness', 'N/A')}")
            print(f"  Warmth: {ai.get('emotional_warmth', 'N/A')}")
            if ai.get("notable_habits"):
                print(f"  Habits:")
                for h in ai["notable_habits"]:
                    print(f"    - {h}")


def main():
    parser = argparse.ArgumentParser(description="MAILMAN Voice Learner")
    parser.add_argument("--train", type=str, help="Train voice from sent emails of <account>")
    parser.add_argument("--profile", action="store_true", help="Show current voice profile")
    parser.add_argument("--draft", type=str, help="Draft reply to <message_id>")
    parser.add_argument("--draft-custom", type=str, help="Draft from a text prompt")
    parser.add_argument("--account", type=str, default="gmail_personal", help="Account name")
    parser.add_argument("--tone", type=str, help="Tone override for drafts")
    args = parser.parse_args()

    learner = VoiceLearner()

    if args.profile:
        learner.show_profile()

    elif args.train:
        from gmail_client import GmailClient
        client = GmailClient(args.train)
        learner.train(client)

    elif args.draft:
        from gmail_client import GmailClient
        client = GmailClient(args.account)
        email = client.get_message(args.draft)
        if email:
            draft = learner.draft_reply(email, client, tone_override=args.tone)
            print(f"\n--- DRAFT REPLY ---\n{draft}\n--- END DRAFT ---")
        else:
            print(f"Message {args.draft} not found.")

    elif args.draft_custom:
        draft = learner.draft_from_prompt(args.draft_custom)
        print(f"\n--- DRAFT EMAIL ---\n{draft}\n--- END DRAFT ---")


if __name__ == "__main__":
    main()
