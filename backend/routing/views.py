from datetime import datetime, timezone

import requests
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from . import planner, services

INTERVALS = (10, 25, 50)


@require_GET
def health(_request):
    return JsonResponse({"ok": True})


@require_GET
def plan(request):
    q = request.GET
    try:
        load = float(q["load_lb"])
        interval = int(q.get("interval", 25))
        depart = datetime.fromisoformat(q["depart"].replace("Z", "+00:00"))
        if depart.tzinfo is None:
            depart = depart.replace(tzinfo=timezone.utc)
        origin_q, dest_q = q["origin"].strip(), q["destination"].strip()
    except (KeyError, ValueError):
        return JsonResponse({"error": "origin, destination, depart (ISO), load_lb required"}, status=400)
    if interval not in INTERVALS or load < 0 or not origin_q or not dest_q:
        return JsonResponse({"error": "invalid parameters"}, status=400)

    try:
        o, d = services.geocode(origin_q), services.geocode(dest_q)
        result = planner.plan(o[:2], d[:2], depart, load, interval)
    except services.UpstreamError as e:
        return JsonResponse({"error": str(e)}, status=422)
    except requests.RequestException as e:
        return JsonResponse({"error": f"Upstream service failed: {e}"}, status=502)
    result["origin"], result["destination"] = o[2], d[2]
    return JsonResponse(result)
