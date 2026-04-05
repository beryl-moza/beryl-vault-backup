# MAILMAN Triage Agent Blueprint

## Purpose
Reads incoming emails across all connected accounts, classifies them by priority and category, applies labels, and surfaces what matters.

## Type
Analyzer Agent

## Frontmatter
```yaml
---
name: MAILMAN Triage Agent
type: analyzer
description: Classifies and prioritizes incoming emails across multiple accounts
author: Beryl / ARC System
version: 1.0
dependencies:
  - google-api-python-client
  - anthropic
  - chromadb
inputs:
  accounts: list[str]
  since: datetime
  max_emails: int
outputs:
  classified_emails: jsonl
  priority_report: md
  action_items: json
schedule: "*/30 * * * *"
---
```

## Classification Categories

### Priority Tiers
- **P0 - FIRE**: Requires immediate response. Client escalations, urgent requests from VIPs, time-sensitive deadlines within 24 hours.
- **P1 - ACTION**: Needs response today. Active threads where you're expected to reply, meeting requests, important decisions.
- **P2 - REVIEW**: Read when you can. Newsletters you actually read, team updates, FYI emails with substance.
- **P3 - LOW**: Batch process weekly. Automated notifications, receipts, confirmations.
- **P4 - JUNK**: Unsubscribe candidates. Marketing spam, promotions you never open, lists you didn't sign up for.

### Content Categories
- `thread_active` - Conversation where a response is expected from you
- `thread_watching` - Conversation you're CC'd on, no action needed
- `meeting` - Calendar invites, scheduling requests
- `financial` - Invoices, receipts, bank notifications, payment confirmations
- `legal` - Contracts, agreements, compliance notices
- `personal` - Friends, family, non-work contacts
- `work_internal` - Antidote team communications
- `work_client` - Client-facing communications
- `newsletter_wanted` - Subscriptions you actually read
- `marketing_unwanted` - Promotional emails to unsubscribe from
- `automated` - System notifications, alerts, confirmations
- `security` - Password resets, 2FA codes, login alerts
- `suspicious` - Potential phishing or BEC attempts

## Classification Pipeline

1. **Header Analysis** - Extract sender, recipients, subject, List-Unsubscribe, reply-to, authentication results (SPF/DKIM/DMARC)
2. **VIP Check** - Compare sender against `rules/vip_contacts.json`
3. **Pattern Match** - Check against known categories in `rules/categories.json`
4. **AI Classification** - Send email summary to Claude API for nuanced classification
5. **Thread Context** - Check if this is part of an active thread needing response
6. **Urgency Scoring** - Scan for deadline keywords, sentiment analysis
7. **Action Extraction** - Pull out action items, questions directed at you, deadlines
8. **Label + Archive** - Apply Gmail labels, archive P3/P4 items

## Signals Used for Priority

- Sender is in VIP list (+2 priority)
- You are in the TO field vs CC (+1 if TO)
- Contains a question mark directed at you (+1)
- Contains deadline language ("by Friday", "EOD", "ASAP") (+1)
- Part of a thread you've previously replied to (+1)
- Negative sentiment detected (+1)
- From a new/unknown sender (-1 priority, +1 suspicious)
- Contains List-Unsubscribe header (-2 priority)
- Sender has sent 5+ emails you never opened (-2 priority)

## Output Format
Each classified email produces:
```json
{
  "message_id": "...",
  "account": "gmail_personal",
  "from": "sender@example.com",
  "subject": "...",
  "priority": "P1",
  "category": "thread_active",
  "action_items": ["Reply to budget question"],
  "urgency_keywords": ["by Friday"],
  "sentiment": "neutral",
  "labels_applied": ["ACTION", "work_internal"],
  "thread_id": "...",
  "needs_response": true,
  "classified_at": "2026-03-14T20:00:00Z"
}
```
