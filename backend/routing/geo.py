import math

R_MILES = 3958.8


def haversine(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (*a, *b))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * R_MILES * math.asin(math.sqrt(h))


def sample(coords, interval):
    """Checkpoints at mile 0, every `interval` miles, and the end."""
    points = [{"lat": coords[0][0], "lng": coords[0][1], "mile": 0.0}]
    travelled, next_mark = 0.0, interval
    for a, b in zip(coords, coords[1:]):
        seg = haversine(a, b)
        while seg and travelled + seg >= next_mark:
            t = (next_mark - travelled) / seg
            points.append({
                "lat": a[0] + (b[0] - a[0]) * t,
                "lng": a[1] + (b[1] - a[1]) * t,
                "mile": next_mark,
            })
            next_mark += interval
        travelled += seg
    if points[-1]["mile"] < travelled:
        points.append({"lat": coords[-1][0], "lng": coords[-1][1], "mile": travelled})
    return points, travelled
