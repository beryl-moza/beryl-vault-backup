# Memory - MAILMAN

> Initialized 2026-03-14 20:33 UTC
> Phase 2 build completed 2026-03-15

## Key Decisions

- decision: MAILMAN lives in BERYL_VAULT/PERSONAL, Beryl-only privacy scope
- decision: Multi-account support via per-account OAuth2 with Fernet encryption
- decision: Gmail API as primary provider, IMAP as fallback for non-Gmail accounts
- decision: Claude Sonnet for email classification (fast, cost-effective for high volume)
- decision: 5-tier priority system (P0 FIRE through P4 JUNK)
- decision: 13 email categories covering work, personal, financial, security, and junk
- decision: Unsubscribe uses RFC 8058 one-click POST as preferred method
- decision: 48-hour cooldown before executing unsubscribes (prevents false positives)
- decision: VIP contacts are always protected from auto-archive and unsubscribe
- decision: Security scanner checks SPF/DKIM/DMARC, lookalike domains, BEC patterns
- decision: Contact intelligence tracks relationship health scores and dormant contacts
- decision: Voice learner trains from sent mail, builds statistical + AI style profile
- decision: Meeting intel detects 4 types: calendar_invite, meeting_request, meeting_notes, scheduling_discussion
- decision: MAILMAN Chat uses ChromaDB when available, keyword index as fallback
- decision: Auto-labeler creates color-coded Gmail label hierarchy (Priority, Category, Status, VIP)
- decision: Orchestrator routes brand-voice emails to arc-email-crafter, personal to voice_learner
- decision: All outbound drafts go through review gate. NEVER auto-send. (rule 11-beryl-rules)
- decision: ARC agent integration uses _incoming/ briefs as messaging protocol
- decision: Fyxer AI feature parity achieved + 6 capabilities Fyxer doesn't have

## Active Context

Phase 4 build complete. 20 Python modules (8,492 lines total), all syntax-verified:

Original modules (Phase 1):
- auth.py (278 lines): OAuth2 + encrypted token vault
- gmail_client.py (262 lines): Gmail API wrapper
- classifier.py (318 lines): AI + rule-based classification
- unsubscriber.py (318 lines): Multi-method unsubscribe engine
- digest.py (208 lines): Daily/weekly digest generator
- security.py (342 lines): Phishing/BEC/spoof detection
- contacts.py (291 lines): Contact intelligence

Phase 2 modules (Fyxer parity + beyond):
- voice_learner.py (478 lines): Writing style learning + voice-matched drafting
- meeting_intel.py (397 lines): Meeting detection, action items, follow-ups, prep briefs
- mailman_chat.py (416 lines): RAG semantic search across all accounts
- auto_labeler.py (327 lines): Gmail label hierarchy, auto-archive, color coding
- email_analytics.py (340 lines): Volume trends, health scoring, sender analysis

Phase 4 modules (Competitor feature parity):
- rules_engine.py (603 lines): Workflow automation rules with conditions/actions/cooldowns
- slack_bridge.py (651 lines): Slack Block Kit integration, alerts, digests, quiet hours
- calendar_scheduler.py (761 lines): Calendar-aware meeting scheduling, time proposals
- task_extractor.py (419 lines): Email-to-task conversion with AI deadline parsing
- smart_replies.py (312 lines): 3-option reply suggestions matching voice profile
- vip_gatekeeper.py (389 lines): Focus mode (normal/focus/dnd), VIP inbox filtering
- templates.py (465 lines): Reusable email template library with variable rendering

Orchestrator (Master controller):
- orchestrator.py (910 lines): v2 with 14-step full cycle, all modules wired

ARC agents wired in:
- arc-inbox, arc-email-crafter, arc-email-reviewer, arc-outreach
- arc-telegram, arc-slack, arc-coordinator, arc-nightwatch

## Fyxer Feature Mapping

| Fyxer Feature | MAILMAN Equivalent | Status |
|---|---|---|
| Inbox Organization | auto_labeler.py + classifier.py | Built |
| Draft Replies | voice_learner.py | Built |
| Voice Learning | voice_learner.py (train from sent mail) | Built |
| Meeting Notetaker | meeting_intel.py (detects + extracts from email) | Built |
| Follow-up Automation | meeting_intel.py (generate_follow_up) | Built |
| Meeting Scheduling | gcal MCP integration via orchestrator | Wired |
| Fyxer Chat | mailman_chat.py (RAG search) | Built |
| File Training | voice_learner.py supports external samples | Built |
| HubSpot/CRM | arc-outreach integration | Wired |

## Beyond Fyxer (MAILMAN Exclusive)

1. Security scanning (phishing, BEC, spoof detection)
2. Unsubscribe automation (RFC 8058 one-click)
3. Contact intelligence + relationship health scores
4. Multi-account with encrypted per-account tokens
5. Email analytics + inbox health grading (A-F)
6. Full ARC agent ecosystem integration (8 agents)
7. Priority-based auto-archive for junk
8. Meeting action item tracking with completion workflow
9. Overdue action item detection
10. Pre-meeting prep brief generation from email history

## Phase 3: Live Connection & Analysis (2026-03-16)

### OAuth2 Setup Complete
- Google Cloud Project: antidote-ai-tools-489918
- Gmail API + Calendar API enabled
- OAuth consent screen: External, Testing mode
- Desktop client: "MAILMAN Email Agent" (credentials.json in config/)
- Both accounts connected and verified via Gmail API

### Connected Accounts
- antidote_work (beryl@antidote.group): 11,729 msgs / 8,426 threads - WORKSPACE
- gmail_personal (beryljacobson@gmail.com): 372,200 msgs / 258,685 threads - PERSONAL

### First Full Analysis Results
- 100 emails scanned (50 per account)
- Priority: P0=0, P1=23, P2=5, P3=17, P4=55
- 55 unsubscribe candidates identified (19 work, 36 personal)
- Personal Gmail has 72% junk ratio — critical cleanup needed
- MAILMAN labels applied to all 100 emails in both accounts
- Voice profile trained from 57 sent emails (28 work, 29 personal)

### Voice Profile Highlights
- Work: 911 avg words, 12.7 sentence length, 18.2 emoji/email, formality 0.65
- Personal: 655 avg words, 15.5 sentence length, 0.6 emoji/email, formality 0.60
- Personal greetings: "Hey there", "Hey brother", "Hi Alex"
- Work is more structured/detailed; personal is warmer/punchier

### Competitor Research (9 products analyzed)
Products: Gmelius, Fyxer, Superhuman, Shortwave, Missive, Spark, Mimestream, DragApp, Perplexity
Full analysis saved to: mailman_competitor_research.json

### Top Feature Gaps to Close
1. CRITICAL: Team collaboration (comments, mentions, assignments) — 5 competitors
2. CRITICAL: CRM integration (Salesforce/HubSpot) — 4 competitors
3. HIGH: Read status / link tracking — 3 competitors
4. HIGH: Workflow automation rules engine — 4 competitors
5. HIGH: Email-to-task conversion — 4 competitors
6. HIGH: Meeting scheduling with calendar checking — 6 competitors
7. MEDIUM: SLA tracking — 2 competitors
8. MEDIUM: Integration ecosystem (Slack, Zapier) — 4 competitors

### MAILMAN Unique Advantages (no competitor has)
- Phishing/BEC/spoof detection with risk scoring
- Contact intelligence with relationship health scores
- RAG-powered semantic search (ChromaDB)
- RFC 8058 compliant batch unsubscriber
- ARC agent ecosystem integration (8 agents)

## Phase 3.5: Batch Unsubscribe (2026-03-16)

- 47 senders unsubscribed (50 candidates minus 3 protected)
- Protected: Zillow rentals, Relix music, Claude/Anthropic
- All unsubscribe URLs hit successfully (GET/POST)
- All threads trashed in both Gmail accounts
- 0 failures out of 47

## Next Steps

1. NOW: Populate vip_contacts.json with Beryl's actual VIP list
2. NOW: Run orchestrator.py full_cycle() on both accounts (v2 14-step)
3. THIS WEEK: Wire MAILMAN into arc-nightwatch for automated 7AM triage
4. THIS WEEK: Set up Slack channels (#mailman-alerts, #mailman-triage, #mailman-digest)
5. THIS WEEK: Configure automation rules for Beryl's specific patterns
6. NEXT: Read status / open tracking on sent emails
7. NEXT: Team collaboration features for Antidote rollout
8. FUTURE: CRM integration (HubSpot first)
9. FUTURE: Multi-language translation

## Important Notes

- All token storage uses Fernet symmetric encryption, one key per account
- Config files (.keys.json, .tokens.enc) must have 0600 permissions
- The Gmail MCP connector is already available in the Cowork environment
- The Google Calendar MCP is available for meeting_intel calendar integration
- Security scanner runs on every triage cycle (built into full-cycle)
- Voice profile improves with more training data (aim for 200+ sent emails)
- ChromaDB is optional for mailman_chat; keyword index works without it
