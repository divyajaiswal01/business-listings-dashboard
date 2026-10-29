// Thin API client. Every call goes through request() so error handling lives in one place.
const BASE = import.meta.env.VITE_API_URL ?? "";

async function request(path, params = {}) {
  // Drop empty filters so they are not sent as "?city=".
  const clean = Object.fromEntries(Object.entries(params).filter(([, v]) => v !== "" && v != null));
  const qs = new URLSearchParams(clean).toString();
  const res = await fetch(`${BASE}${path}${qs ? `?${qs}` : ""}`);
  if (!res.ok) throw new Error(`API ${res.status}: ${res.statusText}`);
  return res.json();
}

export const api = {
  summary: (f) => request("/api/dashboard/summary", f),
  cities: (f) => request("/api/dashboard/cities", { ...f, limit: 10 }),
  categories: (f) => request("/api/dashboard/categories", { ...f, limit: 10 }),
  sources: (f) => request("/api/dashboard/sources", f),
  insights: (f) => request("/api/dashboard/insights", f),
  listings: (f, page, q, pageSize = 10) =>
    request("/api/listings", { ...f, q, page, page_size: pageSize }),
};
