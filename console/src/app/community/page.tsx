"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/button";
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


const PLATFORM_STYLES: Record<string, { bg: string; text: string; initial: string }> = {
  discord: { bg: "bg-indigo-500/20", text: "text-indigo-300", initial: "D" },
  wechat: { bg: "bg-emerald-500/20", text: "text-emerald-300", initial: "W" },
  slack: { bg: "bg-amber-500/20", text: "text-amber-300", initial: "S" },
  twitter: { bg: "bg-sky-500/20", text: "text-sky-300", initial: "X" },
};

const INTENT_STYLES: Record<string, { bg: string; text: string }> = {
  enterprise: { bg: "bg-red-500/10 border-red-500/20", text: "text-red-400" },
  technical: { bg: "bg-blue-500/10 border-blue-500/20", text: "text-blue-400" },
  help_seeking: { bg: "bg-amber-500/10 border-amber-500/20", text: "text-amber-400" },
  comparison: { bg: "bg-purple-500/10 border-purple-500/20", text: "text-purple-400" },
  complaint: { bg: "bg-orange-500/10 border-orange-500/20", text: "text-orange-400" },
  general: { bg: "bg-zinc-500/10 border-zinc-500/20", text: "text-zinc-400" },
};

function CommunityIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#10b981" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M23 21v-2a4 4 0 00-3-3.87" />
      <path d="M16 3.13a4 4 0 010 7.75" />
    </svg>
  );
}

function StatPill({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="flex items-center gap-3 px-4 py-3 rounded-xl bg-white/[0.03] border border-white/[0.05]">
      <div>
        <p className="stat-number text-lg font-semibold text-white leading-none">{value}</p>
        <p className="text-[10px] text-zinc-500 mt-0.5 font-medium uppercase tracking-wider">{label}</p>
      </div>
    </div>
  );
}

function MessageCard({ msg, index }: { msg: CommunityMessage; index: number }) {
  const platform = msg.platform.toLowerCase();
  const platformStyle = PLATFORM_STYLES[platform] ?? { bg: "bg-zinc-500/20", text: "text-zinc-300", initial: "?" };
  const intentStyle = INTENT_STYLES[msg.intent?.toLowerCase()] ?? INTENT_STYLES.general;

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.06, duration: 0.35 }}
      exit={{ opacity: 0, x: -20, transition: { duration: 0.2 } }}
      layout
      className="card-hover rounded-xl border border-white/[0.06] bg-[#111113] overflow-hidden"
    >
      {/* Top accent */}
      <div className="h-[2px] bg-emerald-500/60" />

      <div className="px-5 pt-4 pb-4">
        {/* Header row */}
        <div className="flex items-start justify-between gap-3 mb-3">
          <div className="flex items-center gap-3">
            {/* Platform avatar */}
            <div className={`w-9 h-9 rounded-xl ${platformStyle.bg} flex items-center justify-center flex-shrink-0`}>
              <span className={`text-xs font-bold font-mono ${platformStyle.text}`}>
                {platformStyle.initial}
              </span>
            </div>

            {/* Author + badges */}
            <div>
              <div className="flex flex-wrap items-center gap-1.5">
                <span className="font-semibold text-white text-sm">{msg.author_name}</span>
                <span className={`text-[10px] px-2 py-0.5 rounded-full border font-semibold uppercase tracking-wider ${intentStyle.bg} ${intentStyle.text}`}>
                  {msg.intent}
                </span>
                {msg.is_lead && (
                  <span className="text-[10px] px-2 py-0.5 rounded-full border border-amber-500/20 bg-amber-500/10 text-amber-400 font-semibold uppercase tracking-wider">
                    Lead
                  </span>
                )}
                {msg.escalated && (
                  <span className="text-[10px] px-2 py-0.5 rounded-full border border-red-500/20 bg-red-500/10 text-red-400 font-semibold uppercase tracking-wider">
                    Escalated
                  </span>
                )}
              </div>
              <p className="text-[11px] text-zinc-600 mt-0.5">{msg.platform}</p>
            </div>
          </div>

          <span className="text-[11px] text-zinc-600 flex-shrink-0 pt-0.5">
            {new Date(msg.created_at).toLocaleDateString()}
          </span>
        </div>

        {/* Message */}
        <div className="rounded-lg bg-white/[0.02] border border-white/[0.04] p-3.5 mb-3">
          <p className="text-[11px] text-zinc-500 font-medium uppercase tracking-wider mb-1.5">Message</p>
          <p className="text-[13px] text-zinc-300 leading-relaxed">{msg.message_text}</p>
        </div>

        {/* Bot response */}
        {msg.response_text && (
          <div className="rounded-lg bg-emerald-500/[0.03] border-l-2 border-emerald-500/40 border border-emerald-500/[0.08] p-3.5">
            <div className="flex items-center gap-1.5 mb-1.5">
              <div className="w-3.5 h-3.5 rounded-sm bg-emerald-500/20 flex items-center justify-center">
                <svg width="8" height="8" viewBox="0 0 24 24" fill="none" stroke="#10b981" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
              </div>
              <p className="text-[11px] text-emerald-500/70 font-medium uppercase tracking-wider">Bot Response</p>
            </div>
            <p className="text-[13px] text-zinc-400 leading-relaxed">{msg.response_text}</p>
          </div>
        )}
      </div>
    </motion.div>
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
    const params = activeTab === "escalated" ? { escalated: true } : { is_lead: true };
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
    <div className="p-8 max-w-[900px] mx-auto">
      {/* Page header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-6 flex items-center justify-between"
      >
        <div>
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-emerald-500/10 flex items-center justify-center">
              <CommunityIcon />
            </div>
            <h1 className="text-xl font-bold tracking-tight text-white">CommunityBot</h1>
          </div>
          <p className="text-sm text-zinc-500 mt-1 ml-9">Monitor escalations, leads, and bot responses</p>
        </div>
        <Button
          onClick={handleReindex}
          disabled={reindexing}
          className="bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-400 border border-emerald-500/20 text-xs font-semibold px-4 rounded-lg"
        >
          {reindexing ? "Reindexing..." : "Reindex Knowledge Base"}
        </Button>
      </motion.div>

      {/* Stats pills */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1, duration: 0.35 }}
        className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 mb-6"
      >
        <StatPill label="Total Messages" value={stats?.total_messages ?? "—"} />
        <StatPill label="Auto-Resolved" value={stats?.auto_resolved ?? "—"} />
        <StatPill label="Escalated" value={stats?.escalated ?? "—"} />
        <StatPill label="Leads Detected" value={stats?.leads_detected ?? "—"} />
        <StatPill
          label="Resolution Rate"
          value={stats ? `${(stats.resolution_rate * 100).toFixed(1)}%` : "—"}
        />
      </motion.div>

      {/* Tab navigation */}
      <div className="flex gap-1.5 mb-5">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`px-4 py-1.5 rounded-full text-xs font-semibold transition-all ${
              activeTab === tab.key
                ? "bg-emerald-600 text-white shadow-lg shadow-emerald-900/30"
                : "text-zinc-500 hover:text-zinc-300 bg-white/[0.03] border border-white/[0.06] hover:border-white/[0.10]"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Message list */}
      {loading && (
        <div className="text-center py-20">
          <div className="w-6 h-6 border-2 border-emerald-500/30 border-t-emerald-400 rounded-full animate-spin mx-auto" />
          <p className="text-zinc-500 text-xs mt-3">Loading messages...</p>
        </div>
      )}

      {!loading && (
        <div className="space-y-3">
          <AnimatePresence>
            {messages.map((msg, i) => (
              <MessageCard key={msg.id} msg={msg} index={i} />
            ))}
          </AnimatePresence>

          {messages.length === 0 && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.2 }}
              className="text-center py-20"
            >
              <div className="w-16 h-16 rounded-2xl bg-emerald-500/5 border border-emerald-500/10 flex items-center justify-center mx-auto mb-4">
                <CommunityIcon />
              </div>
              <p className="text-zinc-500 text-sm">
                No {activeTab === "escalated" ? "escalated messages" : "enterprise leads"} found.
              </p>
              <p className="text-zinc-600 text-xs mt-1">CommunityBot is monitoring all channels...</p>
            </motion.div>
          )}
        </div>
      )}
    </div>
  );
}
