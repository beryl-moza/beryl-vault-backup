#!/usr/bin/env python3
"""
MAILMAN Task Extractor
Converts classified P1 ACTION emails into structured tasks with deadlines.

Usage:
  python3 task_extractor.py --extract <message_id>  # Extract tasks from email
  python3 task_extractor.py --list                  # List all open tasks
  python3 task_extractor.py --today                 # Show tasks due today
  python3 task_extractor.py --overdue               # Show overdue tasks
  python3 task_extractor.py --complete <task_id>    # Mark task as complete
"""

import json
import argparse
import sys
from datetime import datetime, timedelta
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


TASK_EXTRACTION_PROMPT = """You are MAILMAN's task extraction system. Analyze this email and extract structured tasks.

EMAIL METADATA:
Subject: {subject}
From: {sender_name} <{sender_email}>
Date: {date}
Body (first 2000 chars): {body_preview}

CLASSIFICATION:
Priority: {priority}
Category: {category}
Action Items: {action_items}
Needs Response: {needs_response}

Extract actionable tasks from this email. For each task, return ONLY valid JSON:
{{
  "tasks": [
    {{
      "title": "Brief, actionable title (e.g., 'Review Board Consent document')",
      "description": "Full description with context from email",
      "deadline": "ISO 8601 datetime if mentioned, or inferred from urgency, or null if no deadline",
      "assignee": "beryl or other person mentioned",
      "priority": "P0|P1|P2|P3",
      "tags": ["category", "tags"]
    }}
  ]
}}

Rules:
- Extract only clear, actionable tasks
- If no deadline is mentioned, use:
  - "urgent/asap" keywords → tomorrow by 5pm
  - "P1 ACTION" → today by 5pm
  - "by EOD" → today by 5pm
  - "by Friday" → this Friday by 5pm
  - "meeting request" → meeting date at meeting time
  - No deadline → null (backlog)
- Title should be concise (50 chars max)
- Include sender context in description
- Set assignee to "beryl" unless someone else is clearly responsible
- Use current date reference: {current_date}
"""


class TaskExtractor:
    """
    Extracts structured tasks from classified emails with AI assistance.
    """

    def __init__(self):
        self.client = anthropic.Anthropic()
        self.tasks_file = MEMORY_DIR / "tasks.json"
        self.extraction_log = LOGS_DIR / "task_extraction_log.jsonl"
        self._ensure_tasks_file()

    def _ensure_tasks_file(self):
        """Ensure tasks.json exists with proper structure."""
        if not self.tasks_file.exists():
            self.tasks_file.write_text(json.dumps({"tasks": []}, indent=2))

    def _load_tasks(self):
        """Load all tasks from disk."""
        try:
            with open(self.tasks_file) as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {"tasks": []}

    def _save_tasks(self, data):
        """Save tasks to disk."""
        with open(self.tasks_file, "w") as f:
            json.dump(data, f, indent=2)

    def extract_tasks(self, email_data, classification):
        """
        Extract tasks from an email and its classification.

        Args:
            email_data: Parsed email dict from GmailClient
            classification: Classification result from EmailClassifier

        Returns:
            List of extracted and created tasks
        """
        body_preview = (email_data.get("body_text", "") or email_data.get("snippet", ""))[:2000]

        prompt = TASK_EXTRACTION_PROMPT.format(
            subject=email_data.get("subject", ""),
            sender_name=email_data.get("sender_name", ""),
            sender_email=email_data.get("sender_email", ""),
            date=email_data.get("date", ""),
            body_preview=body_preview,
            priority=classification.get("priority", "P3"),
            category=classification.get("category", ""),
            action_items=", ".join(classification.get("action_items", [])),
            needs_response=classification.get("needs_response", False),
            current_date=datetime.utcnow().isoformat(),
        )

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-5-20250514",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}],
            )
            result_text = response.content[0].text.strip()

            # Parse JSON from response (handle markdown code blocks)
            if result_text.startswith("```"):
                result_text = result_text.split("\n", 1)[1].rsplit("```", 1)[0]

            extracted = json.loads(result_text)
            created_tasks = []

            for task_dict in extracted.get("tasks", []):
                created = self.create_task(
                    task_dict,
                    source_email_id=email_data.get("id", ""),
                    source_thread_id=email_data.get("thread_id", ""),
                )
                created_tasks.append(created)
                self._log_extraction(email_data, created)

            return created_tasks

        except Exception as e:
            print(f"Task extraction error: {e}")
            self._log_extraction(email_data, None, error=str(e))
            return []

    def create_task(self, task_dict, source_email_id="", source_thread_id=""):
        """
        Create a new task and save it to tasks.json.

        Args:
            task_dict: Task data dict with title, description, deadline, etc.
            source_email_id: Associated email message ID
            source_thread_id: Associated thread ID

        Returns:
            Created task dict with assigned ID
        """
        task_id = f"task_{uuid4().hex[:8]}"

        task = {
            "id": task_id,
            "title": task_dict.get("title", "Untitled Task"),
            "description": task_dict.get("description", ""),
            "deadline": task_dict.get("deadline"),
            "assignee": task_dict.get("assignee", "beryl"),
            "priority": task_dict.get("priority", "P3"),
            "status": "open",
            "source_email_id": source_email_id,
            "source_thread_id": source_thread_id,
            "created_at": datetime.utcnow().isoformat(),
            "completed_at": None,
            "tags": task_dict.get("tags", []),
        }

        data = self._load_tasks()
        data["tasks"].append(task)
        self._save_tasks(data)

        return task

    def list_tasks(self, status="open", priority=None):
        """
        List tasks filtered by status and priority.

        Args:
            status: "open", "completed", or "all"
            priority: Filter by priority (P0, P1, etc.) or None for all

        Returns:
            List of filtered task dicts
        """
        data = self._load_tasks()
        tasks = data.get("tasks", [])

        # Filter by status
        if status == "open":
            tasks = [t for t in tasks if t["status"] == "open"]
        elif status == "completed":
            tasks = [t for t in tasks if t["status"] == "completed"]

        # Filter by priority
        if priority:
            tasks = [t for t in tasks if t.get("priority") == priority]

        return sorted(tasks, key=lambda t: (t.get("deadline") or "z", t.get("priority", "P3")))

    def complete_task(self, task_id):
        """
        Mark a task as completed.

        Args:
            task_id: ID of task to complete

        Returns:
            Updated task dict or None if not found
        """
        data = self._load_tasks()
        for task in data.get("tasks", []):
            if task["id"] == task_id:
                task["status"] = "completed"
                task["completed_at"] = datetime.utcnow().isoformat()
                self._save_tasks(data)
                return task
        return None

    def get_overdue(self):
        """
        Get all overdue tasks (past deadline and still open).

        Returns:
            List of overdue task dicts
        """
        now = datetime.utcnow()
        overdue = []

        for task in self.list_tasks(status="open"):
            deadline_str = task.get("deadline")
            if deadline_str:
                try:
                    deadline = datetime.fromisoformat(deadline_str.replace("Z", "+00:00"))
                    if deadline < now:
                        overdue.append(task)
                except ValueError:
                    pass

        return sorted(overdue, key=lambda t: t.get("deadline", ""))

    def get_today(self):
        """
        Get all tasks due today.

        Returns:
            List of task dicts due today
        """
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)

        due_today = []
        for task in self.list_tasks(status="open"):
            deadline_str = task.get("deadline")
            if deadline_str:
                try:
                    deadline = datetime.fromisoformat(deadline_str.replace("Z", "+00:00"))
                    if today_start <= deadline < today_end:
                        due_today.append(task)
                except ValueError:
                    pass

        return sorted(due_today, key=lambda t: t.get("deadline", ""))

    def format_task_summary(self):
        """
        Format all open tasks as a readable summary string.

        Returns:
            Formatted task summary for digest
        """
        tasks = self.list_tasks(status="open")

        if not tasks:
            return "No open tasks."

        lines = ["OPEN TASKS\n" + "=" * 60]

        # Group by priority
        for priority in ["P0", "P1", "P2", "P3"]:
            priority_tasks = [t for t in tasks if t.get("priority") == priority]
            if priority_tasks:
                lines.append(f"\n{priority}:")
                for task in priority_tasks:
                    deadline_str = ""
                    if task.get("deadline"):
                        deadline_str = f" [Due: {task['deadline'][:10]}]"
                    lines.append(f"  • {task['title']}{deadline_str}")

        overdue = self.get_overdue()
        if overdue:
            lines.append(f"\n⚠️  OVERDUE ({len(overdue)}):")
            for task in overdue:
                lines.append(f"  • {task['title']} [Was due: {task['deadline'][:10]}]")

        return "\n".join(lines)

    def link_task_to_email(self, task_id, message_id):
        """
        Create bidirectional link between task and email.
        (Stores reference in task; optionally in email metadata)

        Args:
            task_id: Task ID
            message_id: Email message ID

        Returns:
            Updated task dict or None if task not found
        """
        data = self._load_tasks()
        for task in data.get("tasks", []):
            if task["id"] == task_id:
                if "linked_emails" not in task:
                    task["linked_emails"] = []
                if message_id not in task["linked_emails"]:
                    task["linked_emails"].append(message_id)
                self._save_tasks(data)
                return task
        return None

    def _log_extraction(self, email_data, task, error=None):
        """Log task extraction attempt."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "message_id": email_data.get("id", ""),
            "sender": email_data.get("sender_email", ""),
            "subject": email_data.get("subject", ""),
            "task_id": task["id"] if task else None,
            "task_title": task["title"] if task else None,
            "error": error,
        }
        with open(self.extraction_log, "a") as f:
            f.write(json.dumps(log_entry) + "\n")


def main():
    parser = argparse.ArgumentParser(description="MAILMAN Task Extractor")
    parser.add_argument("--extract", type=str, help="Extract tasks from message ID")
    parser.add_argument("--list", action="store_true", help="List all open tasks")
    parser.add_argument("--today", action="store_true", help="Show tasks due today")
    parser.add_argument("--overdue", action="store_true", help="Show overdue tasks")
    parser.add_argument("--complete", type=str, help="Mark task as complete by ID")
    args = parser.parse_args()

    extractor = TaskExtractor()

    if args.list:
        tasks = extractor.list_tasks()
        if not tasks:
            print("No open tasks.")
        else:
            print(f"OPEN TASKS ({len(tasks)}):\n")
            for task in tasks:
                deadline = f" [Due: {task.get('deadline', 'No deadline')[:10]}]" if task.get("deadline") else ""
                print(f"  [{task['id']}] {task['title']}{deadline}")
                print(f"      Priority: {task['priority']} | Assignee: {task['assignee']}")

    elif args.today:
        tasks = extractor.get_today()
        if not tasks:
            print("No tasks due today.")
        else:
            print(f"TASKS DUE TODAY ({len(tasks)}):\n")
            for task in tasks:
                print(f"  [{task['id']}] {task['title']} [Due: {task['deadline']}]")
                print(f"      {task['description'][:80]}...")

    elif args.overdue:
        tasks = extractor.get_overdue()
        if not tasks:
            print("No overdue tasks.")
        else:
            print(f"⚠️  OVERDUE TASKS ({len(tasks)}):\n")
            for task in tasks:
                print(f"  [{task['id']}] {task['title']} [Was due: {task['deadline'][:10]}]")
                print(f"      Priority: {task['priority']}")

    elif args.complete:
        completed = extractor.complete_task(args.complete)
        if completed:
            print(f"✓ Completed: {completed['title']}")
        else:
            print(f"Task not found: {args.complete}")

    elif args.extract:
        print(f"To extract tasks from {args.extract}, use classifier first to get classification")
        print("Then: extractor.extract_tasks(email_data, classification)")

    else:
        print("Use --help for options")


if __name__ == "__main__":
    main()
