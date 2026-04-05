# MAILMAN Unsubscribe Agent Blueprint

## Purpose
Automates unsubscribing from unwanted email lists. Parses List-Unsubscribe headers, executes one-click unsubscribes via HTTP POST, and tracks results.

## Type
Executor Agent

## Frontmatter
```yaml
---
name: MAILMAN Unsubscribe Agent
type: executor
description: Automated email unsubscribe processing
author: Beryl / ARC System
version: 1.0
dependencies:
  - google-api-python-client
  - requests
  - beautifulsoup4
inputs:
  target_emails: list[message_id]
  mode: [preview|execute|bulk]
outputs:
  unsub_report: json
  success_count: int
  failed_list: json
schedule: null
---
```

## Unsubscribe Methods (Priority Order)

### Method 1: RFC 8058 One-Click (Preferred)
Parse `List-Unsubscribe-Post: List-Unsubscribe=One-Click` header. Send a single HTTP POST to the URL in `List-Unsubscribe` header. No user interaction needed, no browser, no form filling. Most reliable method.

### Method 2: List-Unsubscribe HTTPS Link
Parse `List-Unsubscribe: <https://...>` header. Follow the HTTPS link and look for confirmation. Some require clicking a button on the landing page. Use requests + BeautifulSoup to find and submit the confirm form.

### Method 3: List-Unsubscribe Mailto
Parse `List-Unsubscribe: <mailto:unsub@...>` header. Send an email to the unsubscribe address. Less reliable, slower confirmation. Use as fallback only.

### Method 4: Body Link Extraction
Scan email HTML body for common unsubscribe link patterns. Look for anchors containing "unsubscribe", "opt out", "manage preferences". Follow the link and attempt to complete the form. Least reliable, most complex. Only used when no header method is available.

## Safety Rules

1. **Never auto-unsubscribe from P0-P2 emails** - Only process P3+ items
2. **Preview mode by default** - Show Beryl what will be unsubscribed before executing
3. **Whitelist protection** - Never unsubscribe from senders in `rules/vip_contacts.json`
4. **Category protection** - Never unsubscribe from `financial`, `legal`, `security` categories
5. **Confirmation logging** - Log every unsubscribe attempt and result to `logs/unsub_log.jsonl`
6. **Cooldown period** - Wait 48 hours after first classification before executing unsubscribe (prevents false positives)
7. **Undo tracking** - Store the original subscribe source so resubscription is possible if needed

## Bulk Unsubscribe Workflow

1. Triage agent flags emails as `marketing_unwanted`
2. After 48-hour cooldown, collect all flagged senders
3. Group by sender domain for efficiency
4. Generate preview report for Beryl
5. On approval, execute unsubscribes in batch
6. Log results, retry failures after 24 hours
7. After 7 days, verify unsubscribe success by checking for new emails from those senders
8. Report final results

## Tracking Schema
```json
{
  "sender": "marketing@company.com",
  "domain": "company.com",
  "method_used": "rfc8058_oneclick",
  "attempted_at": "2026-03-14T20:00:00Z",
  "status": "success",
  "verified_at": null,
  "emails_received_since": 0,
  "resubscribe_url": null
}
```
