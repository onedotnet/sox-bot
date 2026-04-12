const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8090";

export async function fetchLeads(params?: { status?: string; priority?: string }) {
  const url = new URL(`${API_BASE}/api/leads`);
  if (params?.status) url.searchParams.set("status", params.status);
  if (params?.priority) url.searchParams.set("priority", params.priority);
  const res = await fetch(url.toString());
  return res.json();
}

export async function updateLead(id: number, data: { status?: string; edited_reply?: string }) {
  const res = await fetch(`${API_BASE}/api/leads/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return res.json();
}

export async function publishLead(id: number) {
  const res = await fetch(`${API_BASE}/api/leads/${id}/publish`, { method: "POST" });
  return res.json();
}

export async function fetchDashboardStats() {
  const res = await fetch(`${API_BASE}/api/dashboard/stats`);
  return res.json();
}

export async function fetchKeywords() {
  const res = await fetch(`${API_BASE}/api/keywords`);
  return res.json();
}

export async function createKeyword(data: { term: string; language: string }) {
  const res = await fetch(`${API_BASE}/api/keywords`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return res.json();
}

export async function deleteKeyword(id: number) {
  await fetch(`${API_BASE}/api/keywords/${id}`, { method: "DELETE" });
}
