# MAILMAN Digest Agent Blueprint

## Purpose
Generates daily and weekly email digests summarizing inbox activity, surfacing priorities, and tracking trends.

## Type
Monitor Agent

## Frontmatter
```yaml
---
name: MAILMAN Digest Agent
type: monitor
description: Generates email summaries and inbox health reports
author: Beryl / ARC System
version: 1.0
dependencies:
  - anthropic
  - jinja2
inputs:
  period: [daily|weekly|custom]
  accounts: list[str]
outputs:
  digest_html: html
  digest_md: md
schedule: "0 7 * * *"
---
```

## Daily Digest Contents

### Section 1: Action Required
- Emails classified P0/P1 that haven't been responded to
- Threads waiting on your reply (with how long they've been waiting)
- Meeting requests pending acceptance
- Deadlines mentioned in emails arriving today

### Section 2: Today's Inbox Summary
- Total new emails by account
- Breakdown by category (work, personal, automated, junk)
- Number auto-archived, number flagged for review
- New senders (people who emailed you for the first time)

### Section 3: Thread Watch
- Active conversation summaries (who said what, what's pending)
- Threads that went quiet but had open questions
- Threads where someone else replied on your behalf

### Section 4: Unsubscribe Report
- Junk emails caught and archived today
- Pending unsubscribes awaiting your approval
- Successful unsubscribes from the past week
- Estimated time saved this week

### Section 5: Contact Intelligence
- Who emailed you most this week
- New contacts detected
- VIPs who haven't heard from you in 7+ days
- Relationship health score for key contacts

## Weekly Digest Additions
- Email volume trends (up/down vs last week)
- Response time analytics (your average, by category)
- Top 10 senders by volume
- Unsubscribe effectiveness (how much junk was reduced)
- Suggestions for new rules or VIP additions based on behavior

## Delivery Options
- Save to `_memory/digests/` as markdown
- Send via Telegram (if arc-telegram bridge is active)
- Display in ARC dashboard
- Email to beryl@antidote.group (optional, ironic but useful)

## Template
Uses Jinja2 templates from `templates/digest_template.md` for consistent formatting. Follows Antidote writing style: no em dashes, active voice, direct, no AI-speak.
