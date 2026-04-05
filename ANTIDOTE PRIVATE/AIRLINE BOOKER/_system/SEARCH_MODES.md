# AIRLINE BOOKER — Two Search Modes

The platform operates in two distinct modes. Both are first-class. Neither replaces the other.
Choose based on what the user actually needs.

---

## MODE 1: SIMPLE SEARCH
*"Find me the best flights for this trip."*

**When to use:**
- Booking for someone else (family member, friend, team)
- Domestic or simple international routes
- User wants: best price, clear reasoning, direct booking links
- No points optimization needed, no staff travel, no hedging

**What it outputs:**
- Top 3 ranked options with badges (Top Pick, Budget Winner, etc.)
- Per-option: airline, flight number, departure/arrival, stops, price, insight line
- Return options for each outbound pick
- Smart insights section (pricing patterns, airport trade-offs, timing)
- Action items with direct booking links

**Reference implementation:** `searches/emunah_chi_srq_april2026.json` + original dashboard
**Template:** `_templates/simple_search_dashboard.jsx`

**Key behaviors in simple mode:**
- Expand city → multiple airports (Chicago = ORD + MDW; Sarasota = SRQ + TPA + PGD)
- Search all date combinations if flexible ("any weekend in April" = 4 weekends × 2 airports)
- Lead with the best single recommendation and explain WHY in plain language
- Show return flight options for each outbound
- Include price context (is this typical? cheap? expensive?)
- End with direct booking action steps

---

## MODE 2: POWER SEARCH
*"Optimize this trip across every variable I have access to."*

**When to use:**
- Long-haul international (especially >8 hrs)
- Points/miles redemption is a goal
- User has staff travel or myIDtravel access
- Multiple routing options viable (via different hubs)
- User wants to hedge — hold multiple bookings, cancel closer to date
- Hybrid strategy: different cabin classes per leg

**What it outputs:**
- Hedge Portfolio tab — multiple simultaneous positions with collapse logic
- Availability Intel — best date windows, seat map tips, daily monitoring cadence
- Hybrid Packages — each leg optimized independently
- Cancellation Policies — exact cancel fees before entering any position
- Daily Checklist — rolling action plan from today to day-of

**Reference implementation:** `searches/beryl_lax_dps_april2026.json` + Bali dashboard
**Beryl-specific:** Always include AA staff standby + myIDtravel as free positions in the hedge

**Key behaviors in power mode:**
- Lay-flat on any leg > 8 hrs; economy acceptable under 4 hrs
- Always surface refundable options alongside non-refundable
- Show cancel fees BEFORE suggesting a booking — user needs to know exit cost
- Check seats.aero + Jetnet daily; alert on new availability
- Register standby for multiple dates simultaneously (free, no commitment)

---

## HOW TO DECIDE WHICH MODE

| Signal | Mode |
|--------|------|
| "Book a flight for [name]" | Simple |
| "Find flights to [city] this weekend" | Simple |
| "Best price for [route]" | Simple |
| "Use my points" | Power |
| "Business class / first class" | Power |
| "Lay-flat" | Power |
| "Standby / staff travel" | Power |
| "Refundable" or "cancelable" | Power |
| "Hedge" or "multiple options" | Power |
| International > 8 hrs | Power |
| Domestic or international < 6 hrs | Simple (default) |
| User is Beryl, trip is personal | Power (default) |
| User is someone else (Clayton, Brandon, Emunah) | Simple (default) |

---

## IMPORTANT: Don't Mix Them

Simple mode should stay clean and scannable. Power mode should stay comprehensive.
Don't add hedge portfolio logic to a simple search output. Don't strip the simple output
down just because a power mode dashboard exists. Both serve different people and moments.
