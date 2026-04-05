import { useState } from "react";

// ═══════════════════════════════════════════════════════════════
// AIRLINE BOOKER — Beryl Jacobson
// SEARCH: LAX → Denpasar Bali (DPS) · April 1–14, 2026
// ENGINE: Hybrid Booking + Hedge Portfolio + Availability Scanner
// PHILOSOPHY: Hold multiple refundable positions. Collapse to best.
// Last updated: March 25, 2026
// ═══════════════════════════════════════════════════════════════

const TABS = ["🚨 5-Day Brief", "🎲 Hedge Portfolio", "📡 Availability Intel", "🔀 Hybrid Packages", "📋 Cancellation Policies", "✅ Daily Checklist"];

// ─── HEDGE PORTFOLIO ─────────────────────────────────────────────
// The strategy: Book 2–3 refundable/cancelable positions simultaneously.
// AA standby is always free. Points awards have small cancel fees.
// Cash refundable fares are fully recoverable. Hold all three, collapse to best.

const PORTFOLIO_STRATEGIES = [
  {
    id: "ps1",
    label: "🏆 Full Hedge",
    tagline: "Hold all three positions simultaneously",
    cardBg: "bg-indigo-950/40 border-indigo-500/40",
    badge: "bg-indigo-600",
    riskLevel: "Lowest risk",
    riskColor: "text-emerald-400",
    totalExposure: "~$150–400 + 65K miles at risk (all recoverable)",
    positions: [
      {
        slot: "A",
        color: "bg-amber-600",
        label: "AA Staff Standby",
        type: "staff",
        route: "LAX → NRT → DPS",
        dates: "April 5–9 (best load factor window)",
        cabin: "D1 Business (if clears) / Economy fallback",
        cost: "~$30–60 taxes only",
        cancelPolicy: "No booking = no cancel. Free to register, free to walk away.",
        cancelFee: "$0",
        refundable: true,
        bookWhere: "AA Jetnet staff portal",
        priority: "Check FIRST — costs nothing to try",
      },
      {
        slot: "B",
        color: "bg-blue-600",
        label: "ANA Mileage Club Award",
        type: "points",
        route: "LAX → NRT/HND → DPS",
        dates: "April 5–9 (same window as standby)",
        cabin: "Business Class (The Room)",
        cost: "65,000 ANA miles + ~$40 taxes",
        cancelPolicy: "Cancel up to 24hr before — miles redeposited minus cancel fee. Low risk.",
        cancelFee: "~$75–150 fee, miles returned",
        refundable: true,
        bookWhere: "ana.co.jp → Mileage Award",
        priority: "Book this as INSURANCE. It's your guaranteed lay-flat if standby fails.",
      },
      {
        slot: "C",
        color: "bg-emerald-600",
        label: "KrisFlyer PE — Spontaneous Escapes",
        type: "points",
        route: "LAX → SIN → DPS",
        dates: "April 6–10 (slightly later window)",
        cabin: "Premium Economy (near lay-flat)",
        cost: "78,500 KrisFlyer miles + ~$50 taxes",
        cancelPolicy: "Cancel before departure — miles redeposited minus $75 fee. Spontaneous Escapes is the most forgiving.",
        cancelFee: "$75, miles returned",
        refundable: true,
        bookWhere: "singaporeair.com → Spontaneous Escapes",
        priority: "Book as BACKUP to B. Different route = diversified hedge.",
      },
    ],
    collapseLogic: [
      { trigger: "AA standby clears D1 with good seat (window/aisle, not middle)", action: "Board the flight. Cancel positions B and C. Recover miles minus cancel fees. Net cost: ~$150.", emoji: "🎉" },
      { trigger: "AA standby clears but seat is middle or cramped", action: "Decline the seat. Take position B (ANA business) or C (KrisFlyer PE). Cancel the one you don't use.", emoji: "🤔" },
      { trigger: "AA standby doesn't clear (full flight)", action: "Take position B (ANA business). Cancel position C. Full lay-flat guaranteed. Cancel fee ~$75 on KrisFlyer.", emoji: "✈️" },
      { trigger: "ANA shows better availability on later date", action: "Adjust position B date. Keep C as different-date backup. Cancel whichever you don't fly.", emoji: "📅" },
    ],
  },
  {
    id: "ps2",
    label: "💰 Cash Hedge",
    tagline: "Book a refundable cash fare as anchor, standby as wildcard",
    cardBg: "bg-slate-800/40 border-slate-600/40",
    badge: "bg-slate-600",
    riskLevel: "Zero financial risk (fully refundable)",
    riskColor: "text-emerald-400",
    totalExposure: "Cash refundable = $0 at risk if cancelled; preserves all points",
    positions: [
      {
        slot: "A",
        color: "bg-amber-600",
        label: "AA Staff Standby",
        type: "staff",
        route: "LAX → NRT → DPS",
        dates: "April 5–9",
        cabin: "D1 if lucky",
        cost: "$30–60",
        cancelPolicy: "Free — no booking to cancel.",
        cancelFee: "$0",
        refundable: true,
        bookWhere: "AA Jetnet",
        priority: "Always register for this — it costs nothing.",
      },
      {
        slot: "B",
        color: "bg-rose-600",
        label: "Refundable Cash — Business Class",
        type: "cash",
        route: "LAX → NRT or SIN → DPS",
        dates: "April 5–9",
        cabin: "Business Class (EVA, Korean Air, or ANA)",
        cost: "$2,700–3,500 RT (fully refundable fare class)",
        cancelPolicy: "100% refund to card if cancelled before departure. MUST book 'Fully Refundable' or 'Flex' fare class.",
        cancelFee: "$0 — full refund",
        refundable: true,
        bookWhere: "airline direct website — select 'Flexible' or 'Fully Refundable' fare",
        priority: "This is your guaranteed anchor. If standby fails and points are gone — you still fly business.",
      },
    ],
    collapseLogic: [
      { trigger: "Standby clears with great seat", action: "Board free. Call airline and cancel refundable cash booking. Full refund to card.", emoji: "🎉" },
      { trigger: "Award space opens up in ANA or KrisFlyer", action: "Transfer points and book award. Then cancel cash booking. Refund received.", emoji: "⚡" },
      { trigger: "Neither happens — trip is tomorrow", action: "Use the refundable cash flight. Great seat, great product. Travel happens.", emoji: "✈️" },
    ],
  },
];

// ─── AVAILABILITY INTELLIGENCE ────────────────────────────────────
const AVAIL_WINDOWS = [
  {
    dates: "Apr 1–3 (Wed–Fri)",
    businessLoad: "HIGH",
    peLoad: "HIGH",
    loadColor: "text-red-400",
    dotColor: "bg-red-500",
    reason: "End of spring break + Easter weekend — one of the busiest periods of April",
    recommendation: "Avoid if possible. Very limited premium cabin availability.",
    staffChance: "Low",
  },
  {
    dates: "Apr 5–7 (Sun–Tue)",
    businessLoad: "MEDIUM",
    peLoad: "MEDIUM",
    loadColor: "text-yellow-400",
    dotColor: "bg-yellow-500",
    reason: "Post-Easter, mid-week. Business travel picks up slightly.",
    recommendation: "Good window. Sunday/Monday departures tend to have more open D1.",
    staffChance: "Medium",
  },
  {
    dates: "Apr 8–10 (Wed–Fri)",
    businessLoad: "LOW-MED",
    peLoad: "LOW",
    loadColor: "text-emerald-400",
    dotColor: "bg-emerald-500",
    reason: "Mid-month mid-week is historically the lightest load period for transpacific. Best window.",
    recommendation: "⭐ Best window. Most premium cabin availability. Check standby loads Apr 8 or 9.",
    staffChance: "Highest",
  },
  {
    dates: "Apr 11–12 (Sat–Sun)",
    businessLoad: "MEDIUM",
    peLoad: "HIGH",
    loadColor: "text-yellow-400",
    dotColor: "bg-yellow-500",
    reason: "Weekend departures — leisure travelers book PE heavily on weekends.",
    recommendation: "Business may have space but PE books up on weekends. Go for business if checking this window.",
    staffChance: "Medium",
  },
  {
    dates: "Apr 13–14 (Mon–Tue)",
    businessLoad: "LOW",
    peLoad: "MEDIUM",
    loadColor: "text-emerald-400",
    dotColor: "bg-emerald-400",
    reason: "Late in the April 1–14 window. Last chance. Monday/Tuesday are always lighter.",
    recommendation: "Second best window if Apr 8–10 is missed. Monday departures especially light.",
    staffChance: "High",
  },
];

const SEAT_TIPS = [
  {
    title: "Odd departure times = open cabins",
    detail: "Flights departing 8–11am LAX time are the sweet spot. Red-eyes (midnight–4am) and 5–7pm departures are packed. Mid-morning gets the most upgrades cleared and the most no-shows.",
    icon: "🕐",
  },
  {
    title: "Check seat maps, not just availability",
    detail: "An 'available' business class ticket doesn't mean the cabin is empty — it means there's at least one seat. Check the actual seat map (flightradar24.com or expert flyer) to see HOW many are open. 6+ open seats = standby paradise. 1–2 = risky.",
    icon: "🗺️",
  },
  {
    title: "Award space spikes 2 weeks out",
    detail: "Airlines release unsold premium cabin seats as award inventory 14–21 days before departure. You're exactly in this window right now. Check daily — new space often appears Tuesday–Thursday as airlines run load optimization.",
    icon: "📈",
  },
  {
    title: "ExpertFlyer = your secret weapon",
    detail: "expertflyer.com ($99/yr or $9.99/mo) shows real-time award availability across all major programs, seat maps, and can alert you when specific award space opens. For a trip like this, it pays for itself immediately.",
    icon: "🔍",
  },
  {
    title: "Seats.aero for award availability",
    detail: "seats.aero is free and shows current award inventory across ANA, United, Air Canada, Singapore and more in one search. Check this daily for LAX→NRT and LAX→SIN business class openings.",
    icon: "🌐",
  },
  {
    title: "Standby timing: arrive 3 hrs early",
    detail: "For D1 standby, arriving early gets your name higher on the list. Other staff travelers compete for the same seats. Check in via app first, then go to the gate and introduce yourself to the GA.",
    icon: "⏰",
  },
];

// ─── CANCELLATION POLICIES ────────────────────────────────────────
const CANCEL_POLICIES = [
  {
    program: "ANA Mileage Club Awards",
    type: "points",
    icon: "✈️",
    cancelCost: "~$75–150 USD + miles redeposited",
    changeAllowed: "Yes — reissue for fee",
    deadline: "Cancel before check-in opens (24 hrs out)",
    refundMethod: "Miles back to account within 3–5 days",
    hedgeFriendly: true,
    notes: "Best cancellation policy of all the award programs. Miles come back. Change fees are small relative to the redemption value.",
    rating: 5,
  },
  {
    program: "Singapore KrisFlyer (Spontaneous Escapes)",
    type: "points",
    icon: "🇸🇬",
    cancelCost: "$75 USD + miles redeposited",
    changeAllowed: "Yes — new booking required",
    deadline: "Cancel 24+ hrs before departure",
    refundMethod: "Miles back within 5–7 days",
    hedgeFriendly: true,
    notes: "Spontaneous Escapes specifically designed for last-minute flexible travel. $75 is reasonable insurance for the hedge strategy.",
    rating: 5,
  },
  {
    program: "Air Canada Aeroplan Awards",
    type: "points",
    icon: "🍁",
    cancelCost: "$150 USD + miles redeposited",
    changeAllowed: "Yes — change or cancel for fee",
    deadline: "Can cancel up to 2 hrs before departure",
    refundMethod: "Miles back within 7–10 days",
    hedgeFriendly: true,
    notes: "Pricier cancel fee but extremely generous deadline. Can literally cancel 2 hours before a flight.",
    rating: 4,
  },
  {
    program: "United MileagePlus Awards",
    type: "points",
    icon: "🔵",
    cancelCost: "Free if cancelled 31+ days out. $125 closer.",
    changeAllowed: "Yes",
    deadline: "Before departure",
    refundMethod: "Miles back within 3 days",
    hedgeFriendly: false,
    notes: "Dynamic pricing makes rebooking risky — cancelled award may not rebook at same price. Less ideal for hedging.",
    rating: 3,
  },
  {
    program: "Cash — Fully Refundable Fare",
    type: "cash",
    icon: "💳",
    cancelCost: "$0 — 100% refund",
    changeAllowed: "Yes — unlimited",
    deadline: "Usually up to 24 hrs before departure",
    refundMethod: "Full refund to card in 7–10 business days",
    hedgeFriendly: true,
    notes: "The gold standard for hedging. Costs more upfront (usually 40–80% premium vs non-refundable), but zero risk. Book through airline direct website, select 'Flexible' or 'Fully Refundable' fare class explicitly.",
    rating: 5,
  },
  {
    program: "Cash — 24-Hour Rule (any airline)",
    type: "cash",
    icon: "⏱️",
    cancelCost: "$0 within 24 hrs of booking",
    changeAllowed: "Cancel only in 24-hr window",
    deadline: "Must cancel within 24 hrs of original booking",
    refundMethod: "Full refund if travel is 7+ days away",
    hedgeFriendly: true,
    notes: "US law requires all airlines to allow free cancellation within 24 hrs of booking as long as departure is 7+ days away. Use this to test-book and compare before committing.",
    rating: 4,
  },
  {
    program: "AA Staff Standby (Jetnet)",
    type: "staff",
    icon: "👤",
    cancelCost: "$0 — no booking to cancel",
    changeAllowed: "N/A — just show up or don't",
    deadline: "Register up to departure day",
    refundMethod: "Nothing to refund",
    hedgeFriendly: true,
    notes: "Ultimate hedge-friendly option. No commitment until you physically board the plane. Perfect anchor position. Register for multiple dates simultaneously.",
    rating: 5,
  },
];

// ─── DAILY CHECKLIST ─────────────────────────────────────────────
const DAILY_CHECKS = [
  {
    day: "TODAY (Day 0)",
    urgency: "🚨",
    urgencyColor: "bg-red-900/60 border-red-600/40",
    tasks: [
      { task: "Register AA standby on Jetnet for April 5, 8, and 9 LAX→NRT simultaneously", tool: "Jetnet", time: "10 min" },
      { task: "Search seats.aero for LAX→NRT and LAX→SIN business class award space", tool: "seats.aero (free)", time: "5 min" },
      { task: "Search ANA Mileage Club for LAX→NRT business OW — if found, transfer Amex MR and book", tool: "ana.co.jp", time: "20 min" },
      { task: "Check KrisFlyer Spontaneous Escapes for LAX→SIN→DPS PE", tool: "singaporeair.com", time: "10 min" },
      { task: "Book NRT→DPS or SIN→DPS short hop (cash economy) — this leg only gets more expensive", tool: "Google Flights", time: "5 min" },
    ],
  },
  {
    day: "Days 1–3 (Daily until booked)",
    urgency: "📅",
    urgencyColor: "bg-blue-900/60 border-blue-600/40",
    tasks: [
      { task: "Check seats.aero for new award space on LAX→NRT/SIN/HKG business class", tool: "seats.aero", time: "3 min" },
      { task: "Check AA Jetnet for load factors on registered standby flights — look for D1 seats opening", tool: "Jetnet", time: "3 min" },
      { task: "Check Google Flights price alerts for LAX→DPS business fare drops", tool: "Google Flights", time: "2 min" },
      { task: "If ANA space appears — transfer Amex MR immediately (transfers are instant)", tool: "amextravel.com → Transfer", time: "10 min" },
    ],
  },
  {
    day: "3–5 Days Before Departure",
    urgency: "⚡",
    urgencyColor: "bg-violet-900/60 border-violet-600/40",
    tasks: [
      { task: "Airlines release last-minute premium cabin seats — do a full sweep of all programs NOW", tool: "seats.aero + award programs", time: "15 min" },
      { task: "Check seat maps on all registered/booked flights — how many D1 seats open?", tool: "flightradar24.com or ExpertFlyer", time: "5 min" },
      { task: "Assess: hold all positions, cancel weakest one, or double down?", tool: "Your judgment", time: "5 min" },
      { task: "If holding cash refundable + points award: decide if you want to keep both until day-before", tool: "Policy review tab", time: "5 min" },
    ],
  },
  {
    day: "Day Before / Day Of",
    urgency: "🎯",
    urgencyColor: "bg-emerald-900/60 border-emerald-600/40",
    tasks: [
      { task: "Check in online if you have a confirmed booking (points or cash)", tool: "Airline app", time: "3 min" },
      { task: "For standby: do NOT check in online — go to airport 3+ hrs early, speak to gate agent", tool: "AA Gate Agent", time: "—" },
      { task: "Cancel any positions you're NOT taking — recover miles and/or cash refund", tool: "Each airline/program portal", time: "10 min" },
      { task: "If on standby and seat offered: check location (window/aisle vs middle) before accepting", tool: "Gate agent", time: "—" },
      { task: "If standby seat is unacceptable: decline gracefully, use your confirmed booking", tool: "Gate agent + airline app", time: "—" },
    ],
  },
];

// ─── HYBRID PACKAGES (condensed) ─────────────────────────────────
const HYBRID_PACKAGES = [
  {
    rank: 1, label: "🌟 AA Standby + Cash Short Hop", badge: "bg-amber-600",
    cardBg: "bg-amber-950/30 border-amber-600/30", staffOnly: true,
    leg1: { route: "LAX → NRT", hours: "11.5 hrs", cabin: "D1 standby", cost: "~$50", type: "staff" },
    leg2: { route: "NRT → DPS", hours: "7.5 hrs", cabin: "Economy", cost: "$120–250", type: "cash" },
    total: "~$170–300 if standby clears", risk: "HIGH — not guaranteed", refundable: "N/A — no commitment until boarding",
  },
  {
    rank: 2, label: "⚡ ANA Miles + Budget Hop", badge: "bg-blue-600",
    cardBg: "bg-blue-950/30 border-blue-600/30", staffOnly: false,
    leg1: { route: "LAX → NRT", hours: "11.5 hrs", cabin: "Business (The Room)", cost: "40K ANA miles", type: "points" },
    leg2: { route: "NRT → DPS", hours: "7.5 hrs", cabin: "Economy", cost: "$120–250", type: "cash" },
    total: "40K miles + $150–300 cash", risk: "LOW", refundable: "Cancel for ~$100, miles returned",
  },
  {
    rank: 3, label: "🇸🇬 KrisFlyer PE + Scoot", badge: "bg-emerald-600",
    cardBg: "bg-emerald-950/30 border-emerald-600/30", staffOnly: false,
    leg1: { route: "LAX → SIN", hours: "17.5 hrs", cabin: "Premium Economy", cost: "78.5K KrisFlyer miles", type: "points" },
    leg2: { route: "SIN → DPS", hours: "2.5 hrs", cabin: "Economy", cost: "$30–80", type: "cash" },
    total: "78.5K miles + $50–100 cash", risk: "VERY LOW", refundable: "Cancel for $75, miles returned",
  },
  {
    rank: 4, label: "💼 Refundable Cash Anchor", badge: "bg-rose-600",
    cardBg: "bg-rose-950/30 border-rose-600/30", staffOnly: false,
    leg1: { route: "LAX → NRT or SIN", hours: "11–17 hrs", cabin: "Business Class", cost: "$2,700–3,500 RT", type: "cash" },
    leg2: { route: "included", hours: "—", cabin: "included", cost: "included", type: "cash" },
    total: "$2,700–3,500 RT fully refundable", risk: "NONE — cancel anytime", refundable: "100% refund to card",
  },
];

// ── COMPONENT ─────────────────────────────────────────────────────
export default function AirlineBookerBali() {
  const [activeTab, setActiveTab] = useState(0);
  const [expandedPS, setExpandedPS] = useState("ps1");

  const typeBadge = (type) => {
    const map = {
      staff: "bg-amber-900/60 border-amber-600/40 text-amber-200",
      points: "bg-indigo-900/60 border-indigo-600/40 text-indigo-200",
      cash: "bg-emerald-900/60 border-emerald-600/40 text-emerald-200",
    };
    const label = { staff: "Staff Travel", points: "Points", cash: "Cash" };
    return <span className={`text-xs border px-2 py-0.5 rounded-full font-semibold ${map[type]}`}>{label[type]}</span>;
  };

  const stars = (n) => Array.from({ length: 5 }, (_, i) => (
    <span key={i} className={i < n ? "text-yellow-400" : "text-gray-700"}>★</span>
  ));

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 font-sans">

      {/* HEADER */}
      <div className="bg-gradient-to-br from-slate-900 via-indigo-950 to-violet-950 px-6 pt-8 pb-0 border-b border-white/10">
        <div className="max-w-5xl mx-auto">
          <div className="flex items-start justify-between flex-wrap gap-4 mb-4">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="text-lg">✈️</span>
                <span className="text-xs font-bold tracking-widest text-indigo-400 uppercase">Airline Booker · ARC Brain</span>
              </div>
              <h1 className="text-2xl font-bold text-white tracking-tight">LAX → Denpasar, Bali · April 1–14</h1>
              <p className="text-indigo-300 mt-0.5 text-sm">Hedge Portfolio Engine · Availability Scanner · Beryl Jacobson</p>
            </div>
            <div className="flex flex-wrap gap-1.5 justify-end items-start pt-1">
              {["AA Staff", "myIDtravel", "Amex MR", "Chase UR", "Hawaiian→Alaska"].map(p => (
                <span key={p} className="bg-white/10 border border-white/20 text-gray-200 text-xs px-2.5 py-1 rounded-full">{p}</span>
              ))}
            </div>
          </div>

          {/* Core Philosophy */}
          <div className="grid grid-cols-3 gap-2 mb-4 text-xs">
            <div className="bg-amber-950/50 border border-amber-700/40 rounded-xl p-3">
              <div className="text-amber-300 font-bold mb-1">📌 Position, Don't Commit</div>
              <div className="text-amber-200/70">Hold 2–3 refundable/cancelable positions simultaneously. Collapse to the best one as you approach the date.</div>
            </div>
            <div className="bg-indigo-950/50 border border-indigo-700/40 rounded-xl p-3">
              <div className="text-indigo-300 font-bold mb-1">📡 Check Daily</div>
              <div className="text-indigo-200/70">Premium cabin seats release on rolling basis. New award inventory appears 14–2 days out. Tuesday–Thursday are best days for new space.</div>
            </div>
            <div className="bg-emerald-950/50 border border-emerald-700/40 rounded-xl p-3">
              <div className="text-emerald-300 font-bold mb-1">🔀 Hybrid-First</div>
              <div className="text-emerald-200/70">Lay-flat on the long haul (&gt;8 hrs). Economy on the short hop (&lt;4 hrs). Split the legs. Save 20–40K miles vs booking through.</div>
            </div>
          </div>

          {/* TIMING ALERT */}
          <div className="bg-red-950/50 border border-red-700/40 rounded-xl px-4 py-3 mb-4 flex gap-3">
            <span className="text-red-300 text-base">⚠️</span>
            <div>
              <p className="text-red-200 text-sm font-bold">April 8–10 is your best availability window — start hedging now</p>
              <p className="text-red-200/70 text-xs mt-0.5">Mid-month mid-week has historically the lightest transpacific premium load. Register standby for Apr 8 AND 9. Book a cancelable award for same dates as insurance. You can always cancel either.</p>
            </div>
          </div>

          {/* TABS */}
          <div className="flex overflow-x-auto -mb-px gap-0.5">
            {TABS.map((tab, i) => (
              <button key={i} onClick={() => setActiveTab(i)}
                className={`px-4 py-3 text-sm font-medium whitespace-nowrap border-b-2 transition-all ${
                  activeTab === i ? "border-indigo-400 text-indigo-300 bg-white/5 rounded-t-lg" : "border-transparent text-gray-400 hover:text-gray-200"
                }`}>
                {tab}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-4 py-6">

        {/* ── TAB 0: 5-DAY BRIEF ── */}
        {activeTab === 0 && (
          <div className="space-y-4">

            {/* Hard Deadline Alert */}
            <div className="bg-red-950/60 border-2 border-red-500/60 rounded-2xl p-5">
              <div className="flex gap-3 items-start">
                <span className="text-2xl">⏱️</span>
                <div>
                  <h3 className="text-red-200 font-bold text-base mb-1">5 Days Out — Hard Deadlines Active</h3>
                  <div className="space-y-1.5 text-sm">
                    <div className="flex gap-2"><span className="text-red-400 font-bold w-32 flex-shrink-0">ANA Awards:</span><span className="text-red-200">4-day minimum rule. Must book by <strong>tomorrow March 27</strong> for March 31 departure. March 28 for April 1. March 29 for April 2.</span></div>
                    <div className="flex gap-2"><span className="text-red-400 font-bold w-32 flex-shrink-0">KrisFlyer:</span><span className="text-red-200">Can book closer — Spontaneous Escapes sometimes allows 24–48 hrs out. Still check today.</span></div>
                    <div className="flex gap-2"><span className="text-red-400 font-bold w-32 flex-shrink-0">AA Standby:</span><span className="text-red-200">Register on Jetnet anytime up to departure. No advance required. Freest option.</span></div>
                    <div className="flex gap-2"><span className="text-red-400 font-bold w-32 flex-shrink-0">Cash fares:</span><span className="text-red-200">Available anytime but last-minute business class runs $4,000–5,500 RT.</span></div>
                  </div>
                </div>
              </div>
            </div>

            {/* Visa Actions */}
            <div className="bg-amber-950/40 border border-amber-600/40 rounded-2xl p-5">
              <h3 className="text-amber-200 font-bold mb-3">🛂 Visas — What to Do Today</h3>
              <div className="space-y-3">
                {[
                  { country: "🇮🇩 Indonesia (Bali)", status: "Required — do TODAY", urgency: "bg-red-900/60 text-red-200 border-red-600/40", detail: "e-VOA online — $35 USD, 30 days. Apply at evisa.imigrasi.go.id — upload passport photo page + photo. Approved in ~1 day. Required regardless of route.", link: "https://evisa.imigrasi.go.id", required: true },
                  { country: "🇦🇺 Australia (Sydney stopover)", status: "Required if routing via SYD", urgency: "bg-yellow-900/60 text-yellow-200 border-yellow-600/40", detail: "ETA subclass 601 — AUD $20 (~$13 USD). Download 'Australian ETA' app on iPhone/Android. Scan passport, answer questions, pay. Approved in minutes.", link: "apps.apple.com — search 'Australian ETA'", required: false },
                  { country: "🇯🇵 Japan (Tokyo hub)", status: "✅ Visa-free 90 days", urgency: "bg-emerald-900/60 text-emerald-200 border-emerald-600/40", detail: "US passport = no visa needed for up to 90 days. Just show up.", link: null, required: false },
                  { country: "🇸🇬 Singapore hub", status: "✅ Visa-free 30 days", urgency: "bg-emerald-900/60 text-emerald-200 border-emerald-600/40", detail: "US passport = no visa needed for transit or stays up to 30 days.", link: null, required: false },
                  { country: "🇭🇰 Hong Kong hub", status: "✅ Visa-free 90 days", urgency: "bg-emerald-900/60 text-emerald-200 border-emerald-600/40", detail: "No visa required.", link: null, required: false },
                  { country: "🇹🇼 Taiwan hub", status: "✅ Visa-free 90 days", urgency: "bg-emerald-900/60 text-emerald-200 border-emerald-600/40", detail: "No visa required.", link: null, required: false },
                ].map((v, i) => (
                  <div key={i} className={`rounded-xl border p-3 ${v.urgency}`}>
                    <div className="flex items-start justify-between gap-2 flex-wrap mb-1">
                      <span className="font-bold text-sm">{v.country}</span>
                      <span className="text-xs font-semibold">{v.status}</span>
                    </div>
                    <p className="text-xs leading-relaxed opacity-80">{v.detail}</p>
                    {v.link && <div className="mt-1 font-mono text-xs opacity-70">{v.link}</div>}
                  </div>
                ))}
              </div>
            </div>

            {/* Route Quick Recommendation */}
            <div className="bg-indigo-950/40 border border-indigo-600/40 rounded-2xl p-5">
              <h3 className="text-indigo-200 font-bold mb-3">🗺️ Best Routes at 5 Days Out</h3>
              <div className="space-y-2 text-sm">
                {[
                  { rank: "1", route: "LAX → NRT → DPS via ANA", why: "Best value if award space exists — MUST book ANA by tomorrow. Otherwise cash ~$4K.", tags: ["points", "urgent"], hours: "~19 hrs" },
                  { rank: "2", route: "LAX → SIN → DPS via Singapore Airlines", why: "KrisFlyer Spontaneous Escapes can book within days. 17.5hr long haul + 2.5hr hop to Bali.", tags: ["points", "available"], hours: "~20 hrs" },
                  { rank: "3", route: "LAX → SYD → DPS — Sydney stopover option", why: "1 night in Sydney, then SYD→DPS. Need Australia ETA (10 min). Qantas lie-flat LAX→SYD.", tags: ["stopover", "first time SYD"], hours: "~21 hrs + 1 night" },
                  { rank: "4", route: "AA Staff Standby LAX → NRT + book NRT→DPS cash", why: "Free if D1 clears. Register on Jetnet now for March 31, April 1, April 2 simultaneously.", tags: ["staff", "free"], hours: "~19 hrs" },
                  { rank: "skip", route: "LAX → JFK → Asia", why: "Wrong direction. Adds 5+ hrs. Only valid if a specific eastbound deal is dramatically cheaper. Skip.", tags: ["skip"], hours: "—" },
                ].map((r, i) => (
                  <div key={i} className={`rounded-xl p-3 flex gap-3 ${r.rank === "skip" ? "bg-red-950/30 border border-red-800/30 opacity-60" : "bg-white/5 border border-white/10"}`}>
                    <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5 ${r.rank === "skip" ? "bg-red-800 text-red-200" : "bg-indigo-700 text-white"}`}>{r.rank === "skip" ? "✕" : r.rank}</div>
                    <div className="flex-1">
                      <div className="text-white font-semibold text-sm">{r.route}</div>
                      <div className="text-gray-400 text-xs mt-0.5">{r.why}</div>
                      <div className="flex gap-1.5 mt-1.5 flex-wrap">
                        {r.tags.map(t => <span key={t} className="bg-white/10 text-gray-300 text-xs px-2 py-0.5 rounded-full">{t}</span>)}
                        <span className="text-gray-500 text-xs ml-auto">{r.hours}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* TODAY's Action Order */}
            <div className="bg-emerald-950/40 border border-emerald-600/40 rounded-2xl p-5">
              <h3 className="text-emerald-200 font-bold mb-3">✅ Do These Right Now (in order)</h3>
              <div className="space-y-2">
                {[
                  { n: 1, action: "Apply for Indonesia e-VOA", detail: "evisa.imigrasi.go.id — $35, takes ~1 day. Do this FIRST regardless of which route you pick.", time: "10 min" },
                  { n: 2, action: "Check ANA Mileage Club for LAX→NRT business", detail: "ana.co.jp → Mileage Award. March 31 or April 1. If available, transfer Amex MR → ANA immediately. Cutoff is TOMORROW for March 31.", time: "15 min" },
                  { n: 3, action: "Register AA standby on Jetnet for March 31, April 1, April 2", detail: "Register all three dates simultaneously. Free. D1 business if it clears. Your zero-cost wildcard.", time: "5 min" },
                  { n: 4, action: "Check KrisFlyer Spontaneous Escapes", detail: "singaporeair.com → Spontaneous Escapes. LAX→SIN→DPS. PE or Business. Most flexible on timing.", time: "10 min" },
                  { n: 5, action: "If doing Sydney: apply for Australia ETA now", detail: "Download 'Australian ETA' app. AUD $20. Approved in minutes. Do it before you need it.", time: "5 min" },
                  { n: 6, action: "Book NRT→DPS or SIN→DPS short hop independently", detail: "This is your anchor leg. Prices only go up. Book it as soon as you know your hub.", time: "5 min" },
                ].map(a => (
                  <div key={a.n} className="flex gap-3 bg-black/20 rounded-lg p-3">
                    <div className="bg-emerald-700 text-white w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5">{a.n}</div>
                    <div className="flex-1">
                      <div className="text-white text-sm font-semibold">{a.action}</div>
                      <div className="text-gray-400 text-xs mt-0.5">{a.detail}</div>
                    </div>
                    <div className="text-gray-500 text-xs flex-shrink-0 mt-1">{a.time}</div>
                  </div>
                ))}
              </div>
            </div>

          </div>
        )}

        {/* ── TAB 1: HEDGE PORTFOLIO ── */}
        {activeTab === 1 && (
          <div className="space-y-6">
            {PORTFOLIO_STRATEGIES.map((ps) => (
              <div key={ps.id} className={`rounded-2xl border ${ps.cardBg} overflow-hidden`}>
                <button className="w-full text-left p-5 pb-3" onClick={() => setExpandedPS(expandedPS === ps.id ? null : ps.id)}>
                  <div className="flex items-start justify-between flex-wrap gap-2">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className={`${ps.badge} text-white text-xs font-bold px-3 py-1 rounded-full`}>{ps.label}</span>
                      <span className={`text-xs font-semibold ${ps.riskColor}`}>{ps.riskLevel}</span>
                    </div>
                    <span className="text-gray-400 text-lg">{expandedPS === ps.id ? "▲" : "▼"}</span>
                  </div>
                  <p className="text-white font-bold text-base mt-2">{ps.tagline}</p>
                  <p className="text-gray-400 text-xs mt-0.5">{ps.totalExposure}</p>
                </button>

                {expandedPS === ps.id && (
                  <div className="px-5 pb-5">
                    {/* Positions */}
                    <div className="space-y-3 mb-4">
                      <div className="text-xs text-gray-500 font-semibold uppercase tracking-wider">Your open positions</div>
                      {ps.positions.map((pos) => (
                        <div key={pos.slot} className="bg-black/30 rounded-xl p-4 border border-white/5">
                          <div className="flex items-start justify-between gap-2 mb-2 flex-wrap">
                            <div className="flex items-center gap-2">
                              <span className={`${pos.color} text-white text-xs font-black w-6 h-6 rounded-full flex items-center justify-center`}>{pos.slot}</span>
                              <span className="text-white font-semibold text-sm">{pos.label}</span>
                              {typeBadge(pos.type)}
                            </div>
                            <div className="text-right">
                              <div className="text-white font-bold text-sm">{pos.cost}</div>
                            </div>
                          </div>
                          <div className="text-gray-300 text-xs mb-2">{pos.route} · {pos.dates} · <span className="text-indigo-300">{pos.cabin}</span></div>
                          <div className="grid grid-cols-2 gap-2 text-xs mb-2">
                            <div className="bg-white/5 rounded-lg p-2">
                              <div className="text-gray-500 mb-0.5">Cancel policy</div>
                              <div className="text-gray-200">{pos.cancelPolicy}</div>
                              <div className="text-emerald-400 font-bold mt-0.5">Fee: {pos.cancelFee}</div>
                            </div>
                            <div className="bg-white/5 rounded-lg p-2">
                              <div className="text-gray-500 mb-0.5">Where to book</div>
                              <div className="font-mono text-indigo-300 text-xs">{pos.bookWhere}</div>
                            </div>
                          </div>
                          <div className="bg-indigo-950/50 border border-indigo-700/30 rounded px-2 py-1.5 text-xs text-indigo-200">
                            <span className="text-indigo-400 font-bold">Priority: </span>{pos.priority}
                          </div>
                        </div>
                      ))}
                    </div>

                    {/* Collapse Logic */}
                    <div>
                      <div className="text-xs text-gray-500 font-semibold uppercase tracking-wider mb-2">When to collapse → what to do</div>
                      <div className="space-y-2">
                        {ps.collapseLogic.map((cl, i) => (
                          <div key={i} className="bg-white/5 rounded-lg p-3 flex gap-3">
                            <span className="text-lg flex-shrink-0 mt-0.5">{cl.emoji}</span>
                            <div>
                              <div className="text-white text-xs font-semibold mb-0.5">If: {cl.trigger}</div>
                              <div className="text-gray-300 text-xs">→ {cl.action}</div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* ── TAB 2: AVAILABILITY INTEL ── */}
        {activeTab === 2 && (
          <div className="space-y-6">
            {/* Date Windows */}
            <div>
              <h3 className="text-white font-bold mb-3">📅 Best Date Windows for Premium Cabin Availability</h3>
              <div className="space-y-2">
                {AVAIL_WINDOWS.map((w, i) => (
                  <div key={i} className="bg-gray-800/50 rounded-xl border border-white/10 p-4">
                    <div className="flex items-start justify-between flex-wrap gap-2 mb-2">
                      <div className="flex items-center gap-3">
                        <div className={`w-3 h-3 rounded-full ${w.dotColor} flex-shrink-0 mt-0.5`} />
                        <span className="text-white font-bold text-sm">{w.dates}</span>
                      </div>
                      <div className="flex gap-2 text-xs">
                        <span className={`font-semibold ${w.loadColor}`}>Business: {w.businessLoad}</span>
                        <span className="text-gray-500">|</span>
                        <span className={`font-semibold ${w.loadColor}`}>PE: {w.peLoad}</span>
                      </div>
                    </div>
                    <p className="text-gray-400 text-xs mb-1.5">{w.reason}</p>
                    <p className="text-gray-200 text-xs">{w.recommendation}</p>
                    <div className="mt-1.5 text-xs text-amber-300">
                      <span className="text-gray-500">Standby chance: </span>
                      <span className="font-semibold">{w.staffChance}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Seat Tips */}
            <div>
              <h3 className="text-white font-bold mb-3">🛠️ Availability Hacks</h3>
              <div className="grid md:grid-cols-2 gap-3">
                {SEAT_TIPS.map((tip, i) => (
                  <div key={i} className="bg-gray-800/50 rounded-xl border border-white/10 p-4">
                    <div className="flex items-start gap-2 mb-1.5">
                      <span className="text-xl flex-shrink-0">{tip.icon}</span>
                      <h4 className="text-white text-sm font-bold">{tip.title}</h4>
                    </div>
                    <p className="text-gray-400 text-xs leading-relaxed">{tip.detail}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ── TAB 3: HYBRID PACKAGES ── */}
        {activeTab === 3 && (
          <div className="space-y-4">
            <p className="text-gray-400 text-sm">Each package shows the leg split — optimize the long haul, don't sweat the short hop. Each is independently bookable and cancelable.</p>
            {HYBRID_PACKAGES.map((pkg) => (
              <div key={pkg.rank} className={`rounded-2xl border ${pkg.cardBg} p-5`}>
                <div className="flex items-start justify-between flex-wrap gap-2 mb-3">
                  <div className="flex items-center gap-2">
                    <span className={`${pkg.badge} text-white text-xs font-bold px-3 py-1 rounded-full`}>{pkg.label}</span>
                    {pkg.staffOnly && <span className="bg-amber-700/60 text-amber-200 text-xs px-2 py-0.5 rounded-full border border-amber-600/40 font-semibold">👤 Staff access</span>}
                  </div>
                  <div className="text-right">
                    <div className="text-white font-bold text-sm">{pkg.total}</div>
                    <div className="text-xs text-gray-400 mt-0.5">Risk: <span className={pkg.risk.startsWith("HIGH") ? "text-red-400" : pkg.risk.startsWith("NONE") || pkg.risk.startsWith("VERY") ? "text-emerald-400" : "text-yellow-400"}>{pkg.risk}</span></div>
                  </div>
                </div>

                <div className="space-y-2 mb-3">
                  {[pkg.leg1, pkg.leg2].map((leg, i) => leg.route !== "included" ? (
                    <div key={i} className="bg-black/20 rounded-lg p-3 flex items-center justify-between gap-3 flex-wrap">
                      <div>
                        <div className="flex items-center gap-2 mb-0.5">
                          <span className="bg-gray-700 text-gray-300 text-xs font-bold px-1.5 py-0.5 rounded">LEG {i + 1}</span>
                          {typeBadge(leg.type)}
                        </div>
                        <div className="text-white text-sm font-medium">{leg.route}</div>
                        <div className="text-gray-400 text-xs">{leg.hours} · <span className="text-indigo-300">{leg.cabin}</span></div>
                      </div>
                      <div className="text-right">
                        <div className="text-white font-bold text-sm">{leg.cost}</div>
                      </div>
                    </div>
                  ) : null)}
                </div>

                <div className="bg-white/5 rounded-lg px-3 py-2 text-xs">
                  <span className="text-gray-400">Cancel: </span>
                  <span className="text-emerald-300">{pkg.refundable}</span>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* ── TAB 4: CANCELLATION POLICIES ── */}
        {activeTab === 4 && (
          <div className="space-y-4">
            <p className="text-gray-400 text-sm">Know exactly what each position costs to exit before you enter it. That's how you hedge without anxiety.</p>
            {CANCEL_POLICIES.map((p, i) => (
              <div key={i} className={`bg-gray-800/50 rounded-2xl border ${p.hedgeFriendly ? "border-emerald-700/30" : "border-white/10"} p-5`}>
                <div className="flex items-start justify-between flex-wrap gap-2 mb-3">
                  <div className="flex items-center gap-2">
                    <span className="text-xl">{p.icon}</span>
                    <div>
                      <h3 className="text-white font-bold text-sm">{p.program}</h3>
                      <div className="flex items-center gap-2 mt-0.5">
                        {typeBadge(p.type)}
                        {p.hedgeFriendly && <span className="text-xs text-emerald-400 font-semibold">✓ Hedge-friendly</span>}
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-emerald-400 font-bold text-sm">{p.cancelCost}</div>
                    <div className="mt-0.5">{stars(p.rating)}</div>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-2 text-xs mb-3">
                  <div className="bg-white/5 rounded-lg p-2">
                    <div className="text-gray-500 mb-0.5">Changes allowed</div>
                    <div className="text-gray-200">{p.changeAllowed}</div>
                  </div>
                  <div className="bg-white/5 rounded-lg p-2">
                    <div className="text-gray-500 mb-0.5">Deadline</div>
                    <div className="text-gray-200">{p.deadline}</div>
                  </div>
                  <div className="bg-white/5 rounded-lg p-2">
                    <div className="text-gray-500 mb-0.5">Refund method</div>
                    <div className="text-gray-200">{p.refundMethod}</div>
                  </div>
                </div>

                <p className="text-gray-400 text-xs leading-relaxed">{p.notes}</p>
              </div>
            ))}
          </div>
        )}

        {/* ── TAB 5: DAILY CHECKLIST ── */}
        {activeTab === 5 && (
          <div className="space-y-5">
            <p className="text-gray-400 text-sm">Your rolling checklist from today through departure. Each phase takes under 15 minutes.</p>
            {DAILY_CHECKS.map((phase, i) => (
              <div key={i} className={`rounded-2xl border ${phase.urgencyColor} p-5`}>
                <div className="flex items-center gap-2 mb-3">
                  <span className="text-base">{phase.urgency}</span>
                  <h3 className="text-white font-bold text-sm">{phase.day}</h3>
                </div>
                <div className="space-y-2">
                  {phase.tasks.map((t, j) => (
                    <div key={j} className="bg-black/20 rounded-lg p-3 flex items-start gap-3">
                      <div className="w-4 h-4 rounded border border-gray-600 flex-shrink-0 mt-0.5" />
                      <div className="flex-1">
                        <div className="text-gray-200 text-sm">{t.task}</div>
                        <div className="flex items-center gap-3 mt-1">
                          <span className="text-indigo-400 font-mono text-xs">{t.tool}</span>
                          {t.time !== "—" && <span className="text-gray-500 text-xs">~{t.time}</span>}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}

            {/* Smart Reminder */}
            <div className="bg-gradient-to-r from-indigo-950/60 to-violet-950/60 border border-indigo-600/30 rounded-2xl p-5">
              <h4 className="text-indigo-200 font-bold mb-2">💡 The Hedge Mindset</h4>
              <p className="text-indigo-200/70 text-sm leading-relaxed">
                You're not trying to predict the future — you're buying options. Register standby (free). Book an award (cancelable for ~$100). If cash refundable, book that too (zero cost to cancel). The worst outcome is you pay one small cancel fee. The best outcome is you're in D1 to Tokyo for $50 and fly to Bali from there on $150. The system works because you act before you commit.
              </p>
            </div>
          </div>
        )}

      </div>

      <div className="border-t border-white/5 bg-gray-900 px-6 py-3">
        <div className="max-w-5xl mx-auto flex justify-between flex-wrap gap-2 text-xs text-gray-600">
          <span>Airline Booker · ARC Brain · March 25, 2026</span>
          <span>Hedge Portfolio Engine v1 · LAX→DPS April 2026</span>
        </div>
      </div>
    </div>
  );
}
