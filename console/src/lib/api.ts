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

export interface ContentItem {
  id: number;
  title: string;
  body: string;
  summary: string | null;
  content_type: string;
  language: string;
  status: string;
  seo_keyword: string | null;
  target_platform: string;
  published_url: string | null;
  scheduled_at: string | null;
  quality_passed: boolean;
  quality_notes: string | null;
  pair_id: string | null;
  generation_cost_cents: number;
  created_at: string;
}

export async function fetchContent(params?: { status?: string; content_type?: string }): Promise<ContentItem[]> {
  const url = new URL(`${API_BASE}/api/content`);
  if (params?.status) url.searchParams.set("status", params.status);
  if (params?.content_type) url.searchParams.set("content_type", params.content_type);
  const res = await fetch(url.toString());
  return res.json();
}

export async function updateContent(id: number, data: { title?: string; body?: string; status?: string }) {
  const res = await fetch(`${API_BASE}/api/content/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return res.json();
}

export async function generateContent(data: { seo_keyword: string; content_type?: string; language?: string }) {
  const res = await fetch(`${API_BASE}/api/content/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return res.json();
}

export async function publishContent(id: number) {
  const res = await fetch(`${API_BASE}/api/content/${id}/publish`, { method: "POST" });
  return res.json();
}

export async function fetchCalendar(weekStart?: string): Promise<ContentItem[]> {
  const url = new URL(`${API_BASE}/api/calendar`);
  if (weekStart) url.searchParams.set("week_start", weekStart);
  const res = await fetch(url.toString());
  return res.json();
}

export interface CommunityMessage {
  id: number;
  platform: string;
  author_name: string;
  message_text: string;
  intent: string;
  response_text: string | null;
  escalated: boolean;
  is_lead: boolean;
  created_at: string;
}

export interface CommunityStats {
  total_messages: number;
  auto_resolved: number;
  escalated: number;
  leads_detected: number;
  resolution_rate: number;
}

export async function fetchCommunityMessages(params?: { escalated?: boolean; is_lead?: boolean }): Promise<CommunityMessage[]> {
  const url = new URL(`${API_BASE}/api/community/messages`);
  if (params?.escalated !== undefined) url.searchParams.set("escalated", String(params.escalated));
  if (params?.is_lead !== undefined) url.searchParams.set("is_lead", String(params.is_lead));
  const res = await fetch(url.toString());
  return res.json();
}

export async function fetchCommunityStats(): Promise<CommunityStats> {
  const res = await fetch(`${API_BASE}/api/community/stats`);
  return res.json();
}

export async function triggerReindex() {
  const res = await fetch(`${API_BASE}/api/community/knowledge/reindex`, { method: "POST" });
  return res.json();
}

export interface WeeklyReport {
  id: number;
  week_start: string;
  week_end: string;
  leads_discovered: number;
  leads_published: number;
  enterprise_leads: number;
  content_generated: number;
  content_published: number;
  content_cost_cents: number;
  messages_received: number;
  messages_auto_resolved: number;
  messages_escalated: number;
  community_leads: number;
  resolution_rate: number;
  summary: string;
  action_items: string; // JSON array
  created_at: string;
}

export interface AnalyticsOverview {
  scout_pending: number;
  scout_published_this_week: number;
  content_drafts: number;
  content_scheduled: number;
  community_messages_today: number;
  community_resolution_rate: number;
  leads_trend: number;
  content_trend: number;
  messages_trend: number;
}

export async function fetchAnalyticsOverview(): Promise<AnalyticsOverview> {
  const res = await fetch(`${API_BASE}/api/analytics/overview`);
  return res.json();
}

export async function fetchWeeklyReports(limit = 10): Promise<WeeklyReport[]> {
  const res = await fetch(`${API_BASE}/api/analytics/reports?limit=${limit}`);
  return res.json();
}

export async function triggerReport() {
  const res = await fetch(`${API_BASE}/api/analytics/reports/generate`, { method: "POST" });
  return res.json();
}
