"use client";

import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import {
  CommunityMessage,
  CommunityStats,
  fetchCommunityMessages,
  fetchCommunityStats,
  triggerReindex,
} from "@/lib/api";

const TABS = [
  { label: "Escalated", key: "escalated" },
  { label: "Enterprise Leads", key: "leads" },
] as const;

type TabKey = (typeof TABS)[number]["key"];

const PLATFORM_COLORS: Record<string, string> = {
  discord: "bg-indigo-700 text-indigo-100",
  wechat: "bg-green-700 text-green-100",
  slack: "bg-yellow-700 text-yellow-100",
  twitter: "bg-sky-700 text-sky-100",
};

function platformBadgeClass(platform: string) {
  return PLATFORM_COLORS[platform.toLowerCase()] ?? "bg-zinc-700 text-zinc-200";
}

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <Card className="bg-zinc-900 border-zinc-800">
      <CardContent className="pt-5 pb-4">
        <p className="text-xs text-zinc-400 mb-1">{label}</p>
        <p className="text-2xl font-bold text-zinc-100">{value}</p>
      </CardContent>
    </Card>
  );
}

export default function CommunityPage() {
  const [activeTab, setActiveTab] = useState<TabKey>("escalated");
  const [messages, setMessages] = useState<CommunityMessage[]>([]);
  const [stats, setStats] = useState<CommunityStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [reindexing, setReindexing] = useState(false);

  useEffect(() => {
    fetchCommunityStats().then(setStats).catch(console.error);
  }, []);

  useEffect(() => {
    setLoading(true);
    const params =
      activeTab === "escalated" ? { escalated: true } : { is_lead: true };
    fetchCommunityMessages(params)
      .then(setMessages)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [activeTab]);

  const handleReindex = async () => {
    setReindexing(true);
    try {
      await triggerReindex();
    } catch (err) {
      console.error(err);
    } finally {
      setReindexing(false);
    }
  };

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Community Management</h1>
        <Button
          className="bg-zinc-700 hover:bg-zinc-600"
          onClick={handleReindex}
          disabled={reindexing}
        >
          {reindexing ? "Reindexing..." : "Reindex Knowledge Base"}
        </Button>
      </div>

      {/* Stats cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4 mb-8">
        <StatCard label="Total Messages" value={stats?.total_messages ?? "—"} />
        <StatCard label="Auto-Resolved" value={stats?.auto_resolved ?? "—"} />
        <StatCard label="Escalated" value={stats?.escalated ?? "—"} />
        <StatCard label="Leads Detected" value={stats?.leads_detected ?? "—"} />
        <StatCard
          label="Resolution Rate"
          value={stats ? `${(stats.resolution_rate * 100).toFixed(1)}%` : "—"}
        />
      </div>

      {/* Tab navigation */}
      <div className="flex gap-1 mb-4 border-b border-zinc-800 pb-2">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`px-4 py-1.5 rounded text-sm font-medium transition-colors ${
              activeTab === tab.key
                ? "bg-zinc-700 text-zinc-100"
                : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {loading && <p className="text-zinc-500 text-center py-12">Loading...</p>}

      {!loading && (
        <div className="space-y-4">
          {messages.map((msg) => (
            <Card key={msg.id} className="bg-zinc-900 border-zinc-800">
              <CardHeader className="flex flex-row items-start justify-between pb-2">
                <div className="space-y-1 flex-1 mr-4">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-semibold text-zinc-100">{msg.author_name}</span>
                    <span
                      className={`text-xs px-2 py-0.5 rounded font-medium ${platformBadgeClass(msg.platform)}`}
                    >
                      {msg.platform}
                    </span>
                    <Badge variant="outline" className="text-xs">
                      {msg.intent}
                    </Badge>
                    {msg.is_lead && (
                      <span className="text-xs px-2 py-0.5 rounded bg-amber-700 text-amber-100 font-medium">
                        Lead
                      </span>
                    )}
                    {msg.escalated && (
                      <span className="text-xs px-2 py-0.5 rounded bg-red-800 text-red-100 font-medium">
                        Escalated
                      </span>
                    )}
                  </div>
                </div>
                <div className="text-xs text-zinc-500 whitespace-nowrap">
                  {new Date(msg.created_at).toLocaleDateString()}
                </div>
              </CardHeader>

              <CardContent className="space-y-3">
                <div className="bg-zinc-800 rounded p-3">
                  <p className="text-xs text-zinc-400 mb-1">Message</p>
                  <p className="text-sm text-zinc-200">{msg.message_text}</p>
                </div>
                {msg.response_text && (
                  <div className="bg-zinc-800 rounded p-3 border-l-2 border-green-600">
                    <p className="text-xs text-zinc-400 mb-1">Bot Response</p>
                    <p className="text-sm text-zinc-300">{msg.response_text}</p>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}

          {messages.length === 0 && (
            <p className="text-zinc-500 text-center py-12">
              No{" "}
              {activeTab === "escalated" ? "escalated messages" : "enterprise leads"}{" "}
              found.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
