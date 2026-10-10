import { useEffect, useMemo, useState } from "react";
import { MapContainer, TileLayer, GeoJSON } from "react-leaflet";

const API = import.meta.env.VITE_API_URL || "";
const COLORS = { Low: "#3a9b6a", Moderate: "#e2b33a", High: "#e27a2c", Extreme: "#b8232f" };
const HEAT_LABELS = { heat_index: "Feels-like temperature", surface_temp: "Hot surfaces (land temp)",
  low_green: "Lack of green cover", population: "Crowding", vulnerable: "Vulnerable residents" };
const WATER_LABELS = { distance: "Distance to water", scarcity: "Few water points per person" };
const DAY_NAMES = ["Today", "Tomorrow", "Day 3"];

function Parts({ parts, labels, max, color }) {
  return Object.entries(parts).map(([k, v]) => (
    <div className="part" key={k}>
      <div className="part-row"><span>{labels[k]}</span><b>{v.toFixed(1)}</b></div>
      <div className="bar"><i style={{ width: `${Math.min(100, (v / max[k]) * 100)}%`, background: color }} /></div>
    </div>
  ));
}
const HEAT_MAX = { heat_index: 35, surface_temp: 25, low_green: 15, population: 15, vulnerable: 10 };
const WATER_MAX = { distance: 60, scarcity: 40 };

export default function App() {
  const [day, setDay] = useState(0);
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    setError("");
    fetch(`${API}/api/wards?day=${day}`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(r.status))))
      .then(setData)
      .catch(() => setError("Can't reach the HeatWatch API. Start the backend on port 8000 and reload."));
  }, [day]);

  const wards = useMemo(() => (data ? data.features.map((f) => f.properties) : []), [data]);
  const top = useMemo(() => [...wards].sort((a, b) => b.priority - a.priority).slice(0, 5), [wards]);
  const current = wards.find((w) => w.id === selected) || null;

  const [lang, setLang] = useState("en");
  const [detail, setDetail] = useState(null);
  const [advisory, setAdvisory] = useState(null);
  const [alertMsg, setAlertMsg] = useState("");

  useEffect(() => {
    setDetail(null);
    setAlertMsg("");
    if (!selected) return;
    fetch(`${API}/api/wards/${selected}?day=${day}`).then((r) => r.json()).then(setDetail).catch(() => {});
  }, [selected, day]);

  useEffect(() => {
    setAdvisory(null);
    if (!selected) return;
    fetch(`${API}/api/wards/${selected}/advisory?day=${day}&lang=${lang}`)
      .then((r) => r.json()).then(setAdvisory).catch(() => {});
  }, [selected, day, lang]);

  const sendAlert = () =>
    fetch(`${API}/api/alerts/send/${selected}?day=${day}`, { method: "POST" })
      .then((r) => r.json())
      .then((r) => setAlertMsg(r.status === "sent" ? "Alert sent to subscribers by SMS/email." : "Alert recorded. SNS isn't connected, so nothing was sent."))
      .catch(() => setAlertMsg("Couldn't send the alert. Check that the API is running."));

  const style = (f) => ({ color: f.properties.id === selected ? "#14262b" : "#fff",
    weight: f.properties.id === selected ? 3 : 1.5, fillColor: COLORS[f.properties.band], fillOpacity: 0.72 });
  const onEach = (f, layer) => {
    layer.on("click", () => setSelected(f.properties.id));
    layer.bindTooltip(`${f.properties.name}: ${f.properties.band}`, { sticky: true });
  };

  return (
    <div className="app">
      <header>
        <div>
          <h1>HeatWatch</h1>
          <p>Which Jaipur neighbourhoods need help first when it's hot and water is short.</p>
        </div>
        <div className="controls">
          <div className="days" role="tablist" aria-label="Forecast day">
            {DAY_NAMES.map((n, i) => (
              <button key={n} role="tab" aria-selected={day === i} className={day === i ? "on" : ""} onClick={() => setDay(i)}>{n}</button>
            ))}
          </div>
          {data && (
            <span className={`src ${data.meta.source}`}>
              {data.meta.source === "live" ? "Live forecast" : "Sample forecast (offline)"}
            </span>
          )}
        </div>
      </header>

      <main>
        <section className="map-wrap">
          {error && <div className="error">{error}</div>}
          <MapContainer center={[26.9, 75.79]} zoom={12} scrollWheelZoom>
            <TileLayer attribution="&copy; OpenStreetMap contributors" url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
            {data && <GeoJSON key={`${day}-${selected}-${data.meta.source}`} data={data} style={style} onEachFeature={onEach} />}
          </MapContainer>
          <div className="legend">
            {Object.entries(COLORS).map(([k, c]) => (<span key={k}><i style={{ background: c }} />{k}</span>))}
          </div>
        </section>

        <aside>
          {current ? (
            <div className="detail">
              <button className="back" onClick={() => setSelected(null)}>Back to top 5</button>
              <h2>{current.name}</h2>
              <div className="badge" style={{ background: COLORS[current.band] }}>{current.band} priority · {current.priority.toFixed(0)}/100</div>
              <p className="wx">{current.temp_c}°C air, {current.humidity_pct}% humidity, feels like {current.feels_like_c}°C</p>
              <h3>Heat risk <span>{current.heat.toFixed(0)}/100</span></h3>
              <Parts parts={current.heat_parts} labels={HEAT_LABELS} max={HEAT_MAX} color="#e27a2c" />
              <h3>Water stress <span>{current.water.toFixed(0)}/100</span></h3>
              <Parts parts={current.water_parts} labels={WATER_LABELS} max={WATER_MAX} color="#2b7fb8" />
              <h3>3-day outlook</h3>
              <div className="trend">
                {(detail?.trend || []).map((t, i) => (
                  <div key={i}><i style={{ height: `${t.priority}%`, background: COLORS[t.band] }} /><span>{DAY_NAMES[i]}<br />{t.priority.toFixed(0)}</span></div>
                ))}
              </div>
              <h3>What to do</h3>
              <ul className="actions">
                {(detail?.actions || []).map((a, i) => (<li key={i} className={a.level}><b>{a.level}</b>{a.text}</li>))}
              </ul>
              <h3>Resident advisory
                <span className="lang">
                  <button className={lang === "en" ? "on" : ""} onClick={() => setLang("en")}>English</button>
                  <button className={lang === "hi" ? "on" : ""} onClick={() => setLang("hi")}>हिन्दी</button>
                </span>
              </h3>
              <p className="advisory" lang={lang}>{advisory ? advisory.text : "Writing advisory..."}</p>
              {advisory && <p className="note">{advisory.source === "bedrock" ? "Written by Amazon Bedrock." : "Template advisory. Amazon Bedrock isn't enabled."}</p>}
              <button className="alert" onClick={sendAlert}>Send alert to subscribers</button>
              {alertMsg && <p className="note">{alertMsg}</p>}
              <p className="note">Priority = 65% heat risk + 35% water stress. Ward values are sample data for the prototype.</p>
            </div>
          ) : (
            <div>
              <h2>Top 5 to act on · {DAY_NAMES[day].toLowerCase()}</h2>
              <ol className="top">
                {top.map((w) => (
                  <li key={w.id}>
                    <button onClick={() => setSelected(w.id)}>
                      <i style={{ background: COLORS[w.band] }} />
                      <span>{w.name}<small>{w.band} · heat {w.heat.toFixed(0)} · water {w.water.toFixed(0)}</small></span>
                      <b>{w.priority.toFixed(0)}</b>
                    </button>
                  </li>
                ))}
              </ol>
              <p className="note">Select a ward on the map or in this list to see why it scores the way it does.</p>
            </div>
          )}
        </aside>
      </main>
    </div>
  );
}
