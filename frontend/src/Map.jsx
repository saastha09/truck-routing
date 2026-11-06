import { useEffect, useRef } from "react";
import L from "leaflet";
import "leaflet.heat";
import { COLORS } from "./risk.js";

const ROUTE_COLORS = ["#1d4ed8", "#0f766e", "#7c3aed"];
const fmt = (iso) => new Date(iso).toLocaleString([], { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" });

export default function Map({ plan, selected, hour, showHeat, onSelect }) {
  const el = useRef(null);
  const map = useRef(null);
  const routeLayer = useRef(L.layerGroup());
  const heatLayer = useRef(null);

  useEffect(() => {
    map.current = L.map(el.current).setView([39, -98], 4);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "© OpenStreetMap",
    }).addTo(map.current);
    routeLayer.current.addTo(map.current);
    return () => map.current.remove();
  }, []);

  useEffect(() => {
    const group = routeLayer.current;
    group.clearLayers();
    if (!plan) return;
    const order = plan.routes.map((_, i) => i).filter((i) => i !== selected);
    order.push(selected);
    for (const i of order) {
      const r = plan.routes[i];
      const active = i === selected;
      const line = L.polyline(r.coords, {
        color: ROUTE_COLORS[i % 3],
        weight: active ? 6 : 3,
        opacity: active ? 0.9 : 0.5,
        dashArray: active ? null : "6 6",
      }).on("click", () => onSelect(i));
      line.bindTooltip(`Route ${i + 1}: ${r.miles} mi, ${r.hours} h`, { sticky: true });
      group.addLayer(line);
      if (!active) continue;
      for (const c of r.checkpoints) {
        L.circleMarker([c.lat, c.lng], {
          radius: 6, color: "#fff", weight: 1.5, fillColor: COLORS[c.risk], fillOpacity: 1,
        })
          .bindPopup(
            `<b>Mile ${c.mile}</b> – ${c.risk_label}<br>ETA ${fmt(c.eta)}<br>` +
            `Wind ${c.wind_mph.toFixed(0)} mph · Rain ${c.rain_in_hr.toFixed(2)} in/hr · Snow ${c.snow_in_hr.toFixed(2)} in/hr`
          )
          .addTo(group);
      }
    }
  }, [plan, selected, onSelect]);

  useEffect(() => {
    if (!plan || !map.current) return;
    const all = plan.routes.flatMap((r) => r.coords);
    if (all.length) map.current.fitBounds(L.latLngBounds(all), { padding: [30, 30] });
  }, [plan]);

  useEffect(() => {
    if (!map.current) return;
    if (!plan || !showHeat) {
      if (heatLayer.current) {
        map.current.removeLayer(heatLayer.current);
        heatLayer.current = null;
      }
      return;
    }
    const pts = plan.heatmap.points.map((p) => [p.lat, p.lng, (p.risk[hour] + 1) / 5]);
    if (heatLayer.current) {
      heatLayer.current.setLatLngs(pts);
      return;
    }
    heatLayer.current = L.heatLayer(pts, {
      radius: 28, blur: 22, max: 1,
      gradient: { 0.2: "#2e9e44", 0.4: "#e0b800", 0.6: "#f08a00", 0.8: "#d62828", 1: "#5b1a8f" },
    }).addTo(map.current);
  }, [plan, hour, showHeat]);

  return <div ref={el} className="map" />;
}
