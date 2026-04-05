# MAILMAN - Personal Email Agent

## Identity
MAILMAN is an ARC-powered email management agent living inside BERYL_VAULT/PERSONAL. It handles multi-account email triage, unsubscribe automation, priority surfacing, voice-matched drafting, meeting intelligence, semantic inbox search, auto-labeling, analytics, and security scanning. Full Fyxer AI feature parity plus capabilities Fyxer does not have.

## Owner
Beryl Jacobson (beryl@antidote.group)

## Privacy & Safety
This is a Beryl-only agent. NEVER expose email content, account credentials, or MAILMAN outputs to shared contexts. All token storage uses per-account Fernet encryption. No email content leaves the local system unless Beryl explicitly authorizes it. NEVER auto-send any email. All outbound goes through draft review. This follows arc rule 11-beryl-rules: always draft, always wait for approval, then send.

## Connected Accounts
Configured in `config/accounts.json` (encrypted). Current targets:
- Gmail Personal
- Antidote Work Email (Google Workspace)
- Additional accounts as added

## Core Capabilities (13 Modules, 4,572 lines)

### Fyxer Parity Features
1. **VOICE LEARNER** (`voice_learner.py`) - Analyzes sent emails to learn your writing style. Builds a statistical + AI profile of greetings, signoffs, sentence length, formality, vocabulary, humor. Drafts replies that sound like you, not an AI.
2. **AUTO-LABELER** (`auto_labeler.py`) - Creates and manages a full MAILMAN label hierarchy in Gmail. Priority colors, category labels, status labels, VIP labels. Auto-archives P4 junk.
3. **DIGEST** (`digest.py`) - Daily and weekly summaries. Action required section, inbox stats, top senders, unsubscribe effectiveness, Claude-generated TL;DR.
4. **MEETING INTEL** (`meeting_intel.py`) - Detects meeting requests, calendar invites, scheduling discussions, and meeting recaps in emails. Extracts action items, generates follow-up emails, creates pre-meeting prep briefs.

### Beyond Fyxer
5. **CLASSIFIER** (`classifier.py`) - Dual-engine classification. Fast rule-based pass (VIP, unsub headers, urgency keywords) then Claude Sonnet for nuanced analysis. 5-tier priority (P0 FIRE through P4 JUNK), 13 categories.
6. **UNSUBSCRIBER** (`unsubscriber.py`) - Multi-method unsubscribe engine. RFC 8058 one-click POST first, HTTPS GET fallback, mailto last resort. Preview mode, 48h cooldown, VIP protection, audit log.
7. **SECURITY** (`security.py`) - Phishing/BEC/spoof detection. Checks SPF/DKIM/DMARC, lookalike domains, suspicious TLDs, IP-based URLs, URL shorteners. Risk score 0-100.
8. **CONTACTS** (`contacts.py`) - Relationship intelligence. Tracks frequency, recency, bidirectional communication, dormant VIPs, new contacts, relationship health scores.
9. **MAILMAN CHAT** (`mailman_chat.py`) - RAG semantic search across all email accounts. ChromaDB vectors when available, keyword index fallback. Natural language queries grounded in actual email content.
10. **ANALYTICS** (`email_analytics.py`) - Volume trends, priority distribution, top senders, time-of-day patterns, response load, unsubscribe effectiveness, inbox health score (0-100 with letter grade).
11. **AUTH** (`auth.py`) - OAuth2 setup with per-account Fernet encryption. Multi-account token vault, secure key storage.
12. **GMAIL CLIENT** (`gmail_client.py`) - Full Gmail API wrapper. Read, label, archive, search, thread management.
13. **ORCHESTRATOR** (`orchestrator.py`) - Master controller. Single entry point for all operations. Wires MAILMAN modules to ARC agent ecosystem.

## ARC Agent Integration
The orchestrator connects to these existing ARC agents:
- **arc-inbox** - Inbound triage methodology and routing logic
- **arc-email-crafter** - Brand-voice drafting (Antidote, ZYVA, Ka'Chava, Moon Juice, Iconic, Growth Channel)
- **arc-email-reviewer** - Pre-send validation (compliance, CAN-SPAM, brand, rendering)
- **arc-outreach** - Campaign management, sequences, contact list hygiene
- **arc-telegram** - Delivery notifications, P0 alerts, digest delivery
- **arc-slack** - Team channel updates
- **arc-coordinator** - Complex multi-agent workflows
- **arc-nightwatch** - Scheduled overnight cycle runs

Integration method: MAILMAN writes structured briefs to `_incoming/` for ARC agents to consume. Uses the same messaging protocol as other ARC agents.

## Dependencies
- google-api-python-client, google-auth-oauthlib (Gmail API + OAuth2)
- cryptography (Fernet token encryption)
- anthropic (Claude API for classification, voice learning, meeting extraction)
- chromadb (optional, vector embeddings for semantic search)
- requests (HTTP unsubscribe calls)
- jinja2 (digest templates)

## File Structure
```
MAILMAN/
  CLAUDE.md                       # This file
  _context/                       # Reference material, API docs
  _proposals/                     # Feature proposals
  _incoming/                      # ARC agent briefs, new items
  _memory/                        # Persistent state
    memory.md                     # Key decisions and context
    voice_profile.json            # Learned writing style
    contacts_db.json              # Contact intelligence database
    meetings_db.json              # Meeting history
    action_items.json             # Meeting action item tracker
    email_index.json              # Keyword search index (fallback)
    vector_db/                    # ChromaDB vector storage
    digests/                      # Generated digest archive
  _SYSTEM/                        # System learning
  config/                         # Encrypted account configs
  agents/                         # Sub-agent blueprints
    arc-mailman-triage.md
    arc-mailman-unsub.md
    arc-mailman-digest.md
  core/                           # Python modules (13 files, 4,572 lines)
    __init__.py
    auth.py                       # OAuth2 + encrypted token vault
    gmail_client.py               # Gmail API wrapper
    classifier.py                 # AI + rule-based classification
    unsubscriber.py               # Multi-method unsubscribe engine
    digest.py                     # Daily/weekly digest generator
    security.py                   # Phishing/BEC/spoof detection
    contacts.py                   # Contact intelligence
    voice_learner.py              # Writing style learning + draft generation
    meeting_intel.py              # Meeting detection, follow-ups, action items
    mailman_chat.py               # RAG semantic search across inbox
    orchestrator.py               # Master controller + ARC agent router
    auto_labeler.py               # Gmail label management + auto-archive
    email_analytics.py            # Inbox analytics + health scoring
  rules/                          # Classification rules
    vip_contacts.json
    categories.json
    urgency_keywords.json
  templates/
    digest_template.md
    reply_templates/
  logs/
    triage_log.jsonl
    unsub_log.jsonl
    security_log.jsonl
    labeling_log.jsonl
    orchestrator_log.jsonl
```

## Running MAILMAN

### Via Orchestrator (recommended)
```bash
# Complete cycle: fetch, scan, classify, label, unsub, contacts, meetings, index
python3 core/orchestrator.py full-cycle --account gmail_personal

# Quick triage
python3 core/orchestrator.py triage --account gmail_personal

# Generate digest
python3 core/orchestrator.py digest --period daily

# Draft a reply in your voice
python3 core/orchestrator.py draft-reply <message_id>

# Draft with brand voice (routes to arc-email-crafter)
python3 core/orchestrator.py draft-reply <message_id> --brand Antidote

# Ask MAILMAN Chat a question
python3 core/orchestrator.py chat "What did Brandon say about the Q4 budget?"

# Meeting operations
python3 core/orchestrator.py meetings --scan
python3 core/orchestrator.py meetings --actions
python3 core/orchestrator.py meetings --follow-up <meeting_id>

# Train voice profile
python3 core/orchestrator.py train-voice --account gmail_personal

# Analytics
python3 core/orchestrator.py analytics --period 30
```

### Direct module access
```bash
python3 core/auth.py --setup                    # First-time OAuth2 setup
python3 core/auto_labeler.py --setup <account>  # Create Gmail label hierarchy
python3 core/voice_learner.py --profile         # View voice profile
python3 core/contacts.py --dormant 14           # Dormant contacts
python3 core/email_analytics.py --health        # Inbox health score
```

## Rollout Plan
Phase 1: Beryl only, Gmail personal account (current)
Phase 2: Add Antidote work email
Phase 3: Add additional accounts
Phase 4: Connect to arc-nightwatch for automated overnight runs
Phase 5: Test with team members
Phase 6: Package for broader rollout
