"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/button";
import {
  AnalyticsOverview,
  WeeklyReport,
  fetchAnalyticsOverview,
  fetchWeeklyReports,
  triggerReport,
} from "@/lib/api";


function AnalyticsIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#a855f7" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <line x1="18" y1="20" x2="18" y2="10" />
      <line x1="12" y1="20" x2="12" y2="4" />
      <line x1="6" y1="20" x2="6" y2="14" />
    </svg>
  );
}

function TrendBadge({ value }: { value: number }) {
  if (value > 0) {
    return (
      <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
        ↑ {value.toFixed(1)}%
      </span>
    );
  }
  if (value < 0) {
    return (
      <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-red-500/10 border border-red-500/20 text-red-400">
        ↓ {Math.abs(value).toFixed(1)}%
      </span>
    );
  }
  return (
    <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-zinc-500/10 border border-zinc-500/20 text-zinc-500">
      — flat
    </span>
  );
}

function OverviewCard({
  title,
  primary,
  primaryLabel,
  secondary,
  secondaryLabel,
  trend,
  index,
}: {
  title: string;
  primary: number | string;
  primaryLabel: string;
  secondary: number | string;
  secondaryLabel: string;
  trend: number;
  index: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.08, duration: 0.35 }}
      className="card-hover rounded-xl border border-white/[0.06] bg-[#111113] overflow-hidden"
    >
      <div className="h-[2px] bg-purple-500/60" />
      <div className="p-5">
        <div className="flex items-center justify-between mb-4">
          <p className="text-[10px] font-semibold text-zinc-500 uppercase tracking-widest">{title}</p>
          <TrendBadge value={trend} />
        </div>
        <div className="space-y-3">
          <div>
            <p className="stat-number text-3xl font-semibold text-white leading-none">{primary}</p>
            <p className="text-[11px] text-zinc-500 mt-1 font-medium">{primaryLabel}</p>
          </div>
          <div className="pt-2 border-t border-white/[0.05]">
            <p className="stat-number text-lg font-semibold text-zinc-300 leading-none">{secondary}</p>
            <p className="text-[11px] text-zinc-600 mt-0.5 font-medium">{secondaryLabel}</p>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

function StatCell({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-lg bg-white/[0.02] border border-white/[0.04] p-3">
      <p className="text-[10px] text-zinc-500 font-medium uppercase tracking-wider mb-1">{label}</p>
      <p className="stat-number text-base font-semibold text-white">{value}</p>
    </div>
  );
}

function ReportCard({ report, index }: { report: WeeklyReport; index: number }) {
  const [expanded, setExpanded] = useState(false);

  let actionItems: string[] = [];
  try {
    actionItems = JSON.parse(report.action_items);
  } catch {
    // ignore parse errors
  }

  const weekStart = new Date(report.week_start).toLocaleDateString();
  const weekEnd = new Date(report.week_end).toLocaleDateString();

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.06, duration: 0.35 }}
      className="card-hover rounded-xl border border-white/[0.06] bg-[#111113] overflow-hidden"
    >
      <div className="px-5 pt-4 pb-4">
        <div className="flex items-center justify-between gap-4">
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold text-white">
              Week of {weekStart} – {weekEnd}
            </p>
            <div className="flex flex-wrap gap-3 mt-1.5">
              <span className="text-[11px] text-zinc-500">
                <span className="stat-number text-zinc-300 font-semibold">{report.leads_published}</span> leads published
              </span>
              <span className="text-[11px] text-zinc-500">
                <span className="stat-number text-zinc-300 font-semibold">{report.content_published}</span> content published
              </span>
              <span className="text-[11px] text-zinc-500">
                <span className="stat-number text-zinc-300 font-semibold">{(report.resolution_rate * 100).toFixed(1)}%</span> resolution
              </span>
            </div>
          </div>
          <button
            onClick={() => setExpanded((v) => !v)}
            className="flex items-center gap-1.5 text-[11px] text-zinc-500 hover:text-zinc-300 px-3 py-1.5 rounded-lg border border-white/[0.06] hover:border-white/[0.10] bg-white/[0.02] hover:bg-white/[0.04] transition-all flex-shrink-0"
          >
            <span>{expanded ? "Collapse" : "Expand"}</span>
            <svg
              width="10"
              height="10"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
              className={`transition-transform duration-200 ${expanded ? "rotate-180" : ""}`}
            >
              <polyline points="6 9 12 15 18 9" />
            </svg>
          </button>
        </div>

        <AnimatePresence>
          {expanded && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.25 }}
              className="overflow-hidden"
            >
              <div className="pt-4 space-y-4">
                {/* Stats grid */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                  <StatCell label="Leads Discovered" value={report.leads_discovered} />
                  <StatCell label="Enterprise Leads" value={report.enterprise_leads} />
                  <StatCell label="Content Generated" value={report.content_generated} />
                  <StatCell label="Messages Received" value={report.messages_received} />
                  <StatCell label="Auto-Resolved" value={report.messages_auto_resolved} />
                  <StatCell label="Escalated" value={report.messages_escalated} />
                  <StatCell label="Community Leads" value={report.community_leads} />
                  <StatCell label="Content Cost" value={`$${(report.content_cost_cents / 100).toFixed(2)}`} />
                </div>

                {/* Summary */}
                {report.summary && (
                  <div className="rounded-lg bg-purple-500/[0.04] border border-purple-500/[0.10] p-4">
                    <p className="text-[10px] font-semibold text-purple-400/70 uppercase tracking-widest mb-2">Summary</p>
                    <p className="text-[13px] text-zinc-400 leading-relaxed whitespace-pre-line">{report.summary}</p>
                  </div>
                )}

                {/* Action items */}
                {actionItems.length > 0 && (
                  <div className="rounded-lg bg-white/[0.02] border border-white/[0.04] p-4">
                    <p className="text-[10px] font-semibold text-zinc-500 uppercase tracking-widest mb-3">Action Items</p>
                    <ul className="space-y-2">
                      {actionItems.map((item, i) => (
                        <li key={i} className="flex items-start gap-2.5 text-[13px] text-zinc-400">
                          <div className="mt-0.5 w-4 h-4 rounded border border-zinc-600 flex items-center justify-center flex-shrink-0">
                            <div className="w-1.5 h-1.5 rounded-sm bg-zinc-600" />
                          </div>
                          {item}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  );
}

export default function AnalyticsPage() {
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [reports, setReports] = useState<WeeklyReport[]>([]);
  const [loadingReports, setLoadingReports] = useState(false);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    fetchAnalyticsOverview().then(setOverview).catch(console.error);
    setLoadingReports(true);
    fetchWeeklyReports()
      .then(setReports)
      .catch(console.error)
      .finally(() => setLoadingReports(false));
  }, []);

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      await triggerReport();
      const updated = await fetchWeeklyReports();
      setReports(updated);
    } catch (err) {
      console.error(err);
    } finally {
      setGenerating(false);
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
            <div className="w-7 h-7 rounded-lg bg-purple-500/10 flex items-center justify-center">
              <AnalyticsIcon />
            </div>
            <h1 className="text-xl font-bold tracking-tight text-white">Analytics</h1>
          </div>
          <p className="text-sm text-zinc-500 mt-1 ml-9">Live metrics and weekly performance reports</p>
        </div>
        <Button
          onClick={handleGenerate}
          disabled={generating}
          className="bg-purple-600/20 hover:bg-purple-600/30 text-purple-400 border border-purple-500/20 text-xs font-semibold px-4 rounded-lg"
        >
          {generating ? "Generating..." : "Generate Report"}
        </Button>
      </motion.div>

      {/* Live Overview */}
      <section className="mb-8">
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.05 }}
          className="text-[10px] font-semibold text-zinc-600 uppercase tracking-widest mb-3"
        >
          Live Overview
        </motion.p>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <OverviewCard
            index={0}
            title="Scout"
            primary={overview?.scout_pending ?? "—"}
            primaryLabel="Pending leads"
            secondary={overview?.scout_published_this_week ?? "—"}
            secondaryLabel="Published this week"
            trend={overview?.leads_trend ?? 0}
          />
          <OverviewCard
            index={1}
            title="Content"
            primary={overview?.content_drafts ?? "—"}
            primaryLabel="Drafts"
            secondary={overview?.content_scheduled ?? "—"}
            secondaryLabel="Scheduled"
            trend={overview?.content_trend ?? 0}
          />
          <OverviewCard
            index={2}
            title="Community"
            primary={overview?.community_messages_today ?? "—"}
            primaryLabel="Messages today"
            secondary={
              overview
                ? `${(overview.community_resolution_rate * 100).toFixed(1)}%`
                : "—"
            }
            secondaryLabel="Resolution rate"
            trend={overview?.messages_trend ?? 0}
          />
        </div>
      </section>

      {/* Weekly Reports */}
      <section>
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.15 }}
          className="text-[10px] font-semibold text-zinc-600 uppercase tracking-widest mb-3"
        >
          Weekly Reports
        </motion.p>

        {loadingReports && (
          <div className="text-center py-20">
            <div className="w-6 h-6 border-2 border-purple-500/30 border-t-purple-400 rounded-full animate-spin mx-auto" />
            <p className="text-zinc-500 text-xs mt-3">Loading reports...</p>
          </div>
        )}

        {!loadingReports && (
          <div className="space-y-3">
            {reports.map((report, i) => (
              <ReportCard key={report.id} report={report} index={i} />
            ))}

            {reports.length === 0 && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.2 }}
                className="text-center py-20"
              >
                <div className="w-16 h-16 rounded-2xl bg-purple-500/5 border border-purple-500/10 flex items-center justify-center mx-auto mb-4">
                  <AnalyticsIcon />
                </div>
                <p className="text-zinc-500 text-sm">No reports yet.</p>
                <p className="text-zinc-600 text-xs mt-1">Click &quot;Generate Report&quot; to create one.</p>
              </motion.div>
            )}
          </div>
        )}
      </section>
    </div>
  );
}
