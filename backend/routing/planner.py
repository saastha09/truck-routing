from datetime import datetime, timedelta, timezone

from . import geo, services
from .risk import HIGH, LEVELS, NO_TRAVEL, SEVERE, classify

HEAT_HOURS = 48


def _hour_index(times, when):
    first = datetime.fromisoformat(times[0]).replace(tzinfo=timezone.utc)
    idx = round((when - first).total_seconds() / 3600)
    return max(0, min(idx, len(times) - 1))


def _summary(checkpoints):
    miles = {i: 0.0 for i in range(5)}
    for c in checkpoints:
        miles[c["risk"]] += c["segment_miles"]
    total = sum(miles.values()) or 1
    return {
        "miles_by_level": {LEVELS[i]: round(m, 1) for i, m in miles.items()},
        "no_travel_miles": miles[NO_TRAVEL],
        "severe_miles": miles[SEVERE],
        "high_miles": miles[HIGH],
        "avg_risk": round(sum(i * m for i, m in miles.items()) / total, 3),
    }


def rank_key(route):
    return (
        route["no_travel_miles"],
        route["severe_miles"],
        route["high_miles"],
        route["avg_risk"],
        route["hours"],
    )


def plan(origin, dest, depart, load_lb, interval):
    raw = services.routes(origin, dest)
    if not raw:
        raise services.UpstreamError("No route found")

    sampled = []
    for rt in raw:
        pts, total = geo.sample(rt["coords"], interval)
        sampled.append((rt, pts, total))

    keys = {}
    for _, pts, _ in sampled:
        for p in pts:
            keys.setdefault((round(p["lat"], 3), round(p["lng"], 3)), None)
    key_list = list(keys)
    for k, wx in zip(key_list, services.weather(key_list)):
        keys[k] = wx
    times = keys[key_list[0]]["times"]

    routes_out = []
    heat = {}
    for n, (rt, pts, total) in enumerate(sampled):
        checkpoints = []
        for i, p in enumerate(pts):
            nxt = pts[i + 1]["mile"] if i + 1 < len(pts) else total
            frac = p["mile"] / total if total else 0
            eta = depart + timedelta(seconds=rt["seconds"] * frac)
            k = (round(p["lat"], 3), round(p["lng"], 3))
            wx = keys[k]
            idx = _hour_index(times, eta)
            level = classify(wx["wind"][idx], wx["rain"][idx], wx["snow"][idx], load_lb)
            checkpoints.append({
                **p,
                "mile": round(p["mile"], 1),
                "segment_miles": nxt - p["mile"],
                "eta": eta.isoformat(),
                "wind_mph": wx["wind"][idx],
                "rain_in_hr": wx["rain"][idx],
                "snow_in_hr": wx["snow"][idx],
                "risk": level,
                "risk_label": LEVELS[level],
            })
            heat.setdefault(k, p)
        routes_out.append({
            "id": n,
            "coords": rt["coords"],
            "miles": round(total, 1),
            "hours": round(rt["seconds"] / 3600, 2),
            "arrival": checkpoints[-1]["eta"],
            "checkpoints": checkpoints,
            **_summary(checkpoints),
        })

    best = min(routes_out, key=rank_key)

    start = _hour_index(times, depart)
    heat_out = []
    for k, p in heat.items():
        wx = keys[k]
        series = []
        for h in range(HEAT_HOURS):
            i = min(start + h, len(times) - 1)
            series.append(classify(wx["wind"][i], wx["rain"][i], wx["snow"][i], load_lb))
        heat_out.append({"lat": p["lat"], "lng": p["lng"], "risk": series})

    return {
        "recommended": best["id"],
        "routes": routes_out,
        "heatmap": {"start": times[start], "points": heat_out},
    }
