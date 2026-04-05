#!/usr/bin/env python3
"""
MAILMAN Gmail Client
Wraps the Gmail API for reading, labeling, archiving, and managing emails.

Usage:
  from gmail_client import GmailClient
  client = GmailClient("gmail_personal")
  emails = client.fetch_unread(max_results=50)
"""

import base64
import email
import json
import re
from datetime import datetime, timedelta
from pathlib import Path

try:
    from googleapiclient.discovery import build
except ImportError:
    print("Missing: pip install google-api-python-client --break-system-packages")
    raise

from auth import AccountManager


class GmailClient:
    """
    Gmail API wrapper for MAILMAN operations.
    One instance per account.
    """

    def __init__(self, account_id):
        self.account_id = account_id
        self.manager = AccountManager()
        self.creds = self.manager.get_credentials(account_id)
        if not self.creds:
            raise RuntimeError(f"No valid credentials for '{account_id}'")
        self.service = build("gmail", "v1", credentials=self.creds)
        self.user_id = "me"

    def fetch_messages(self, query="", max_results=100, include_body=True):
        """
        Fetch messages matching a Gmail search query.

        Args:
            query: Gmail search syntax (e.g., "is:unread", "from:boss@company.com")
            max_results: Maximum messages to return
            include_body: Whether to fetch full message body

        Returns:
            List of parsed message dicts
        """
        results = self.service.users().messages().list(
            userId=self.user_id,
            q=query,
            maxResults=max_results,
        ).execute()

        messages = results.get("messages", [])
        parsed = []

        for msg_stub in messages:
            msg = self.service.users().messages().get(
                userId=self.user_id,
                id=msg_stub["id"],
                format="full" if include_body else "metadata",
            ).execute()
            parsed.append(self._parse_message(msg, include_body))

        return parsed

    def fetch_unread(self, max_results=50):
        """Fetch unread messages."""
        return self.fetch_messages(query="is:unread", max_results=max_results)

    def fetch_since(self, hours=24, max_results=200):
        """Fetch messages from the last N hours."""
        since = (datetime.utcnow() - timedelta(hours=hours)).strftime("%Y/%m/%d")
        return self.fetch_messages(query=f"after:{since}", max_results=max_results)

    def _parse_message(self, msg, include_body=True):
        """Parse a raw Gmail API message into a clean dict."""
        headers = {h["name"].lower(): h["value"] for h in msg["payload"]["headers"]}

        parsed = {
            "id": msg["id"],
            "thread_id": msg["threadId"],
            "account": self.account_id,
            "from": headers.get("from", ""),
            "to": headers.get("to", ""),
            "cc": headers.get("cc", ""),
            "subject": headers.get("subject", ""),
            "date": headers.get("date", ""),
            "message_id": headers.get("message-id", ""),
            "in_reply_to": headers.get("in-reply-to", ""),
            "references": headers.get("references", ""),
            "labels": msg.get("labelIds", []),
            "snippet": msg.get("snippet", ""),
            "size_estimate": msg.get("sizeEstimate", 0),
            # Unsubscribe headers
            "list_unsubscribe": headers.get("list-unsubscribe", ""),
            "list_unsubscribe_post": headers.get("list-unsubscribe-post", ""),
            # Authentication results
            "authentication_results": headers.get("authentication-results", ""),
            "dkim_signature": headers.get("dkim-signature", ""),
            # Parsed sender info
            "sender_email": self._extract_email(headers.get("from", "")),
            "sender_name": self._extract_name(headers.get("from", "")),
            "sender_domain": self._extract_domain(headers.get("from", "")),
        }

        if include_body:
            parsed["body_text"] = self._extract_body(msg["payload"], "text/plain")
            parsed["body_html"] = self._extract_body(msg["payload"], "text/html")

        return parsed

    def _extract_body(self, payload, mime_type):
        """Extract body content of specified MIME type from message payload."""
        if payload.get("mimeType") == mime_type:
            data = payload.get("body", {}).get("data", "")
            if data:
                return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")

        parts = payload.get("parts", [])
        for part in parts:
            result = self._extract_body(part, mime_type)
            if result:
                return result
        return ""

    def _extract_email(self, from_header):
        """Extract email address from From header."""
        match = re.search(r"<(.+?)>", from_header)
        if match:
            return match.group(1).lower()
        if "@" in from_header:
            return from_header.strip().lower()
        return ""

    def _extract_name(self, from_header):
        """Extract display name from From header."""
        match = re.search(r'^"?(.+?)"?\s*<', from_header)
        if match:
            return match.group(1).strip().strip('"')
        return ""

    def _extract_domain(self, from_header):
        """Extract domain from sender email."""
        email_addr = self._extract_email(from_header)
        if "@" in email_addr:
            return email_addr.split("@")[1]
        return ""

    # --- Label Operations ---

    def create_label(self, label_name, bg_color=None, text_color=None):
        """Create a Gmail label if it doesn't exist."""
        existing = self._get_label_id(label_name)
        if existing:
            return existing

        body = {"name": label_name, "labelListVisibility": "labelShow", "messageListVisibility": "show"}
        if bg_color and text_color:
            body["color"] = {"backgroundColor": bg_color, "textColor": text_color}

        result = self.service.users().labels().create(userId=self.user_id, body=body).execute()
        return result["id"]

    def _get_label_id(self, label_name):
        """Get label ID by name."""
        labels = self.service.users().labels().list(userId=self.user_id).execute()
        for label in labels.get("labels", []):
            if label["name"] == label_name:
                return label["id"]
        return None

    def apply_labels(self, message_id, label_names):
        """Apply labels to a message."""
        label_ids = []
        for name in label_names:
            lid = self._get_label_id(name)
            if not lid:
                lid = self.create_label(name)
            label_ids.append(lid)

        if label_ids:
            self.service.users().messages().modify(
                userId=self.user_id,
                id=message_id,
                body={"addLabelIds": label_ids},
            ).execute()

    def archive_message(self, message_id):
        """Remove INBOX label (archive) from a message."""
        self.service.users().messages().modify(
            userId=self.user_id,
            id=message_id,
            body={"removeLabelIds": ["INBOX"]},
        ).execute()

    def mark_read(self, message_id):
        """Mark a message as read."""
        self.service.users().messages().modify(
            userId=self.user_id,
            id=message_id,
            body={"removeLabelIds": ["UNREAD"]},
        ).execute()

    def trash_message(self, message_id):
        """Move a message to trash."""
        self.service.users().messages().trash(userId=self.user_id, id=message_id).execute()

    # --- Thread Operations ---

    def get_thread(self, thread_id):
        """Fetch full thread with all messages."""
        thread = self.service.users().threads().get(
            userId=self.user_id, id=thread_id, format="full"
        ).execute()
        messages = [self._parse_message(msg) for msg in thread.get("messages", [])]
        return {
            "thread_id": thread_id,
            "message_count": len(messages),
            "messages": messages,
            "participants": list(set(m["sender_email"] for m in messages if m["sender_email"])),
        }

    def get_thread_count(self, thread_id):
        """Get number of messages in a thread."""
        thread = self.service.users().threads().get(
            userId=self.user_id, id=thread_id, format="minimal"
        ).execute()
        return len(thread.get("messages", []))

    # --- Search Helpers ---

    def search_from(self, sender_email, max_results=20):
        """Search emails from a specific sender."""
        return self.fetch_messages(query=f"from:{sender_email}", max_results=max_results)

    def search_subject(self, subject_query, max_results=20):
        """Search emails by subject."""
        return self.fetch_messages(query=f"subject:{subject_query}", max_results=max_results)

    def get_sender_frequency(self, sender_email, days=30):
        """Count emails from a sender in the last N days."""
        since = (datetime.utcnow() - timedelta(days=days)).strftime("%Y/%m/%d")
        results = self.service.users().messages().list(
            userId=self.user_id,
            q=f"from:{sender_email} after:{since}",
            maxResults=500,
        ).execute()
        return len(results.get("messages", []))

    # --- Profile ---

    def get_profile(self):
        """Get the authenticated user's email profile."""
        return self.service.users().getProfile(userId=self.user_id).execute()
