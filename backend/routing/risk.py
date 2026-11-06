LEVELS = ["Low", "Moderate", "High", "Severe", "No Travel"]
LOW, MODERATE, HIGH, SEVERE, NO_TRAVEL = range(5)

# exclusive upper bounds for Low/Mod/High. rain/snow: 1.00 / 3.0 still Severe.
WIND = (25, 35, 45, 55)
RAIN = (0.10, 0.25, 0.50, 1.00)
SNOW = (0.5, 1.0, 2.0, 3.0)


def _band(value, bounds, last_inclusive):
    for level, upper in enumerate(bounds):
        last = level == len(bounds) - 1
        if value < upper or (last and last_inclusive and value <= upper):
            return level
    return NO_TRAVEL


def classify(wind_mph, rain_in_hr, snow_in_hr, load_lb):
    level = max(
        _band(wind_mph, WIND, False),
        _band(rain_in_hr, RAIN, True),
        _band(snow_in_hr, SNOW, True),
    )
    if wind_mph >= 55:
        level = NO_TRAVEL
    elif wind_mph >= 45 and load_lb > 30000:
        level = NO_TRAVEL
    elif wind_mph >= 35 and load_lb > 40000:
        level = max(level, SEVERE)
    return level
