import { useCallback, useState } from "react";
import Map from "./Map.jsx";
import { fetchPlan } from "./api.js";
import { COLORS, LEVELS } from "./risk.js";

const fmt = (iso) => new Date(iso).toLocaleString([], { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" });

function defaultDeparture() {
  const d = new Date(Date.now() + 3600e3);
  d.setMinutes(0, 0, 0);
  return new Date(d - d.getTimezoneOffset() * 60e3).toISOString().slice(0, 16);
}

export default function App() {
  const [form, setForm] = useState({
    origin: "Chicago, IL", destination: "Denver, CO",
    depart: defaultDeparture(), load_lb: 35000, interval: 25,
  });
  const [plan, setPlan] = useState(null);
  const [selected, setSelected] = useState(0);
  const [hour, setHour] = useState(0);
  const [showHeat, setShowHeat] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });
  const select = useCallback((i) => setSelected(i), []);

  async function submit(e) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const data = await fetchPlan({ ...form, depart: new Date(form.depart).toISOString() });
      setPlan(data);
      setSelected(data.recommended);
      setHour(0);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app">
      <aside>
        <h1>Weather-Aware Truck Routing</h1>
        <form onSubmit={submit}>
          <label>Origin<input value={form.origin} onChange={set("origin")} required /></label>
          <label>Destination<input value={form.destination} onChange={set("destination")} required /></label>
          <label>Departure<input type="datetime-local" value={form.depart} onChange={set("depart")} required /></label>
          <div className="row">
            <label>Load (lb)<input type="number" min="0" value={form.load_lb} onChange={set("load_lb")} required /></label>
            <label>Checkpoint every
              <select value={form.interval} onChange={set("interval")}>
                <option value="10">10 mi</option><option value="25">25 mi</option><option value="50">50 mi</option>
              </select>
            </label>
          </div>
          <button disabled={loading}>{loading ? "Planning…" : "Find routes"}</button>
        </form>
        {error && <p className="error">{error}</p>}

        {plan && (
          <>
            <div className="heat">
              <label>
                <input type="checkbox" checked={showHeat} onChange={(e) => setShowHeat(e.target.checked)} /> Weather heatmap
              </label>
              <input type="range" min="0" max="47" value={hour} onChange={(e) => setHour(+e.target.value)} disabled={!showHeat} />
              <small>+{hour} h after departure · {fmt(new Date(new Date(plan.heatmap.start + "Z").getTime() + hour * 3600e3))}</small>
            </div>

            {plan.routes.map((r, i) => (
              <div key={r.id} className={`card ${i === selected ? "on" : ""}`} onClick={() => setSelected(i)}>
                <h3>
                  Route {i + 1} {i === plan.recommended && <span className="badge">Recommended</span>}
                </h3>
                <p>{r.miles} mi · {r.hours} h · arrive {fmt(r.arrival)}</p>
                <p className="small">
                  Avg risk {r.avg_risk.toFixed(2)} / 4 · Severe {r.severe_miles.toFixed(0)} mi · High {r.high_miles.toFixed(0)} mi
                  {r.no_travel_miles > 0 && <b> · No Travel {r.no_travel_miles.toFixed(0)} mi</b>}
                </p>
                <div className="bar">
                  {LEVELS.map((l, k) => (
                    <span key={l} title={`${l}: ${r.miles_by_level[l]} mi`}
                      style={{ flex: r.miles_by_level[l], background: COLORS[k] }} />
                  ))}
                </div>
              </div>
            ))}
            <p className="legend">
              {LEVELS.map((l, k) => <span key={l}><i style={{ background: COLORS[k] }} />{l}</span>)}
            </p>
          </>
        )}
      </aside>
      <Map plan={plan} selected={selected} hour={hour} showHeat={showHeat} onSelect={select} />
    </div>
  );
}
