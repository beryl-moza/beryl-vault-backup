#!/usr/bin/env python3
"""
MAILMAN Email Templates Library
Stores and retrieves reusable email reply templates with variable support.

Usage:
  python3 templates.py --list                    # List all templates
  python3 templates.py --add                     # Add new template (interactive)
  python3 templates.py --render <template_id>    # Render template with variables
  python3 templates.py --suggest <message_id>    # Suggest template for email
"""

import json
import argparse
import sys
from datetime import datetime
from pathlib import Path
from uuid import uuid4

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


DEFAULT_TEMPLATES = {
    "templates": [
        {
            "id": "meeting_confirm",
            "name": "Meeting Confirmation",
            "category": "meetings",
            "subject": "Re: {{original_subject}}",
            "body": "Thanks for proposing this meeting. I have it on my calendar for {{meeting_date}} at {{meeting_time}}. Looking forward to discussing {{topic}}.",
            "variables": ["original_subject", "meeting_date", "meeting_time", "topic"],
            "created_at": datetime.utcnow().isoformat(),
        },
        {
            "id": "intro_response",
            "name": "Intro Request Response",
            "category": "outreach",
            "subject": "Re: Introduction to {{sender_name}}",
            "body": "Thanks for the intro. Great to connect with {{sender_name}}. I'd love to learn more about {{company}} and explore opportunities to work together.",
            "variables": ["sender_name", "company"],
            "created_at": datetime.utcnow().isoformat(),
        },
        {
            "id": "follow_up",
            "name": "Gentle Follow-up",
            "category": "follow-ups",
            "subject": "Following up on {{original_subject}}",
            "body": "Hi {{sender_name}},\n\nI wanted to follow up on the {{topic}} we discussed. Do you have any updates or thoughts? I'm happy to help move this forward.",
            "variables": ["original_subject", "sender_name", "topic"],
            "created_at": datetime.utcnow().isoformat(),
        },
        {
            "id": "delegate",
            "name": "Delegate to Colleague",
            "category": "delegation",
            "subject": "Re: {{original_subject}}",
            "body": "Thanks for this. I'm looping in {{colleague_name}} who is better positioned to help with {{task}}. {{colleague_name}}, can you take it from here?",
            "variables": ["original_subject", "colleague_name", "task"],
            "created_at": datetime.utcnow().isoformat(),
        },
        {
            "id": "decline_politely",
            "name": "Polite Decline",
            "category": "responses",
            "subject": "Re: {{original_subject}}",
            "body": "Thanks for reaching out about {{request}}. I appreciate the opportunity, but I'm not able to take this on at the moment due to {{reason}}. I hope you can find someone who's a good fit.",
            "variables": ["original_subject", "request", "reason"],
            "created_at": datetime.utcnow().isoformat(),
        },
        {
            "id": "acknowledge",
            "name": "Quick Acknowledgment",
            "category": "acknowledgments",
            "subject": "Re: {{original_subject}}",
            "body": "Got it. I've noted this and will handle it by {{deadline}}. Thanks for looping me in.",
            "variables": ["original_subject", "deadline"],
            "created_at": datetime.utcnow().isoformat(),
        },
        {
            "id": "out_of_office",
            "name": "Out of Office Auto-reply",
            "category": "automation",
            "subject": "Out of Office: {{original_subject}}",
            "body": "I'm currently out of the office and will return on {{return_date}}. I will have limited email access. For urgent matters, please contact {{backup_contact}}. I'll get back to you when I return.",
            "variables": ["original_subject", "return_date", "backup_contact"],
            "created_at": datetime.utcnow().isoformat(),
        },
        {
            "id": "thank_you",
            "name": "Thank You Note",
            "category": "gratitude",
            "subject": "Thank you for {{action}}",
            "body": "{{sender_name}},\n\nI wanted to thank you for {{action}}. It really meant a lot to me. Your support and {{quality}} are much appreciated.",
            "variables": ["sender_name", "action", "quality"],
            "created_at": datetime.utcnow().isoformat(),
        },
    ]
}

TEMPLATE_SUGGESTION_PROMPT = """You are MAILMAN's template suggestion system. Analyze this email and suggest appropriate templates.

EMAIL METADATA:
From: {sender_name} <{sender_email}>
Subject: {subject}
Body (first 1000 chars): {body_preview}

CLASSIFICATION:
Priority: {priority}
Category: {category}
Summary: {summary}

AVAILABLE TEMPLATES:
{available_templates}

Suggest the 2-3 most appropriate templates for this email. Return ONLY valid JSON:
{{
  "suggestions": [
    {{
      "template_id": "meeting_confirm",
      "name": "Meeting Confirmation",
      "confidence": 0.95,
      "reason": "Email contains meeting date and time"
    }}
  ]
}}

Rules:
- Match based on email type and content
- Only suggest templates that are clearly relevant
- Provide confidence scores (0.0-1.0)
- Include brief reason for each suggestion
"""


class TemplateLibrary:
    """
    Manages reusable email templates with variable support.
    """

    def __init__(self):
        self.client = anthropic.Anthropic()
        self.templates_file = MEMORY_DIR / "email_templates.json"
        self.suggestion_log = LOGS_DIR / "template_suggestion_log.jsonl"
        self._ensure_templates_file()

    def _ensure_templates_file(self):
        """Ensure templates file exists with defaults."""
        if not self.templates_file.exists():
            self.templates_file.write_text(json.dumps(DEFAULT_TEMPLATES, indent=2))

    def _load_templates(self):
        """Load all templates from disk."""
        try:
            with open(self.templates_file) as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return DEFAULT_TEMPLATES.copy()

    def _save_templates(self, data):
        """Save templates to disk."""
        with open(self.templates_file, "w") as f:
            json.dump(data, f, indent=2)

    def get_template(self, template_id):
        """
        Get a single template by ID.

        Args:
            template_id: Template ID (e.g., "meeting_confirm")

        Returns:
            Template dict or None if not found
        """
        data = self._load_templates()
        for template in data.get("templates", []):
            if template.get("id") == template_id:
                return template
        return None

    def list_templates(self, category=None):
        """
        List all templates, optionally filtered by category.

        Args:
            category: Filter by category (e.g., "meetings") or None for all

        Returns:
            List of template dicts
        """
        data = self._load_templates()
        templates = data.get("templates", [])

        if category:
            templates = [t for t in templates if t.get("category") == category]

        return sorted(templates, key=lambda t: t.get("name", ""))

    def add_template(self, name, category, subject, body, variables=None):
        """
        Add a new template to the library.

        Args:
            name: Template display name
            category: Category (e.g., "meetings", "follow-ups")
            subject: Email subject template (supports {{variable}} syntax)
            body: Email body template (supports {{variable}} syntax)
            variables: List of variable names used in template

        Returns:
            Created template dict
        """
        template_id = f"tmpl_{uuid4().hex[:8]}"

        template = {
            "id": template_id,
            "name": name,
            "category": category,
            "subject": subject,
            "body": body,
            "variables": variables or [],
            "created_at": datetime.utcnow().isoformat(),
        }

        data = self._load_templates()
        data["templates"].append(template)
        self._save_templates(data)

        return template

    def remove_template(self, template_id):
        """
        Remove a template from the library.

        Args:
            template_id: Template ID to remove

        Returns:
            True if removed, False if not found
        """
        data = self._load_templates()
        original_count = len(data.get("templates", []))

        data["templates"] = [
            t for t in data.get("templates", [])
            if t.get("id") != template_id
        ]

        if len(data["templates"]) < original_count:
            self._save_templates(data)
            return True

        return False

    def render_template(self, template_id, context_dict):
        """
        Render a template by filling in variables.

        Args:
            template_id: Template ID
            context_dict: Dictionary of variable values
                         (e.g., {"meeting_date": "2026-03-20", "topic": "project planning"})

        Returns:
            Rendered template dict with filled subject and body, or None if not found
        """
        template = self.get_template(template_id)
        if not template:
            return None

        rendered = dict(template)
        subject = template.get("subject", "")
        body = template.get("body", "")

        # Replace all {{variable}} with values from context
        for var_name, var_value in context_dict.items():
            placeholder = f"{{{{{var_name}}}}}"
            subject = subject.replace(placeholder, str(var_value))
            body = body.replace(placeholder, str(var_value))

        rendered["subject"] = subject
        rendered["body"] = body
        rendered["rendered_at"] = datetime.utcnow().isoformat()
        rendered["context_used"] = context_dict

        return rendered

    def suggest_template(self, email_data, classification):
        """
        Suggest templates for an email based on its content.

        Args:
            email_data: Parsed email dict from GmailClient
            classification: Classification result from EmailClassifier

        Returns:
            List of suggested template dicts with confidence scores
        """
        body_preview = (email_data.get("body_text", "") or email_data.get("snippet", ""))[:1000]

        # Build available templates list
        all_templates = self.list_templates()
        templates_str = "\n".join(
            f"- {t['id']}: {t['name']} (category: {t['category']})"
            for t in all_templates
        )

        prompt = TEMPLATE_SUGGESTION_PROMPT.format(
            sender_name=email_data.get("sender_name", ""),
            sender_email=email_data.get("sender_email", ""),
            subject=email_data.get("subject", ""),
            body_preview=body_preview,
            priority=classification.get("priority", "P3"),
            category=classification.get("category", ""),
            summary=classification.get("summary", ""),
            available_templates=templates_str,
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

            suggestions = json.loads(result_text)
            self._log_suggestion(email_data, suggestions)

            return suggestions.get("suggestions", [])

        except Exception as e:
            print(f"Template suggestion error: {e}")
            self._log_suggestion(email_data, [], error=str(e))
            return []

    def create_from_sent(self, email_data):
        """
        Analyze a sent email and save it as a reusable template.

        Args:
            email_data: Sent email data

        Returns:
            Created template dict
        """
        subject = email_data.get("subject", "Sent Reply")
        body = email_data.get("body_text", "")

        # Simple heuristic: identify variables based on common patterns
        variables = []
        if "{{" in body or "{{" in subject:
            # Already has template variables
            import re
            vars_found = re.findall(r"\{\{(\w+)\}\}", subject + body)
            variables = list(set(vars_found))

        template = self.add_template(
            name=f"Custom: {subject[:40]}",
            category="custom",
            subject=f"Re: {{{{original_subject}}}}",
            body=body,
            variables=variables,
        )

        return template

    def _log_suggestion(self, email_data, suggestions, error=None):
        """Log template suggestion attempt."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "message_id": email_data.get("id", ""),
            "sender": email_data.get("sender_email", ""),
            "subject": email_data.get("subject", ""),
            "suggestions_count": len(suggestions),
            "error": error,
        }
        with open(self.suggestion_log, "a") as f:
            f.write(json.dumps(log_entry) + "\n")


def main():
    parser = argparse.ArgumentParser(description="MAILMAN Template Library")
    parser.add_argument("--list", action="store_true", help="List all templates")
    parser.add_argument("--category", type=str, help="Filter by category")
    parser.add_argument("--add", action="store_true", help="Add new template (interactive)")
    parser.add_argument("--render", type=str, help="Render template by ID")
    parser.add_argument("--suggest", type=str, help="Suggest templates for message ID")
    args = parser.parse_args()

    library = TemplateLibrary()

    if args.list:
        templates = library.list_templates(category=args.category)
        if not templates:
            print("No templates found.")
        else:
            print(f"EMAIL TEMPLATES ({len(templates)}):\n")
            current_category = None
            for tmpl in templates:
                if tmpl.get("category") != current_category:
                    current_category = tmpl.get("category")
                    print(f"\n{current_category.upper()}:")
                print(f"  [{tmpl['id']}] {tmpl['name']}")
                if tmpl.get("variables"):
                    print(f"      Variables: {', '.join(tmpl['variables'])}")

    elif args.add:
        print("Add New Template")
        print("-" * 40)
        name = input("Template name: ").strip()
        category = input("Category (meetings/follow-ups/responses/etc): ").strip()
        subject = input("Subject template (use {{variable}}): ").strip()
        print("Body template (end with 'END' on new line):")
        body_lines = []
        while True:
            line = input()
            if line.strip() == "END":
                break
            body_lines.append(line)
        body = "\n".join(body_lines)

        template = library.add_template(name, category, subject, body)
        print(f"✓ Created template: {template['id']}")

    elif args.render:
        template = library.get_template(args.render)
        if template:
            print(f"Template: {template['name']}")
            print(f"Variables needed: {', '.join(template.get('variables', []))}")
            print("\nProvide values for each variable:")
            context = {}
            for var in template.get("variables", []):
                context[var] = input(f"  {var}: ").strip()

            rendered = library.render_template(args.render, context)
            print("\nRENDERED TEMPLATE:")
            print(f"Subject: {rendered['subject']}")
            print(f"Body:\n{rendered['body']}")
        else:
            print(f"Template not found: {args.render}")

    elif args.suggest:
        print(f"To suggest templates for {args.suggest}, use:")
        print("  library.suggest_template(email_data, classification)")

    else:
        print("Use --help for options")


if __name__ == "__main__":
    main()
