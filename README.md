# Weather-Aware Truck Routing

Coding assessment for Spotter. A truck driver types origin, destination, departure time, and load weight. The app pulls a few driving routes, checks weather along each one, scores risk, and recommends the safest option that isn’t ridiculously slow.

- **Frontend:** React + Vite + Leaflet — [`frontend/`](frontend/)
- **Backend:** Django — [`backend/`](backend/)
- **APIs:** Nominatim (geocoding), OSRM (routes), Open-Meteo (hourly wind / rain / snow). No API keys.

## Links

- GitHub: https://github.com/saastha09/truck-routing
- Live app (frontend): _add after you deploy_
- API (backend): _add after you deploy_
- Loom: https://www.loom.com/share/1a4047b2e9884386be8c4889f19b2470

The form wants the GitHub repo for “code”, and the **frontend** URL for “hosted version”.

## Run locally

Two terminals.

```bash
# API on :8000
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python manage.py test
DEBUG=1 .venv/bin/python manage.py runserver
```

```bash
# UI on :5173
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. Try Chicago, IL → Denver, CO.

## How it works

`GET /api/plan?origin&destination&depart&load_lb&interval` does the whole trip in one call.

1. Geocode the two cities.
2. Ask OSRM for up to 3 driving routes (sometimes you only get 1–2).
3. Drop checkpoints every 10 / 25 / 50 miles.
4. ETA at a checkpoint = departure + (distance / total) × OSRM duration. Grab the forecast hour closest to that ETA.
5. Risk = worst of wind / rain / snow, then the load rules. Wind 55 mph is already No Travel. Rain 1.00 in/hr and snow 3.0 in/hr still count as Severe.
6. Pick a route: fewest No Travel miles, then Severe, then High, then lowest average risk, then shortest time. Average risk is mile-weighted (Low = 0 … No Travel = 4).
7. The 48-hour heatmap rides along in the same JSON, so the slider doesn’t hit the network.

## Deploy (when you have URLs)

Frontend build needs `VITE_API_URL` pointed at the live Django URL.

Backend (gunicorn) needs:

- `DEBUG=0`
- `SECRET_KEY`
- `ALLOWED_HOSTS` = your API hostname
- `CORS_ORIGINS` = your frontend origin (https://…)
