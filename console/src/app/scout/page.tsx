"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { fetchLeads, updateLead, publishLead } from "@/lib/api";

interface Lead {
  id: number;
  source: string;
  source_url: string;
  author: string;
  original_text: string;
  relevance_score: number;
  intent: string;
  sentiment: string;
  priority: string;
  suggested_reply: string;
  edited_reply: string | null;
  status: string;
  detected_at: string;
}

const INTENT_STYLES: Record<string, { bg: string; text: string }> = {
  enterprise: { bg: "bg-red-500/10 border-red-500/20", text: "text-red-400" },
  technical: { bg: "bg-blue-500/10 border-blue-500/20", text: "text-blue-400" },
  help_seeking: { bg: "bg-amber-500/10 border-amber-500/20", text: "text-amber-400" },
  comparison: { bg: "bg-purple-500/10 border-purple-500/20", text: "text-purple-400" },
  complaint: { bg: "bg-orange-500/10 border-orange-500/20", text: "text-orange-400" },
};

const PRIORITY_STYLES: Record<string, { bg: string; text: string; label: string }> = {
  high: { bg: "bg-red-500/20", text: "text-red-300", label: "HIGH" },
  medium: { bg: "bg-amber-500/15", text: "text-amber-300", label: "MED" },
  low: { bg: "bg-zinc-500/15", text: "text-zinc-400", label: "LOW" },
};

const SOURCE_ICONS: Record<string, string> = {
  hackernews: "HN",
  reddit: "R",
  twitter: "X",
  zhihu: "Z",
  v2ex: "V",
};

function ScoreRing({ score }: { score: number }) {
  const radius = 16;
  const circ = 2 * Math.PI * radius;
  const offset = circ - (score / 100) * circ;
  const color = score >= 80 ? "#ef4444" : score >= 60 ? "#f59e0b" : "#71717a";

  return (
    <div className="relative w-10 h-10 flex-shrink-0">
      <svg width="40" height="40" className="-rotate-90">
        <circle cx="20" cy="20" r={radius} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="3" />
        <circle
          cx="20" cy="20" r={radius} fill="none"
          stroke={color} strokeWidth="3"
          strokeDasharray={circ} strokeDashoffset={offset}
          strokeLinecap="round"
          className="transition-all duration-700"
        />
      </svg>
      <span className="absolute inset-0 flex items-center justify-center text-[10px] font-mono font-semibold text-zinc-300">
        {score}
      </span>
    </div>
  );
}

function LeadCard({
  lead,
  onApprove,
  onDismiss,
  onEdit,
  isEditing,
  editText,
  setEditText,
  onEditSave,
  onEditCancel,
}: {
  lead: Lead;
  onApprove: () => void;
  onDismiss: () => void;
  onEdit: () => void;
  isEditing: boolean;
  editText: string;
  setEditText: (v: string) => void;
  onEditSave: () => void;
  onEditCancel: () => void;
}) {
  const intent = INTENT_STYLES[lead.intent] ?? INTENT_STYLES.technical;
  const priority = PRIORITY_STYLES[lead.priority] ?? PRIORITY_STYLES.low;
  const sourceIcon = SOURCE_ICONS[lead.source] ?? "?";
  const timeAgo = getTimeAgo(lead.detected_at);

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, x: -20, transition: { duration: 0.2 } }}
      className="card-hover rounded-xl border border-white/[0.06] bg-[#111113] overflow-hidden"
    >
      {/* Header row */}
      <div className="px-5 pt-4 pb-3 flex items-center gap-3">
        {/* Source icon */}
        <div className="w-8 h-8 rounded-lg bg-amber-500/10 flex items-center justify-center flex-shrink-0">
          <span className="text-xs font-bold text-amber-400 font-mono">{sourceIcon}</span>
        </div>

        {/* Score ring */}
        <ScoreRing score={lead.relevance_score} />

        {/* Meta */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <a
              href={lead.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm font-medium text-zinc-200 hover:text-white transition-colors"
            >
              @{lead.author}
            </a>
            <span className={`text-[10px] px-2 py-0.5 rounded-full border font-semibold uppercase tracking-wider ${intent.bg} ${intent.text}`}>
              {lead.intent.replace("_", " ")}
            </span>
            <span className={`text-[10px] px-1.5 py-0.5 rounded font-mono font-semibold ${priority.bg} ${priority.text}`}>
              {priority.label}
            </span>
          </div>
          <p className="text-[11px] text-zinc-600 mt-0.5">{lead.source} &middot; {timeAgo}</p>
        </div>
      </div>

      {/* Original text */}
      <div className="px-5 pb-3">
        <div className="rounded-lg bg-white/[0.02] border border-white/[0.04] p-3.5">
          <p className="text-[13px] text-zinc-400 leading-relaxed line-clamp-4">{stripHtml(lead.original_text)}</p>
        </div>
      </div>

      {/* AI reply or editor */}
      <div className="px-5 pb-3">
        {isEditing ? (
          <div className="space-y-2">
            <Textarea
              value={editText}
              onChange={(e) => setEditText(e.target.value)}
              rows={5}
              className="bg-white/[0.03] border-white/[0.08] text-[13px] text-zinc-300 focus:border-amber-500/30 rounded-lg"
            />
            <div className="flex gap-2">
              <Button
                size="sm"
                className="bg-amber-500 hover:bg-amber-600 text-black font-semibold text-xs px-4"
                onClick={onEditSave}
              >
                Save & Publish
              </Button>
              <Button size="sm" variant="ghost" className="text-xs text-zinc-500" onClick={onEditCancel}>
                Cancel
              </Button>
            </div>
          </div>
        ) : (
          <div className="rounded-lg bg-amber-500/[0.03] border border-amber-500/[0.08] p-3.5 relative">
            <div className="absolute top-3 right-3">
              <span className="text-[9px] font-mono text-amber-500/40 uppercase tracking-widest">AI Draft</span>
            </div>
            <p className="text-[13px] text-zinc-400 leading-relaxed pr-16">{lead.suggested_reply}</p>
          </div>
        )}
      </div>

      {/* Action bar */}
      {!isEditing && (
        <div className="px-5 pb-4 flex items-center gap-2">
          <Button
            size="sm"
            className="bg-emerald-500/90 hover:bg-emerald-500 text-black font-semibold text-xs px-5 rounded-lg"
            onClick={onApprove}
          >
            Publish
          </Button>
          <Button
            size="sm"
            variant="ghost"
            className="text-xs text-zinc-500 hover:text-zinc-300 px-4"
            onClick={onEdit}
          >
            Edit Reply
          </Button>
          <div className="flex-1" />
          <Button
            size="sm"
            variant="ghost"
            className="text-xs text-zinc-600 hover:text-red-400 px-3"
            onClick={onDismiss}
          >
            Dismiss
          </Button>
        </div>
      )}
    </motion.div>
  );
}

function stripHtml(text: string): string {
  return text.replace(/<[^>]*>/g, " ").replace(/&[a-z]+;/g, " ").replace(/\s+/g, " ").trim();
}

function getTimeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

export default function ScoutPage() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editText, setEditText] = useState("");

  useEffect(() => {
    fetchLeads({ status: "pending_review" })
      .then(setLeads)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const handleApprove = async (lead: Lead) => {
    await updateLead(lead.id, { status: "approved" });
    try { await publishLead(lead.id); } catch {}
    setLeads((prev) => prev.filter((l) => l.id !== lead.id));
  };

  const handleDismiss = async (id: number) => {
    await updateLead(id, { status: "dismissed" });
    setLeads((prev) => prev.filter((l) => l.id !== id));
  };

  const handleEditSave = async (id: number) => {
    await updateLead(id, { edited_reply: editText, status: "approved" });
    try { await publishLead(id); } catch {}
    setLeads((prev) => prev.filter((l) => l.id !== id));
    setEditingId(null);
  };

  return (
    <div className="p-8 max-w-[900px] mx-auto">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-6 flex items-center justify-between"
      >
        <div>
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-amber-500/10 flex items-center justify-center">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
              </svg>
            </div>
            <h1 className="text-xl font-bold tracking-tight text-white">ScoutBot</h1>
          </div>
          <p className="text-sm text-zinc-500 mt-1 ml-9">Review and publish lead responses</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="stat-number text-sm font-semibold text-amber-400 bg-amber-500/10 px-3 py-1.5 rounded-lg">
            {leads.length} pending
          </div>
        </div>
      </motion.div>

      {/* Leads list */}
      <div className="space-y-3">
        <AnimatePresence>
          {leads.map((lead) => (
            <LeadCard
              key={lead.id}
              lead={lead}
              onApprove={() => handleApprove(lead)}
              onDismiss={() => handleDismiss(lead.id)}
              onEdit={() => { setEditingId(lead.id); setEditText(lead.suggested_reply); }}
              isEditing={editingId === lead.id}
              editText={editText}
              setEditText={setEditText}
              onEditSave={() => handleEditSave(lead.id)}
              onEditCancel={() => setEditingId(null)}
            />
          ))}
        </AnimatePresence>
      </div>

      {/* Empty state */}
      {!loading && leads.length === 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="text-center py-20"
        >
          <div className="w-16 h-16 rounded-2xl bg-amber-500/5 border border-amber-500/10 flex items-center justify-center mx-auto mb-4">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="opacity-40">
              <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
          </div>
          <p className="text-zinc-500 text-sm">No pending leads</p>
          <p className="text-zinc-600 text-xs mt-1">ScoutBot is scanning for new discussions...</p>
        </motion.div>
      )}

      {loading && (
        <div className="text-center py-20">
          <div className="w-6 h-6 border-2 border-amber-500/30 border-t-amber-400 rounded-full animate-spin mx-auto" />
          <p className="text-zinc-500 text-xs mt-3">Loading leads...</p>
        </div>
      )}
    </div>
  );
}
