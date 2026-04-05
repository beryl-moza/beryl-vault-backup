import { useState, useEffect } from "react";

const SunIcon = () => (
  <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
    <circle cx="24" cy="24" r="10" fill="#FBBF24" />
    <g stroke="#FBBF24" strokeWidth="3" strokeLinecap="round">
      <line x1="24" y1="2" x2="24" y2="8" />
      <line x1="24" y1="40" x2="24" y2="46" />
      <line x1="2" y1="24" x2="8" y2="24" />
      <line x1="40" y1="24" x2="46" y2="24" />
      <line x1="8.5" y1="8.5" x2="12.7" y2="12.7" />
      <line x1="35.3" y1="35.3" x2="39.5" y2="39.5" />
      <line x1="8.5" y1="39.5" x2="12.7" y2="35.3" />
      <line x1="35.3" y1="12.7" x2="39.5" y2="8.5" />
    </g>
  </svg>
);

const CloudIcon = () => (
  <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
    <path d="M12 36a8 8 0 01-.5-15.97A12 12 0 0136 24h1a6 6 0 010 12H12z" fill="#94A3B8" />
  </svg>
);

const RainIcon = () => (
  <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
    <path d="M12 28a8 8 0 01-.5-15.97A12 12 0 0136 16h1a6 6 0 010 12H12z" fill="#94A3B8" />
    <line x1="16" y1="34" x2="14" y2="40" stroke="#60A5FA" strokeWidth="2" strokeLinecap="round" />
    <line x1="24" y1="34" x2="22" y2="42" stroke="#60A5FA" strokeWidth="2" strokeLinecap="round" />
    <line x1="32" y1="34" x2="30" y2="40" stroke="#60A5FA" strokeWidth="2" strokeLinecap="round" />
  </svg>
);

const ShortsIcon = () => (
  <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
    <path d="M14 16h36v8l-6 28h-8L32 32l-4 20h-8L14 24v-8z" fill="#3B82F6" stroke="#1E40AF" strokeWidth="2" />
    <line x1="32" y1="16" x2="32" y2="32" stroke="#1E40AF" strokeWidth="1.5" strokeDasharray="3 2" />
  </svg>
);

const LongsIcon = () => (
  <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
    <path d="M18 8h28v6l-2 42h-8L32 24l-4 32h-8L18 14V8z" fill="#4B5563" stroke="#1F2937" strokeWidth="2" />
    <line x1="32" y1="8" x2="32" y2="24" stroke="#1F2937" strokeWidth="1.5" strokeDasharray="3 2" />
  </svg>
);

const LayersIcon = () => (
  <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
    <rect x="16" y="12" width="32" height="40" rx="4" fill="#6366F1" stroke="#4338CA" strokeWidth="2" />
    <rect x="20" y="8" width="24" height="36" rx="3" fill="#818CF8" stroke="#6366F1" strokeWidth="1.5" />
    <line x1="32" y1="12" x2="32" y2="22" stroke="#4338CA" strokeWidth="2" />
    <line x1="26" y1="12" x2="38" y2="12" stroke="#4338CA" strokeWidth="2" />
  </svg>
);

const SAMPLE_WEATHER = {
  location: "Encinitas, CA",
  current_temp: 71,
  feels_like: 73,
  high: 78,
  low: 62,
  conditions: "Sunny",
  precipitation: 0,
  wind_mph: 8,
  wind_dir: "W",
  humidity: 65,
  uv_index: 7,
  hourly: [
    { hour: "6am", temp: 62, condition: "Clear" },
    { hour: "8am", temp: 65, condition: "Clear" },
    { hour: "10am", temp: 70, condition: "Sunny" },
    { hour: "12pm", temp: 75, condition: "Sunny" },
    { hour: "2pm", temp: 78, condition: "Sunny" },
    { hour: "4pm", temp: 76, condition: "Sunny" },
    { hour: "6pm", temp: 72, condition: "Clear" },
    { hour: "8pm", temp: 67, condition: "Clear" },
    { hour: "10pm", temp: 64, condition: "Clear" },
  ],
};

const USER_PROFILE = {
  name: "Beryl",
  temp_sensitivity: -2,
  location: "Encinitas, CA",
};

function getRecommendation(weather, profile) {
  const feelsLike = weather.feels_like;
  const adjusted = feelsLike - profile.temp_sensitivity;

  let verdict, confidence, color, bgColor, Icon;

  if (weather.precipitation > 30) {
    if (adjusted >= 75) {
      verdict = "SHORTS";
      confidence = "medium";
      color = "#2563EB";
      bgColor = "#DBEAFE";
      Icon = ShortsIcon;
    } else if (adjusted < 70) {
      verdict = "LONGS";
      confidence = "high";
      color = "#4B5563";
      bgColor = "#F3F4F6";
      Icon = LongsIcon;
    } else {
      verdict = "LAYERS";
      confidence = "medium";
      color = "#6366F1";
      bgColor = "#EEF2FF";
      Icon = LayersIcon;
    }
  } else {
    if (adjusted >= 72) {
      verdict = "SHORTS";
      confidence = adjusted >= 77 ? "high" : "medium";
      color = "#2563EB";
      bgColor = "#DBEAFE";
      Icon = ShortsIcon;
    } else if (adjusted < 65) {
      verdict = "LONGS";
      confidence = adjusted < 60 ? "high" : "medium";
      color = "#4B5563";
      bgColor = "#F3F4F6";
      Icon = LongsIcon;
    } else {
      verdict = "LAYERS";
      confidence = "medium";
      color = "#6366F1";
      bgColor = "#EEF2FF";
      Icon = LayersIcon;
    }
  }

  const tips = [];
  if (weather.uv_index >= 6) tips.push("Sunscreen - UV is high today");
  if (weather.precipitation > 30) tips.push("Grab an umbrella or rain jacket");
  if (weather.wind_mph > 15) tips.push("Windy - consider a windbreaker");
  if (weather.humidity > 80) tips.push("Humid - go lightweight and breathable");
  if (weather.high - weather.low > 15) tips.push("Big temp swing - bring a layer for evening");
  if (weather.low < 60 && verdict === "SHORTS") tips.push("Morning will be cool, hoodie until it warms up");

  return { verdict, confidence, color, bgColor, Icon, tips, adjustedTemp: adjusted };
}

function WeatherIcon({ conditions }) {
  if (conditions.toLowerCase().includes("rain") || conditions.toLowerCase().includes("drizzle")) return <RainIcon />;
  if (conditions.toLowerCase().includes("cloud") || conditions.toLowerCase().includes("overcast")) return <CloudIcon />;
  return <SunIcon />;
}

function ConfidenceBadge({ level }) {
  const colors = {
    high: { bg: "#DCFCE7", text: "#166534", label: "High Confidence" },
    medium: { bg: "#FEF9C3", text: "#854D0E", label: "Medium Confidence" },
    low: { bg: "#FEE2E2", text: "#991B1B", label: "Low Confidence" },
  };
  const c = colors[level];
  return (
    <span style={{ background: c.bg, color: c.text, padding: "4px 12px", borderRadius: "12px", fontSize: "13px", fontWeight: 600 }}>
      {c.label}
    </span>
  );
}

export default function WeathermanDashboard() {
  const [weather] = useState(SAMPLE_WEATHER);
  const [profile] = useState(USER_PROFILE);
  const [showDetails, setShowDetails] = useState(false);
  const rec = getRecommendation(weather, profile);
  const now = new Date();
  const dateStr = now.toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric", year: "numeric" });

  return (
    <div style={{ minHeight: "100vh", background: "linear-gradient(135deg, #F8FAFC 0%, #E2E8F0 100%)", fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif", padding: "24px" }}>
      <div style={{ maxWidth: "520px", margin: "0 auto" }}>
        {/* Header */}
        <div style={{ textAlign: "center", marginBottom: "24px" }}>
          <h1 style={{ fontSize: "14px", fontWeight: 700, letterSpacing: "3px", color: "#94A3B8", margin: 0, textTransform: "uppercase" }}>Weatherman</h1>
          <p style={{ fontSize: "13px", color: "#94A3B8", margin: "4px 0 0" }}>{dateStr}</p>
        </div>

        {/* Main Verdict Card */}
        <div style={{ background: "white", borderRadius: "20px", padding: "32px", marginBottom: "16px", boxShadow: "0 4px 24px rgba(0,0,0,0.06)", textAlign: "center" }}>
          <div style={{ marginBottom: "16px" }}>
            <rec.Icon />
          </div>
          <h2 style={{ fontSize: "36px", fontWeight: 800, color: rec.color, margin: "0 0 8px", letterSpacing: "-1px" }}>
            {rec.verdict} DAY
          </h2>
          <ConfidenceBadge level={rec.confidence} />
          <p style={{ fontSize: "15px", color: "#64748B", margin: "16px 0 0", lineHeight: 1.5 }}>
            {weather.feels_like}F and {weather.conditions.toLowerCase()} in {weather.location}.
            {rec.verdict === "SHORTS" && " Perfect shorts weather."}
            {rec.verdict === "LONGS" && " Keep it covered today."}
            {rec.verdict === "LAYERS" && " Borderline - start with layers, adjust as needed."}
          </p>
        </div>

        {/* Weather Stats */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "12px", marginBottom: "16px" }}>
          {[
            { label: "High / Low", value: `${weather.high}F / ${weather.low}F` },
            { label: "Wind", value: `${weather.wind_mph}mph ${weather.wind_dir}` },
            { label: "UV Index", value: weather.uv_index >= 6 ? `${weather.uv_index} (High)` : `${weather.uv_index}` },
          ].map((stat, i) => (
            <div key={i} style={{ background: "white", borderRadius: "14px", padding: "16px", textAlign: "center", boxShadow: "0 2px 12px rgba(0,0,0,0.04)" }}>
              <div style={{ fontSize: "11px", color: "#94A3B8", fontWeight: 600, textTransform: "uppercase", letterSpacing: "1px", marginBottom: "4px" }}>{stat.label}</div>
              <div style={{ fontSize: "16px", fontWeight: 700, color: "#1E293B" }}>{stat.value}</div>
            </div>
          ))}
        </div>

        {/* Tips */}
        {rec.tips.length > 0 && (
          <div style={{ background: "white", borderRadius: "16px", padding: "20px", marginBottom: "16px", boxShadow: "0 2px 12px rgba(0,0,0,0.04)" }}>
            <h3 style={{ fontSize: "12px", fontWeight: 700, color: "#94A3B8", textTransform: "uppercase", letterSpacing: "1.5px", margin: "0 0 12px" }}>Tips</h3>
            {rec.tips.map((tip, i) => (
              <div key={i} style={{ display: "flex", alignItems: "flex-start", gap: "8px", marginBottom: i < rec.tips.length - 1 ? "8px" : 0 }}>
                <span style={{ color: rec.color, fontWeight: 700, fontSize: "14px", lineHeight: "20px" }}>-</span>
                <span style={{ fontSize: "14px", color: "#475569", lineHeight: "20px" }}>{tip}</span>
              </div>
            ))}
          </div>
        )}

        {/* Hourly Toggle */}
        <button
          onClick={() => setShowDetails(!showDetails)}
          style={{ width: "100%", background: "white", border: "none", borderRadius: "14px", padding: "14px", cursor: "pointer", boxShadow: "0 2px 12px rgba(0,0,0,0.04)", fontSize: "13px", fontWeight: 600, color: "#64748B", display: "flex", alignItems: "center", justifyContent: "center", gap: "6px" }}
        >
          {showDetails ? "Hide" : "Show"} Hourly Breakdown
          <span style={{ transform: showDetails ? "rotate(180deg)" : "rotate(0)", transition: "transform 0.2s", display: "inline-block" }}>v</span>
        </button>

        {showDetails && (
          <div style={{ background: "white", borderRadius: "16px", padding: "20px", marginTop: "12px", boxShadow: "0 2px 12px rgba(0,0,0,0.04)" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", height: "120px", marginBottom: "8px" }}>
              {weather.hourly.map((h, i) => {
                const minT = Math.min(...weather.hourly.map(x => x.temp));
                const maxT = Math.max(...weather.hourly.map(x => x.temp));
                const range = maxT - minT || 1;
                const height = ((h.temp - minT) / range) * 80 + 20;
                const isShorts = h.temp - profile.temp_sensitivity >= 72;
                return (
                  <div key={i} style={{ display: "flex", flexDirection: "column", alignItems: "center", flex: 1 }}>
                    <span style={{ fontSize: "11px", fontWeight: 700, color: "#1E293B", marginBottom: "4px" }}>{h.temp}F</span>
                    <div style={{
                      width: "24px",
                      height: `${height}px`,
                      borderRadius: "6px",
                      background: isShorts
                        ? "linear-gradient(180deg, #3B82F6 0%, #93C5FD 100%)"
                        : "linear-gradient(180deg, #94A3B8 0%, #CBD5E1 100%)",
                    }} />
                  </div>
                );
              })}
            </div>
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              {weather.hourly.map((h, i) => (
                <span key={i} style={{ fontSize: "10px", color: "#94A3B8", flex: 1, textAlign: "center" }}>{h.hour}</span>
              ))}
            </div>
            <div style={{ display: "flex", gap: "16px", marginTop: "12px", justifyContent: "center" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                <div style={{ width: "12px", height: "12px", borderRadius: "3px", background: "#3B82F6" }} />
                <span style={{ fontSize: "11px", color: "#64748B" }}>Shorts zone</span>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                <div style={{ width: "12px", height: "12px", borderRadius: "3px", background: "#94A3B8" }} />
                <span style={{ fontSize: "11px", color: "#64748B" }}>Longs zone</span>
              </div>
            </div>
          </div>
        )}

        {/* Profile Note */}
        <div style={{ textAlign: "center", marginTop: "20px", fontSize: "12px", color: "#94A3B8" }}>
          {profile.name}'s profile - temp sensitivity: {profile.temp_sensitivity > 0 ? "+" : ""}{profile.temp_sensitivity} (adjusted threshold: {72 + profile.temp_sensitivity}F)
        </div>
      </div>
    </div>
  );
}
