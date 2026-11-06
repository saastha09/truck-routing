import requests

try:
    # system Python on macOS uses LibreSSL; some APIs fail TLS without this
    import urllib3.contrib.pyopenssl as _pyopenssl
    _pyopenssl.inject_into_urllib3()
except Exception:
    pass

HEADERS = {"User-Agent": "weather-truck-routing/1.0"}
TIMEOUT = 30


class UpstreamError(Exception):
    pass


def geocode(query):
    r = requests.get(
        "https://nominatim.openstreetmap.org/search",
        params={"q": query, "format": "json", "limit": 1},
        headers=HEADERS, timeout=TIMEOUT,
    )
    r.raise_for_status()
    hits = r.json()
    if not hits:
        raise UpstreamError(f"Could not find location: {query}")
    return float(hits[0]["lat"]), float(hits[0]["lon"]), hits[0]["display_name"]


def routes(origin, dest):
    url = "https://router.project-osrm.org/route/v1/driving/{},{};{},{}".format(
        origin[1], origin[0], dest[1], dest[0]
    )
    r = requests.get(
        url, params={"alternatives": 3, "overview": "full", "geometries": "geojson"},
        headers=HEADERS, timeout=TIMEOUT,
    )
    r.raise_for_status()
    data = r.json()
    if data.get("code") != "Ok":
        raise UpstreamError(f"No route found ({data.get('code')})")
    return [
        {
            "coords": [(lat, lng) for lng, lat in rt["geometry"]["coordinates"]],
            "seconds": rt["duration"],
        }
        for rt in data["routes"][:3]
    ]


def weather(points, chunk=50):
    out = []
    for i in range(0, len(points), chunk):
        part = points[i:i + chunk]
        r = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": ",".join(f"{p[0]:.3f}" for p in part),
                "longitude": ",".join(f"{p[1]:.3f}" for p in part),
                "hourly": "wind_speed_10m,rain,snowfall",
                "wind_speed_unit": "mph",
                "precipitation_unit": "inch",
                "timezone": "UTC",
                "forecast_days": 7,
            },
            headers=HEADERS, timeout=TIMEOUT,
        )
        if r.status_code != 200:
            raise UpstreamError(f"Weather API error: {r.text[:200]}")
        body = r.json()
        for loc in body if isinstance(body, list) else [body]:
            h = loc["hourly"]
            out.append({
                "times": h["time"],
                "wind": [v or 0 for v in h["wind_speed_10m"]],
                "rain": [v or 0 for v in h["rain"]],
                "snow": [v or 0 for v in h["snowfall"]],
            })
    return out
