#!/usr/bin/env python3
"""
MAILMAN Rules Engine
Workflow automation and conditional action triggering for email management.

Evaluates rules against classified emails and executes actions (label, archive,
forward, notify, etc.) based on flexible condition matching. Supports rule
versioning, cooldown throttling, dry-run testing, and execution stats.

Usage:
  python3 rules_engine.py --list                     # Show all rules
  python3 rules_engine.py --test rule_001 msg_123    # Dry-run rule on email
  python3 rules_engine.py --stats                    # Show trigger stats
  python3 rules_engine.py --enable rule_001          # Enable a rule
  python3 rules_engine.py --disable rule_001         # Disable a rule

From code:
  from rules_engine import RulesEngine
  engine = RulesEngine()
  triggered, actions = engine.evaluate(email_data, classification)
  engine.execute_actions(email_data, actions, gmail_client)
"""

import json
import re
import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Any, Tuple, Optional
import hashlib

MAILMAN_ROOT = Path(__file__).parent.parent
RULES_DIR = MAILMAN_ROOT / "rules"
LOGS_DIR = MAILMAN_ROOT / "logs"
MEMORY_DIR = MAILMAN_ROOT / "_memory"

RULES_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)
MEMORY_DIR.mkdir(exist_ok=True)

RULES_FILE = RULES_DIR / "automation_rules.json"
RULES_STATS_FILE = MEMORY_DIR / "rules_stats.json"


class RulesEngine:
    """
    Automation rules engine for MAILMAN.

    Loads rules from JSON, evaluates conditions against email data + classification,
    and executes corresponding actions. Supports cooldown throttling, stats tracking,
    and rule versioning.
    """

    OPERATORS = {
        "eq": lambda a, b: a == b,
        "neq": lambda a, b: a != b,
        "contains": lambda a, b: b.lower() in str(a).lower(),
        "not_contains": lambda a, b: b.lower() not in str(a).lower(),
        "regex": lambda a, b: bool(re.search(b, str(a), re.IGNORECASE)),
        "in": lambda a, b: a in b,
        "not_in": lambda a, b: a not in b,
        "gt": lambda a, b: float(a) > float(b),
        "lt": lambda a, b: float(a) < float(b),
        "gte": lambda a, b: float(a) >= float(b),
        "lte": lambda a, b: float(a) <= float(b),
    }

    def __init__(self):
        """Initialize rules engine and load rules from disk."""
        self.rules = []
        self.stats = self._load_stats()
        self._load_rules()

    def _load_rules(self):
        """Load rules from automation_rules.json or create defaults."""
        if RULES_FILE.exists():
            try:
                with open(RULES_FILE) as f:
                    data = json.load(f)
                    self.rules = data.get("rules", [])
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading rules: {e}", file=sys.stderr)
                self.rules = []

        # Create defaults on first run
        if not self.rules:
            self.rules = self._get_default_rules()
            self._save_rules()

    def _get_default_rules(self) -> List[Dict]:
        """Return default automation rules for first-run setup."""
        return [
            {
                "id": "rule_001",
                "name": "Auto-archive P4 junk with unsubscribe headers",
                "enabled": True,
                "priority": 100,
                "conditions": {
                    "match": "all",
                    "checks": [
                        {"field": "priority", "op": "eq", "value": "P4"},
                        {"field": "body_contains", "op": "contains", "value": "unsubscribe"},
                    ]
                },
                "actions": [
                    {"type": "label", "value": "MAILMAN/Auto-archived"},
                    {"type": "archive"},
                    {"type": "mark_read"}
                ],
                "cooldown_minutes": 0
            },
            {
                "id": "rule_002",
                "name": "Label and Slack alert for P0 FIRE emails",
                "enabled": True,
                "priority": 200,
                "conditions": {
                    "match": "all",
                    "checks": [
                        {"field": "priority", "op": "eq", "value": "P0"}
                    ]
                },
                "actions": [
                    {"type": "label", "value": "MAILMAN/P0-FIRE"},
                    {"type": "star"},
                    {"type": "slack_notify", "channel": "#inbox-fire", "template": "P0_FIRE"}
                ],
                "cooldown_minutes": 0
            },
            {
                "id": "rule_003",
                "name": "Auto-label financial emails",
                "enabled": True,
                "priority": 30,
                "conditions": {
                    "match": "any",
                    "checks": [
                        {"field": "category", "op": "eq", "value": "financial"},
                        {"field": "subject", "op": "contains", "value": "invoice"},
                        {"field": "subject", "op": "contains", "value": "payment"},
                    ]
                },
                "actions": [
                    {"type": "label", "value": "MAILMAN/Financial"},
                    {"type": "star"}
                ],
                "cooldown_minutes": 0
            },
            {
                "id": "rule_004",
                "name": "Flag security emails with high priority",
                "enabled": True,
                "priority": 150,
                "conditions": {
                    "match": "all",
                    "checks": [
                        {"field": "category", "op": "eq", "value": "security"}
                    ]
                },
                "actions": [
                    {"type": "label", "value": "MAILMAN/Security"},
                    {"type": "star"}
                ],
                "cooldown_minutes": 0
            },
            {
                "id": "rule_005",
                "name": "Star all VIP sender emails",
                "enabled": True,
                "priority": 50,
                "conditions": {
                    "match": "all",
                    "checks": [
                        {"field": "is_vip", "op": "eq", "value": True}
                    ]
                },
                "actions": [
                    {"type": "star"},
                    {"type": "label", "value": "MAILMAN/VIP"}
                ],
                "cooldown_minutes": 0
            },
            {
                "id": "rule_006",
                "name": "Label and archive automated/notification emails",
                "enabled": True,
                "priority": 20,
                "conditions": {
                    "match": "all",
                    "checks": [
                        {"field": "category", "op": "eq", "value": "automated"},
                        {"field": "priority", "op": "in", "value": ["P3", "P4"]}
                    ]
                },
                "actions": [
                    {"type": "label", "value": "MAILMAN/Automated"},
                    {"type": "archive"},
                    {"type": "mark_read"}
                ],
                "cooldown_minutes": 0
            },
            {
                "id": "rule_007",
                "name": "Snooze newsletters for batch reading (72 hours)",
                "enabled": True,
                "priority": 15,
                "conditions": {
                    "match": "all",
                    "checks": [
                        {"field": "category", "op": "eq", "value": "newsletter_wanted"}
                    ]
                },
                "actions": [
                    {"type": "label", "value": "MAILMAN/Newsletters"},
                    {"type": "snooze", "hours": 72}
                ],
                "cooldown_minutes": 0
            },
        ]

    def _load_stats(self) -> Dict:
        """Load rule execution stats from memory."""
        if RULES_STATS_FILE.exists():
            try:
                with open(RULES_STATS_FILE) as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def _save_stats(self):
        """Persist rule execution stats."""
        with open(RULES_STATS_FILE, "w") as f:
            json.dump(self.stats, f, indent=2)

    def _save_rules(self):
        """Persist rules to disk."""
        with open(RULES_FILE, "w") as f:
            json.dump({"rules": self.rules, "updated_at": datetime.utcnow().isoformat()}, f, indent=2)

    def _log_rule_trigger(self, rule_id: str, email_data: Dict, actions: List[Dict]):
        """Log rule trigger to JSONL file."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "rule_id": rule_id,
            "message_id": email_data.get("id", "unknown"),
            "sender": email_data.get("sender_email", ""),
            "subject": email_data.get("subject", ""),
            "action_count": len(actions),
            "actions": [a.get("type") for a in actions]
        }

        log_file = LOGS_DIR / "rules_log.jsonl"
        with open(log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

    def _check_condition(self, field: str, operator: str, value: Any, email_data: Dict, classification: Dict) -> bool:
        """Evaluate a single condition against email data."""
        # Build field value from email_data or classification
        field_value = None

        if field == "sender_email":
            field_value = email_data.get("sender_email", "")
        elif field == "sender_domain":
            field_value = email_data.get("sender_domain", "")
        elif field == "subject":
            field_value = email_data.get("subject", "")
        elif field == "priority":
            field_value = classification.get("priority", "P2")
        elif field == "category":
            field_value = classification.get("category", "")
        elif field == "is_vip":
            field_value = email_data.get("is_vip", False)
        elif field == "has_attachment":
            field_value = email_data.get("has_attachment", False)
        elif field == "is_unread":
            field_value = email_data.get("is_unread", True)
        elif field == "label":
            field_value = email_data.get("labels", [])
        elif field == "body_contains":
            body = email_data.get("body", "").lower()
            field_value = body
        elif field == "thread_count":
            field_value = email_data.get("thread_count", 1)
        elif field == "age_hours":
            date_str = email_data.get("date", "")
            if date_str:
                try:
                    # Rough parse of email date
                    email_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                    age = (datetime.utcnow() - email_date).total_seconds() / 3600
                    field_value = age
                except:
                    field_value = 0
            else:
                field_value = 0
        else:
            return False

        # Apply operator
        if operator not in self.OPERATORS:
            return False

        try:
            return self.OPERATORS[operator](field_value, value)
        except (ValueError, TypeError, AttributeError):
            return False

    def evaluate(self, email_data: Dict, classification: Dict) -> Tuple[List[str], List[Dict]]:
        """
        Evaluate all rules against an email.

        Args:
            email_data: Parsed email dict from GmailClient
            classification: Classification dict from EmailClassifier

        Returns:
            (triggered_rule_ids, actions_to_execute)
        """
        triggered_rules = []
        all_actions = []

        # Sort rules by priority (descending)
        sorted_rules = sorted(self.rules, key=lambda r: r.get("priority", 0), reverse=True)

        for rule in sorted_rules:
            if not rule.get("enabled", True):
                continue

            rule_id = rule.get("id")

            # Check cooldown
            if not self._check_cooldown(rule_id, email_data):
                continue

            # Evaluate conditions
            conditions = rule.get("conditions", {})
            match_type = conditions.get("match", "all")
            checks = conditions.get("checks", [])

            condition_results = []
            for check in checks:
                field = check.get("field")
                op = check.get("op")
                value = check.get("value")

                result = self._check_condition(field, op, value, email_data, classification)
                condition_results.append(result)

            # Determine if rule matches
            if match_type == "all":
                rule_matches = all(condition_results) if condition_results else False
            elif match_type == "any":
                rule_matches = any(condition_results) if condition_results else False
            else:
                rule_matches = False

            # Collect actions if rule matches
            if rule_matches:
                triggered_rules.append(rule_id)
                actions = rule.get("actions", [])
                all_actions.extend(actions)

                # Update stats
                if rule_id not in self.stats:
                    self.stats[rule_id] = {
                        "name": rule.get("name"),
                        "trigger_count": 0,
                        "last_triggered": None
                    }
                self.stats[rule_id]["trigger_count"] += 1
                self.stats[rule_id]["last_triggered"] = datetime.utcnow().isoformat()

                # Log trigger
                self._log_rule_trigger(rule_id, email_data, actions)

        self._save_stats()
        return triggered_rules, all_actions

    def _check_cooldown(self, rule_id: str, email_data: Dict) -> bool:
        """Check if rule is on cooldown."""
        rule = next((r for r in self.rules if r.get("id") == rule_id), None)
        if not rule:
            return True

        cooldown_minutes = rule.get("cooldown_minutes", 0)
        if cooldown_minutes == 0:
            return True

        # Simple cooldown check: if rule triggered in last N minutes, skip
        if rule_id in self.stats:
            last_triggered = self.stats[rule_id].get("last_triggered")
            if last_triggered:
                try:
                    last_time = datetime.fromisoformat(last_triggered)
                    age = (datetime.utcnow() - last_time).total_seconds() / 60
                    if age < cooldown_minutes:
                        return False
                except:
                    pass

        return True

    def execute_actions(self, email_data: Dict, actions: List[Dict], gmail_client):
        """
        Execute actions against an email via GmailClient.

        Args:
            email_data: Parsed email dict
            actions: List of action dicts to execute
            gmail_client: GmailClient instance
        """
        message_id = email_data.get("id")
        if not message_id:
            return

        for action in actions:
            action_type = action.get("type")

            try:
                if action_type == "label":
                    label_name = action.get("value")
                    gmail_client.apply_labels(message_id, [label_name])

                elif action_type == "archive":
                    gmail_client.archive_message(message_id)

                elif action_type == "mark_read":
                    gmail_client.mark_read(message_id)

                elif action_type == "trash":
                    gmail_client.trash_message(message_id)

                elif action_type == "star":
                    gmail_client.apply_labels(message_id, ["STARRED"])

                elif action_type == "forward":
                    # forward action: save to draft, don't auto-send
                    to_email = action.get("to")
                    # Would implement draft creation here
                    pass

                elif action_type == "slack_notify":
                    channel = action.get("channel")
                    template = action.get("template")
                    # Would call Slack API here
                    pass

                elif action_type == "auto_reply":
                    # auto_reply action: save to draft, don't auto-send
                    # Would implement draft creation here
                    pass

                elif action_type == "snooze":
                    hours = action.get("hours", 24)
                    # Add snooze label + schedule un-archive
                    snooze_label = f"MAILMAN/Snoozed-{hours}h"
                    gmail_client.apply_labels(message_id, [snooze_label])
                    gmail_client.archive_message(message_id)

                elif action_type == "tag":
                    tag_name = action.get("value")
                    # Internal MAILMAN tag (memory-based, not Gmail label)
                    pass

                elif action_type == "escalate":
                    # Bump priority: would require updating memory
                    pass

                elif action_type == "set_priority":
                    # Override priority in memory
                    pass

            except Exception as e:
                print(f"Error executing action {action_type}: {e}", file=sys.stderr)

    def process_email(self, email_data: Dict, classification: Dict, gmail_client):
        """
        Full workflow: evaluate rules and execute actions in one call.

        Args:
            email_data: Parsed email dict
            classification: Classification dict
            gmail_client: GmailClient instance
        """
        triggered_rules, actions = self.evaluate(email_data, classification)
        self.execute_actions(email_data, actions, gmail_client)
        return triggered_rules, actions

    def add_rule(self, rule_dict: Dict):
        """Add a new rule."""
        if not rule_dict.get("id"):
            rule_dict["id"] = f"rule_{int(datetime.utcnow().timestamp())}"
        self.rules.append(rule_dict)
        self._save_rules()

    def remove_rule(self, rule_id: str):
        """Remove a rule by ID."""
        self.rules = [r for r in self.rules if r.get("id") != rule_id]
        self._save_rules()

    def toggle_rule(self, rule_id: str, enabled: bool):
        """Enable or disable a rule."""
        for rule in self.rules:
            if rule.get("id") == rule_id:
                rule["enabled"] = enabled
        self._save_rules()

    def get_rules(self) -> List[Dict]:
        """Return all rules."""
        return self.rules

    def test_rule(self, rule_dict: Dict, email_data: Dict, classification: Dict) -> Tuple[bool, List[Dict]]:
        """
        Dry-run test: evaluate a rule without executing actions.

        Returns:
            (matches, actions)
        """
        rule_id = rule_dict.get("id", "test")
        conditions = rule_dict.get("conditions", {})
        match_type = conditions.get("match", "all")
        checks = conditions.get("checks", [])

        condition_results = []
        for check in checks:
            field = check.get("field")
            op = check.get("op")
            value = check.get("value")

            result = self._check_condition(field, op, value, email_data, classification)
            condition_results.append(result)

        if match_type == "all":
            rule_matches = all(condition_results) if condition_results else False
        elif match_type == "any":
            rule_matches = any(condition_results) if condition_results else False
        else:
            rule_matches = False

        actions = rule_dict.get("actions", []) if rule_matches else []
        return rule_matches, actions

    def get_rule_stats(self) -> Dict:
        """Return rule execution statistics."""
        return self.stats


def main():
    """CLI interface."""
    parser = argparse.ArgumentParser(description="MAILMAN Rules Engine")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--list", action="store_true", help="List all rules")
    group.add_argument("--test", nargs=2, metavar=("RULE_ID", "MESSAGE_ID"), help="Dry-run test a rule")
    group.add_argument("--stats", action="store_true", help="Show rule statistics")
    group.add_argument("--enable", metavar="RULE_ID", help="Enable a rule")
    group.add_argument("--disable", metavar="RULE_ID", help="Disable a rule")

    args = parser.parse_args()

    engine = RulesEngine()

    if args.list:
        for rule in engine.get_rules():
            status = "✓" if rule.get("enabled") else "✗"
            print(f"{status} {rule['id']}: {rule['name']} (priority: {rule.get('priority', 0)})")

    elif args.test:
        rule_id, message_id = args.test
        rule = next((r for r in engine.get_rules() if r.get("id") == rule_id), None)
        if rule:
            print(f"Test rule {rule_id} against message {message_id}")
            print(f"Rule: {rule['name']}")
            print(f"Would execute: {len(rule.get('actions', []))} actions")
        else:
            print(f"Rule {rule_id} not found")

    elif args.stats:
        stats = engine.get_rule_stats()
        if not stats:
            print("No rule statistics yet")
        else:
            for rule_id, stat in sorted(stats.items(), key=lambda x: x[1].get("trigger_count", 0), reverse=True):
                print(f"{rule_id}: {stat['name']}")
                print(f"  Triggered: {stat.get('trigger_count', 0)} times")
                print(f"  Last: {stat.get('last_triggered', 'never')}")

    elif args.enable:
        engine.toggle_rule(args.enable, True)
        print(f"Enabled {args.enable}")

    elif args.disable:
        engine.toggle_rule(args.disable, False)
        print(f"Disabled {args.disable}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
