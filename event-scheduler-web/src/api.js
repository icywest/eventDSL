const API_BASE = "http://127.0.0.1:8000";

export async function fetchFormConfig(requesterType) {
  const res = await fetch(`${API_BASE}/form-config?requester_type=${encodeURIComponent(requesterType)}`);
  if (!res.ok) {
    const error = await res.json().catch(() => ({}));
    throw new Error(error.detail || "Failed to load form config");
  }
  return res.json();
}

export async function fetchEvents() {
  const res = await fetch(`${API_BASE}/events`);
  if (!res.ok) {
    throw new Error("Failed to load events");
  }
  return res.json();
}

export async function createEvent(data) {
  const res = await fetch(`${API_BASE}/events`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({}));
    throw new Error(error.detail || "Failed to create event");
  }

  return res.json();
}
