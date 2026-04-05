# TROV — Collectibles Event Discovery iOS App

**Project:** Collectibles event discovery app for iOS. Formerly "Scout," rebranded March 2026.
**Founder:** Ryan Wanderer (17yo). Investor: Phil Benson (grandfather). Product lead & builder: Beryl.
**Launch target:** App Store, July 15, 2026 (Fanatics Fest marketing catalyst: July 16-19).

---

## What TROV Is

A curated, personalized push-notification-first platform for sports collectibles & card show events. Users customize interests → app alerts them to matching events → Ryan manually curates NYC/NJ events + future backend AI aggregation.

**v1 Features:** Customizable dashboard (preferences), push alerts, event details, athlete/team filters, admin analytics, production-quality UX.

---

## Tech Stack & Architecture

- **Frontend:** Expo/React Native (iOS first, Android follow-on)
- **Backend:** Supabase (existing from Ryan's v1 prototype)
- **Deployment:** iOS App Store + TestFlight
- **No ejection needed.** Expo managed workflow covers all v1 requirements.
- **APIs:** OneSignal (push notifications), Supabase real-time.
- **Hard costs:** < $500 (Supabase, EAS Build, API tokens).

---

## Folder Structure

- `_proposals/` — Client proposal (Package A/B) + internal brief
- `_archive/original-scout-docs/` — Original Scout docs, competitive analysis, call notes
- `_memory/memory.md` — Full project history, timeline, decisions, engagement structure
- `_incoming/beryl-learnings.md` — Build learnings & sprint notes
- `_context/` — Additional reference materials

---

## Key Files

- `_proposals/TROV_Client_Proposal.docx` — Package A (Lean Launch) & Package B (Full Partnership)
- `_proposals/TROV_Internal_Brief_CONFIDENTIAL.docx` — Hard costs, margins, dev sourcing strategy
- `_memory/memory.md` — Complete context (don't duplicate here)
- **Lovable prototype:** scoutcollectibles.lovable.app (4 working routes: /home, /explore, /event/:id, /profile)

---

## Build Approach

**Beryl + Claude (Cowork/Claude Code) as core dev team.** Contract developer brought in for code review and App Store final mile.

**5 Phases (milestone-based, no calendar commitments):**
1. **Phase 1:** Technical spec + proof-of-deliverability sprint (before formal engagement)
2. **Phase 2:** Core app shell (auth, dashboard, event feed)
3. **Phase 3:** Push notifications + admin system
4. **Phase 4:** App Store submission + rejection response cycle
5. **Phase 5:** Launch + post-launch maintenance

---

## Key People & Roles

- **Ryan Wanderer** — Founder, 17yo. Handles manual event entry for v1. Decision-maker.
- **Phil Benson** — Investor, Ryan's grandfather. Approves budget/decisions.
- **Beryl** — Product lead, design, build overseer (Antidote Group).
- **Claude** — Dev partner (Cowork/Claude Code).
- **Contract dev** — Code review + App Store final mile (sourced Apr).

---

## Critical Dates

- **June 7, 2026** — App Store submission deadline
- **July 15, 2026** — Target launch
- **July 16-19, 2026** — Fanatics Fest (Javits Center, NYC) — marketing catalyst
- **Mar 30, 2026** — Proof-of-deliverability sprint begins

---

## Next Actions

1. Build prototype → technical spec as build bible
2. Present Package A/B proposal to Ryan/Phil
3. Lock engagement + retainer scope in writing
4. Start dev team sourcing (Lemon.io, Expo Discord)
5. Execute 5-phase build on milestone basis

See `_memory/memory.md` for full engagement history and competitive landscape.
