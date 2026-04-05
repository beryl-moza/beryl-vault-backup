import { useState } from "react";

// ═══════════════════════════════════════════════════════════════
// AIRLINE BOOKER — Simple Search Template
// MODE: Simple — best price, clear reasoning, direct booking
// Use this template when: booking for someone, domestic routes,
//   no points needed, user wants "just find me the best flight"
//
// HOW TO USE THIS TEMPLATE:
// 1. Replace TRIP_META with the actual trip details
// 2. Replace LIVE_TRIPS with real search results
// 3. Replace INSIGHTS with route-specific patterns found
// 4. Replace ACTIONS with actual booking links
// ═══════════════════════════════════════════════════════════════

// ── CUSTOMIZE THIS PER SEARCH ─────────────────────────────────

const TRIP_META = {
  traveler: "Emunah",           // who is traveling
  purpose: "Visit Grammy",       // why
  origin: "Chicago (ORD/MDW)",  // origin with airport codes
  destination: "Sarasota (SRQ/TPA/PGD)", // dest with airports
  dates: "Any weekend in April 2026",
  passengers: "1 adult",
  searchedAt: "March 16, 2026",
  notes: "Searched all 4 April weekends × all airport combos",
};

// ── LIVE SEARCH RESULTS ───────────────────────────────────────
// Replace with real flights found via Google Flights / airline sites
// Each entry is a complete roundtrip recommendation

const LIVE_TRIPS = [
  {
    rank: 1,
    label: "Top Pick",
    badgeColor: "bg-green-600",
    cardColor: "border-green-400 bg-green-50",
    priceLevel: "typical",        // "cheap" | "typical" | "expensive"
    price: 309,                    // total roundtrip USD
    outbound: {
      airline: "American",
      flight: "AA Nonstop",
      date: "Thu Apr 16",
      depart: "7:59 PM",
      arrive: "11:47 PM",
      origin: "ORD",
      destination: "SRQ",
      stops: 0,
      duration: "2h 48m",
    },
    returnFlight: {
      airline: "American",
      flight: "AA 1-stop (CLT)",
      date: "Sun Apr 19",
      depart: "7:43 PM",
      arrive: "11:54 PM",
      origin: "SRQ",
      destination: "ORD",
      stops: 1,
      duration: "5h 11m",
    },
    insight: "BEST DEAL! Thu evening out, late Sun evening back. Full Fri/Sat/Sun with Grammy.",
    returnOptions: [
      { time: "8:46 AM → 10:55 AM", type: "Nonstop", note: "If she wants to leave early" },
      { time: "7:43 PM → 11:54 PM", type: "1-stop CLT", note: "Latest & cheapest return" },
    ],
  },
  {
    rank: 2,
    label: "Same Price, Week Later",
    badgeColor: "bg-green-500",
    cardColor: "border-green-300 bg-green-50",
    priceLevel: "typical",
    price: 309,
    outbound: {
      airline: "American",
      flight: "AA Nonstop",
      date: "Thu Apr 23",
      depart: "7:59 PM",
      arrive: "11:47 PM",
      origin: "ORD",
      destination: "SRQ",
      stops: 0,
      duration: "2h 48m",
    },
    returnFlight: {
      airline: "American",
      flight: "AA 1-stop (CLT)",
      date: "Sun Apr 26",
      depart: "7:43 PM",
      arrive: "11:54 PM",
      origin: "SRQ",
      destination: "ORD",
      stops: 1,
      duration: "5h 11m",
    },
    insight: "Identical flight/price one week later. Pick whichever weekend works better.",
    returnOptions: [
      { time: "7:43 PM → 11:54 PM", type: "1-stop CLT", note: "Cheapest return" },
    ],
  },
  {
    rank: 3,
    label: "Budget Winner",
    badgeColor: "bg-amber-500",
    cardColor: "border-amber-300 bg-amber-50",
    priceLevel: "cheap",
    price: 176,
    outbound: {
      airline: "Allegiant",
      flight: "G4 Nonstop",
      date: "Thu Apr 16",
      depart: "9:16 AM",
      arrive: "1:05 PM",
      origin: "MDW",
      destination: "PGD",
      stops: 0,
      duration: "2h 49m",
    },
    returnFlight: {
      airline: "Allegiant",
      flight: "G4 Nonstop",
      date: "Sun Apr 19",
      depart: "1:45 PM",
      arrive: "4:35 PM",
      origin: "PGD",
      destination: "MDW",
      stops: 0,
      duration: "2h 50m",
    },
    insight: "$133 cheaper than AA picks. Uses MDW + PGD (60 min from Sarasota). Good if Grammy can pick up.",
    returnOptions: [],
  },
];

// ── SMART INSIGHTS ────────────────────────────────────────────
// Patterns found across all the dates/airports searched

const INSIGHTS = [
  "April 16–19 and 23–26 weekends are identical in price — both are great",
  "ORD is ~$30–50 more than MDW on this route but much more convenient",
  "Allegiant via MDW→PGD saves $130+ but PGD is 60 min from Sarasota city center",
  "Nonstop options exist on American (ORD→SRQ) and Allegiant (MDW→PGD)",
  "Apr 3–5 weekend was ~$50 more expensive — skip it",
];

// ── ACTION ITEMS ─────────────────────────────────────────────

const ACTIONS = [
  {
    step: 1,
    title: "Book Top Pick on Google Flights",
    detail: "Search ORD → SRQ, Thu Apr 16, return Sun Apr 19 on American. Select nonstop outbound + 1-stop return via CLT.",
    link: "https://flights.google.com",
  },
  {
    step: 2,
    title: "Or book directly on aa.com",
    detail: "American Airlines direct often matches Google Flights price and gives easier management.",
    link: "https://www.aa.com",
  },
  {
    step: 3,
    title: "Budget option: book on Allegiant",
    detail: "MDW → PGD, $176 roundtrip. Only if Grammy can drive 60 min to pick up at Punta Gorda airport.",
    link: "https://www.allegiantair.com",
  },
];

// ─────────────────────────────────────────────────────────────
// COMPONENT — don't need to edit below this line
// ─────────────────────────────────────────────────────────────

export default function SimpleSearchDashboard() {
  const [expandedCard, setExpandedCard] = useState(0);

  const priceTag = (level) => {
    const map = {
      cheap: "bg-green-100 text-green-800",
      typical: "bg-gray-100 text-gray-700",
      expensive: "bg-red-100 text-red-800",
    };
    const label = { cheap: "Below average price", typical: "Typical price", expensive: "Above average" };
    return <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${map[level]}`}>{label[level]}</span>;
  };

  const stopsBadge = (n) =>
    n === 0
      ? <span className="text-xs bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded-full font-medium">Nonstop</span>
      : <span className="text-xs bg-gray-100 text-gray-700 px-2 py-0.5 rounded-full">{n} stop</span>;

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900 font-sans">

      {/* HEADER */}
      <div className="bg-white border-b border-gray-200 px-6 py-5 shadow-sm">
        <div className="max-w-3xl mx-auto">
          <div className="flex items-start justify-between gap-3 flex-wrap">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span>✈️</span>
                <span className="text-xs font-semibold tracking-widest text-gray-400 uppercase">Airline Booker</span>
              </div>
              <h1 className="text-2xl font-bold text-gray-900">
                {TRIP_META.origin} → {TRIP_META.destination}
              </h1>
              <p className="text-gray-500 text-sm mt-0.5">
                {TRIP_META.traveler} · {TRIP_META.purpose} · {TRIP_META.dates}
              </p>
            </div>
            <div className="text-right text-xs text-gray-400">
              <div>{TRIP_META.passengers}</div>
              <div>Searched {TRIP_META.searchedAt}</div>
              <div className="text-gray-300 mt-0.5">{TRIP_META.notes}</div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-3xl mx-auto px-4 py-6 space-y-4">

        {/* RESULTS */}
        {LIVE_TRIPS.map((trip) => (
          <div
            key={trip.rank}
            className={`rounded-2xl border-2 overflow-hidden transition-all cursor-pointer ${trip.cardColor} ${expandedCard === trip.rank ? "shadow-md" : "shadow-sm hover:shadow-md"}`}
            onClick={() => setExpandedCard(expandedCard === trip.rank ? null : trip.rank)}
          >
            <div className="p-5">
              {/* Card header */}
              <div className="flex items-start justify-between gap-2 mb-3 flex-wrap">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className={`${trip.badgeColor} text-white text-xs font-bold px-3 py-1 rounded-full`}>
                    #{trip.rank} {trip.label}
                  </span>
                  {priceTag(trip.priceLevel)}
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold text-gray-900">${trip.price}</div>
                  <div className="text-xs text-gray-500">roundtrip per person</div>
                </div>
              </div>

              {/* Insight line */}
              <p className="text-sm font-medium text-gray-700 mb-3">{trip.insight}</p>

              {/* Outbound */}
              <div className="bg-white/70 rounded-xl p-3 mb-2">
                <div className="flex items-center justify-between flex-wrap gap-1 mb-1">
                  <span className="text-xs font-semibold text-gray-500 uppercase">Outbound · {trip.outbound.date}</span>
                  {stopsBadge(trip.outbound.stops)}
                </div>
                <div className="flex items-center gap-2 text-sm flex-wrap">
                  <span className="font-bold text-gray-900">{trip.outbound.depart}</span>
                  <span className="text-gray-400">{trip.outbound.origin}</span>
                  <span className="text-gray-300">→</span>
                  <span className="font-bold text-gray-900">{trip.outbound.arrive}</span>
                  <span className="text-gray-400">{trip.outbound.destination}</span>
                  <span className="text-gray-400 text-xs ml-auto">{trip.outbound.airline} · {trip.outbound.duration}</span>
                </div>
              </div>

              {/* Return */}
              <div className="bg-white/70 rounded-xl p-3">
                <div className="flex items-center justify-between flex-wrap gap-1 mb-1">
                  <span className="text-xs font-semibold text-gray-500 uppercase">Return · {trip.returnFlight.date}</span>
                  {stopsBadge(trip.returnFlight.stops)}
                </div>
                <div className="flex items-center gap-2 text-sm flex-wrap">
                  <span className="font-bold text-gray-900">{trip.returnFlight.depart}</span>
                  <span className="text-gray-400">{trip.returnFlight.origin}</span>
                  <span className="text-gray-300">→</span>
                  <span className="font-bold text-gray-900">{trip.returnFlight.arrive}</span>
                  <span className="text-gray-400">{trip.returnFlight.destination}</span>
                  <span className="text-gray-400 text-xs ml-auto">{trip.returnFlight.airline} · {trip.returnFlight.duration}</span>
                </div>
              </div>

              {/* Expanded: return options */}
              {expandedCard === trip.rank && trip.returnOptions.length > 0 && (
                <div className="mt-3">
                  <div className="text-xs font-semibold text-gray-500 uppercase mb-2">Other return options</div>
                  <div className="space-y-1.5">
                    {trip.returnOptions.map((opt, i) => (
                      <div key={i} className="bg-white/60 rounded-lg px-3 py-2 flex items-center justify-between gap-2 text-xs">
                        <span className="font-mono text-gray-700">{opt.time}</span>
                        <span className="text-gray-500">{opt.type}</span>
                        <span className="text-gray-400">{opt.note}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}

        {/* INSIGHTS */}
        <div className="bg-white rounded-2xl border border-gray-200 p-5 shadow-sm">
          <h3 className="font-bold text-gray-800 mb-3">💡 What We Found</h3>
          <ul className="space-y-2">
            {INSIGHTS.map((insight, i) => (
              <li key={i} className="flex gap-2 text-sm text-gray-600">
                <span className="text-gray-300 flex-shrink-0 mt-0.5">•</span>
                <span>{insight}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* ACTIONS */}
        <div className="bg-white rounded-2xl border border-gray-200 p-5 shadow-sm">
          <h3 className="font-bold text-gray-800 mb-3">🎯 Book It</h3>
          <div className="space-y-3">
            {ACTIONS.map((a) => (
              <div key={a.step} className="flex gap-3">
                <div className="bg-gray-100 text-gray-600 text-xs font-bold w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                  {a.step}
                </div>
                <div>
                  <div className="text-sm font-semibold text-gray-800">{a.title}</div>
                  <div className="text-sm text-gray-500 mt-0.5">{a.detail}</div>
                  {a.link && (
                    <div className="mt-1 font-mono text-blue-500 text-xs">{a.link}</div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>

      <div className="border-t border-gray-100 bg-white px-6 py-3 mt-4">
        <div className="max-w-3xl mx-auto text-xs text-gray-400 flex justify-between flex-wrap gap-1">
          <span>Airline Booker · Simple Search · {TRIP_META.searchedAt}</span>
          <span>For power mode (points, hybrid, hedge) use power_search_dashboard.jsx</span>
        </div>
      </div>
    </div>
  );
}
