const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

export async function fetchPlan(params) {
  const res = await fetch(`${API}/api/plan?${new URLSearchParams(params)}`);
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(body.error || "Request failed");
  return body;
}
