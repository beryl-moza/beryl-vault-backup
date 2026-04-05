# Memory — TROV (formerly Scout)

> Initialized 2026-03-14 05:05 UTC
> Updated 2026-03-28 (rebrand to TROV, folder reorganization, new proposal docs, Ryan's latest requirements)

---

## People

- **Ryan Wanderer** — Founder, 17 years old. Beryl's cousin. Passionate about sports collectibles/card hobby. Built a working v1 prototype on Supabase. Energetic, follows through on feedback, tends to think 10 steps ahead. Has matured significantly in thinking since Jan 2026 — now understands manual-first approach and legal grey areas of scraping.
- **Phil Benson** — Ryan's grandfather. Investor. Willing to back Ryan if Beryl endorses it, doesn't want to waste money.
- **Beryl (Antidote Group)** — Product Lead. Transitioned from informal monthly advisor to formal client engagement. Managing design, offshore dev sourcing, and App Store launch. Has drafted both a client proposal and internal financial brief.

---

## Project Evolution

### Phase 1: Advisory (Jan–Mar 2026)
1. **Jan 2026** — Ryan presents original business plan to Phil. Broad concept: AI-powered event discovery for everything.
2. **Jan 20** — Ryan emails Beryl. Had tried building on Supabase (pulled ~3,000 events via APIs/RSS, mostly big events). Couldn't build frontend. Two Upwork quotes: Taylor Ohlsen (~$50k), Barry Johnson (~$8k).
3. **Feb 2** — Beryl sends detailed analysis: legal/liability risks (scraping CFAA, copyright, accuracy, GDPR), competitive landscape (Bandsintown, DICE, Eventbrite, FB Events, Google/Apple), uniqueness 6/10 (push-first alert is only differentiator), route-to-market (micro-niche, hyper-local), capital reality ($8.8k insufficient). Referenced JamBase as model.
4. **Feb 14** — Ryan pivots to sports collectibles/card shows. Proposes NYC or Miami. Does competitive research on 10+ platforms. Also expands into vision for IRL athlete events (Luka Heartbreak Factory inspiration).
5. **Mar 18** — Third check-in call. Beryl prepares briefing (see _archive/original-scout-docs/Call Notes - March 18 2026.pdf).
6. **Late Mar 2026** — Project renamed from Scout to TROV. Beryl formalizes engagement via Antidote Group. Client proposal and internal brief drafted.

### Phase 2: Engagement (Current — Mar 2026+)
- Antidote Group client engagement formalized
- Two-package proposal created (see _proposals/)
- Target: iOS App Store launch July 15, 2026 (Fanatics Fest at Javits Center July 16-19)
- App Store submission deadline: June 7, 2026
- Ryan has a working v1 prototype to use as design reference

---

## Ryan's Latest Requirements (March 2026)

Ryan provided updated thinking on what the initial app must have:

### Core App Requirements:
1. **Customizable dashboard** — Users personalize interests, which connects throughout the whole app changing events shown
2. **Automatic push notifications** — Alert users when a new event matching their preferences is added
3. **Backend analytics** — Admin system where Ryan can view metrics and statistics on users
4. **Production quality** — Must work, feel, and function like any other real app

### Event Data Strategy (Critical):
- **For v1/launch:** Ryan will manually find and insert events himself. No automated scraping.
- **Future (if traction):** Backend AI system that automatically scours sources and pulls/plugs/sends new events
- **Ryan acknowledges:** Web scraping is legally grey, code must be right, and it adds complexity — so manual first is the smart move
- This is a major evolution from the original plan — Ryan has internalized the "validate manually first" advice

### Business Focus:
- **Consumer side:** Show users all events they'd like → create FOMO if they don't have TROV
- **B2B side:** Prove that having events on TROV generates highest participant turnout because of active, trust-based user community
- **Key metric:** Click-through percentage — proving users trust TROV and actually attend events
- **Geographic scope:** NYC/NJ only for now. If growth in a few months, expand to top cities in this category
- **Category:** Sports and collectibles only. Potential future expansion to other interests or producing own events

### Ryan's Maturation Points:
- Now understands scraping is legally grey and shouldn't be in v1
- Wants to get the app in the App Store before pursuing users (wants it to feel real)
- Thinking about B2B proof metrics (click-through rate) not just user count
- Acknowledges future expansion should be earned, not assumed

---

## Engagement Structure (from Proposals)

### Client Proposal (_proposals/TROV_Client_Proposal.docx):
**Package A — Lean Launch:**
- Client (Ryan) closely involved in build process
- Beryl personally designs UI/UX, manages dev
- Lower cost (~$10k build)
- Monthly partnership post-launch: $2,500/mo

**Package B — Full Partnership:**
- Antidote assembles and manages dedicated dev team
- Ryan shows up for weekly reviews, makes key decisions
- Higher cost (~$10-15k/mo during build)
- Monthly partnership post-launch: $2,500/mo or $5,000/mo growth retainer

**Both packages deliver:**
- Complete native iOS app (Expo/React Native)
- Wired into existing Supabase backend
- App Store submission and rejection response handling
- Full code ownership to client

**Payment:** Milestone-based, not calendar-based

**Post-launch retainer ($2,500/mo) includes:**
- Up to 8 hrs dev time (bug fixes, minor updates)
- Monthly check-in call (45 min)
- Push notification monitoring and uptime
- App Store review/OS compatibility responses
- NOT included: new features, design changes, new screens, third-party integrations

### Internal Brief (_proposals/TROV_Internal_Brief_CONFIDENTIAL.docx):
**⛔ CONFIDENTIAL — Key numbers (not for client):**
- Package A hard cost: $2,730–$4,980 → margin is real at $10k
- Package B: Target $6,000–$10,000 for LatAm dev team build
- $2,500/mo retainer real cost: ~$800-1,200/mo → strong margin
- Beryl's time commitment: Package A = 4-6 hrs/week during build; Package B = less hands-on
- Dev sourcing: Lemon.io + Expo Discord. Interview 3-5, require 2 App Store submissions, Expo+Supabase experience
- Floor price: Never discount below $10k for build

**Internal risks flagged:**
- Claude Code output quality not guaranteed — some screens may need rework
- Expo managed workflow covers 80% of needs; remaining 20% (custom push certs, deep links, background fetch) can hit walls
- App Store rejection cycles unpredictable
- Supabase real-time at scale could buckle if Fanatics Fest drives meaningful traction
- Scope creep on retainer is #1 margin killer
- July 15 is hard deadline — if App Store rejects twice, miss Fanatics Fest
- Finding quality LatAm dev team by Apr 10 requires starting NOW
- TestFlight fallback plan: soft launch at Fanatics Fest if App Store approval doesn't come through

**Internal decisions needed:**
1. Lead with Package B (higher margin, less Beryl time) — offer Package A as pushback alternative
2. Dev team sourcing must start this week regardless of which package sells
3. Retainer scope must be written clearly before signing
4. TestFlight fallback should be built into contract as deliverable

---

## Competitive Landscape (from original research)

### Direct Competitors in Collectibles Space:
- **CSAC (csac.biz)** — Closest competitor. $5.99/mo subscription for Chicagoland autograph events. Proves the model works. No push notifications, no personalization engine, only one city.
- **TCG Shows Near Me** — 4,000+ events, map view, sort by distance. But too many ads, no automation, community-submitted = outdated entries.
- **Sports Card Investor** — Large database, filtered by state, map view. Community-submitted, no personalization, outdated entries common.
- **TCDB (Trading Card Database)** — Organized by state, links to original source. Just a list, outdated, no smart feed.
- **Facebook Events/Groups** — Where most local card shows are ONLY announced. No aggregation, no integration.
- **Signing Hotline** — Wide range of autographs, all sports. Very dated UI, no filtering for preferences.

### Hidden Competitors:
- **Fanatics** — Owns cards (Topps), retail, events (Fanatics Fest). Could add "Alert Me" feature and wipe TROV out. TROV's angle: focus on niche, local, independent events Fanatics ignores.
- **Google/Apple** — Both integrating events into Maps. But commodity-level, no collectibles specialization.

### TROV's Differentiators:
- Push-first alert system (don't search, we find you)
- Collectibles-specific personalization (athletes, teams, leagues, event types)
- Manual curation for v1 = higher quality than community-submitted competitors
- NYC/NJ hyper-local focus = deep rather than wide

---

## Earlier Analysis Context

### Beryl's Feb 2 Email — Key Concerns:
1. Scraping vs. Terms of Service / CFAA risk
2. Copyright issues with aggregating event content
3. AI "prediction" accuracy liability (hallucination risk)
4. GDPR/CCPA location tracking compliance
5. Empty map problem (app looks dead if scraping fails)
6. Signal vs. noise (too many irrelevant alerts = uninstall)
7. Scraper maintenance is a full-time engineering job
8. Affiliate revenue from ticketing is low margin
9. Discovery is a "graveyard category" in tech

### Gemini Analysis Highlights:
- Uniqueness: 6/10. Push-first alert is only real differentiator
- Capital reality: Production-grade AI scraper + geofencing = $130k-$150k for Series A readiness
- Sports collectibles pivot pros: High-intent/high-spend users, fragmented market, data monetization potential
- Sports collectibles pivot cons: "Operating system" trap if producing events, athlete gatekeepers, Fanatics threat
- Lean MVP path: (1) Curated drop calendar, (2) Partner with shops for early access, (3) At 1,000 users approach athletes

### Earlier Pricing Exploration (Gemini thread — superseded by current proposals):
- Plan A: 6-month/$90k concept-to-community
- Plan B: 90-day/$50k MVP sprint
- These were early explorations. The current TROV proposals (_proposals/) are the finalized versions.

---

## Technical Stack

- **Frontend:** Expo / React Native (iOS first, Android as follow-on sprint)
- **Backend:** Supabase (existing from Ryan's v1 prototype)
- **Event data v1:** Manual entry by Ryan
- **Event data future:** Automated scraping/AI aggregation
- **Deployment:** iOS App Store (TestFlight for beta)
- **Target launch:** July 15, 2026

---

## Active Context (as of March 28, 2026)

- Project renamed from SCOUT to TROV
- Folder reorganized: proposals in `_proposals/`, original docs archived in `_archive/`
- Client proposal and internal brief drafted and ready
- **URGENT:** Engagement needs to begin THIS WEEK for July 15 deadline
- Dev team sourcing should start immediately (Lemon.io, Expo Discord)
- App Store submission deadline: June 7, 2026
- Ryan's v1 prototype exists as design reference
- Ryan will handle manual event entry for launch
- NYC/NJ is the launch region
- Fanatics Fest (July 16-19, Javits Center) is the marketing catalyst

## Next Steps for Beryl
1. Finalize which package to present (recommendation: lead with B, A as fallback)
2. Begin dev team sourcing NOW regardless of package decision
3. Present proposal to Ryan/Phil
4. Lock retainer scope in writing before signing
5. Build TestFlight fallback into contract
6. Begin technical spec from Ryan's v1 prototype once engagement starts

---

## Lovable Prototype Review (March 30, 2026)

**URL:** scoutcollectibles.lovable.app

**Routes crawled and working:**
- `/home` — Dashboard with user preference chips (sports, collectibles types). Real event cards below. Customizable filters. Full preference engine works.
- `/explore` — Browse all events, map view, distance filtering, sort by date/distance. Real event data from Supabase.
- `/event/:id` — Event detail page. Full info: date, time, location, athlete rosters, description, organizer, ticketing link. Real data populated.
- `/profile` — User profile, saved preferences, notification settings, saved events (wishlist).

**Routes NOT built:**
- `/saved` — Returns 404 (not implemented)
- Login/onboarding flow — Not built (assuming app flow starts at dashboard)
- Admin dashboard — Not built (Ryan managing events manually via direct DB for now)

**Third-party integrations referenced but not functional:**
- OneSignal push notification system (placeholder only, no real push notifications in prototype)

**Feature inventory from screens:**
- Preference chips: sports categories (NFL, NBA, MLB, NHL, MLS), collectibles types (cards, memorabilia, autographs, jerseys, figurines), event types (buying, selling, authentication, grading)
- Real-time event feed with filtering by preferences
- Event search/discovery with geolocation
- Athlete roster display on event cards (pulls from Supabase)
- Admin control of event curation (Ryan's manual queue)
- Push notification system wired but not active
- Saved/wishlist event collection

**Key findings:**
- Prototype is 60% of the UX work done — screens are polished, navigation clean, mobile-first design solid.
- Real event data already in Supabase (not dummy data). Ryan has 150+ NYC/NJ card shows, collectibles events, athlete signing events loaded.
- Preference engine fully functional — correctly filters events based on user interests.
- Data model is production-ready — Supabase schema supports all v1 features without modification.
- No custom push certificate infrastructure needed — OneSignal integration path is clear.

---

## Build Decision (March 30, 2026)

**Decision:** Beryl will build the native iOS app herself with Claude as development partner. Contract developer to be brought in for code review and App Store final-mile only.

**Rationale:**
- Lovable prototype proved concept is viable and design is solid
- Beryl's product lead + Claude's dev speed is faster than sourcing and managing a full external team for the entire build
- Milestone-based approach eliminates calendar risk and speeds decision-making
- Contract dev for code review ensures production quality without full-time management overhead
- Proof-of-deliverability sprint (before formal engagement) de-risks technical feasibility

**Cost structure (estimated):**
- Hard costs: < $500 (Supabase hosting, EAS Build credits, OneSignal API tokens)
- Contract dev code review: sourced from Lemon.io, ~$100-150/hour, ~20-30 hours = $2,000-4,500
- Beryl time: product lead + design + build oversight (no line-of-code development except architecture)
- Claude time: unlimited as dev partner (included in existing Cowork subscription)

**No calendar commitments.** Build on 5-phase milestone basis:
1. Phase 1 (this week): Technical spec, proof-of-deliverability sprint
2. Phase 2-5: Dependent on Ryan/Phil engagement + budget approval

**Proof-of-deliverability sprint plan (before formal contract):**
- Build Phase 1: Expo app shell + navigation + Supabase auth
- Test: Deploy to EAS Build, run on simulator + physical device
- Validate: Expo workflow covers all tech needs without ejection
- Output: Technical spec as build bible for remaining phases

**Technical spec will document:**
- Exact Expo/React Native + Supabase architecture
- Component breakdown per phase
- OneSignal integration path
- App Store submission checklist
- TestFlight + sandbox environment setup
- Post-launch maintenance scope

**Contract developer selection criteria:**
- 2+ production iOS apps shipped with Expo + Supabase
- 2+ App Store submissions and approval history
- Code review expertise (security, performance, best practices)
- Expo Discord community reputation (if possible)
