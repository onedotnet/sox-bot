"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { fetchDashboardStats, fetchCommunityStats, type CommunityStats } from "@/lib/api";

interface DashboardStats {
  total_leads: number;
  pending_review: number;
  published: number;
  enterprise_leads: number;
}

const fadeUp = {
  hidden: { opacity: 0, y: 12 },
  visible: (i: number) => ({
    opacity: 1, y: 0,
    transition: { delay: i * 0.08, duration: 0.4 },
  }),
};

function BotCard({
  name,
  status,
  color,
  glowClass,
  metrics,
  icon,
  index,
}: {
  name: string;
  status: string;
  color: string;
  glowClass: string;
  metrics: { label: string; value: string | number }[];
  icon: React.ReactNode;
  index: number;
}) {
  return (
    <motion.div
      custom={index}
      initial="hidden"
      animate="visible"
      variants={fadeUp}
      className={`card-hover relative rounded-xl border border-white/[0.06] bg-[#111113] overflow-hidden`}
    >
      {/* Top accent line */}
      <div className={`h-[2px] ${color}`} />

      <div className="p-5">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2.5">
            <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${color} bg-opacity-10`}
              style={{ background: `linear-gradient(135deg, ${color === 'bg-amber-400' ? 'rgba(245,158,11,0.15)' : color === 'bg-blue-400' ? 'rgba(59,130,246,0.15)' : color === 'bg-emerald-400' ? 'rgba(16,185,129,0.15)' : 'rgba(168,85,247,0.15)'}, transparent)` }}>
              {icon}
            </div>
            <div>
              <h3 className="text-sm font-semibold text-white">{name}</h3>
              <p className="text-[10px] text-zinc-500 uppercase tracking-wider font-medium">{status}</p>
            </div>
          </div>
          <div className="w-2 h-2 rounded-full bg-emerald-400 pulse-dot" />
        </div>

        <div className="grid grid-cols-2 gap-3">
          {metrics.map((m) => (
            <div key={m.label} className="bg-white/[0.03] rounded-lg px-3 py-2.5">
              <p className="stat-number text-xl font-semibold text-white">{m.value}</p>
              <p className="text-[10px] text-zinc-500 mt-0.5 font-medium">{m.label}</p>
            </div>
          ))}
        </div>
      </div>
    </motion.div>
  );
}

function StatPill({ label, value, color }: { label: string; value: string | number; color: string }) {
  return (
    <div className="flex items-center gap-3 px-4 py-3 rounded-xl bg-white/[0.03] border border-white/[0.05]">
      <div className={`w-2.5 h-2.5 rounded-full ${color}`} />
      <div>
        <p className="stat-number text-lg font-semibold text-white">{value}</p>
        <p className="text-[10px] text-zinc-500 font-medium uppercase tracking-wider">{label}</p>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats>({
    total_leads: 0, pending_review: 0, published: 0, enterprise_leads: 0,
  });
  const [communityStats, setCommunityStats] = useState<CommunityStats | null>(null);

  useEffect(() => {
    fetchDashboardStats().then(setStats).catch(console.error);
    fetchCommunityStats().then(setCommunityStats).catch(() => {});
  }, []);

  return (
    <div className="p-8 max-w-[1400px] mx-auto">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="mb-8"
      >
        <h1 className="text-2xl font-bold tracking-tight text-white">Command Center</h1>
        <p className="text-sm text-zinc-500 mt-1">Your AI marketing team at a glance</p>
      </motion.div>

      {/* Quick stats row */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2, duration: 0.5 }}
        className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-8"
      >
        <StatPill label="Pending Review" value={stats.pending_review} color="bg-amber-400" />
        <StatPill label="Published" value={stats.published} color="bg-emerald-400" />
        <StatPill label="Enterprise Leads" value={stats.enterprise_leads} color="bg-red-400" />
        <StatPill label="Total Leads" value={stats.total_leads} color="bg-blue-400" />
      </motion.div>

      {/* Bot cards grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <BotCard
          name="ScoutBot"
          status="Monitoring 6 platforms"
          color="bg-amber-400"
          glowClass="glow-scout"
          index={0}
          icon={
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
          }
          metrics={[
            { label: "Pending Review", value: stats.pending_review },
            { label: "Published", value: stats.published },
            { label: "Enterprise Leads", value: stats.enterprise_leads },
            { label: "Total Discovered", value: stats.total_leads },
          ]}
        />
        <BotCard
          name="ContentBot"
          status="Multi-model pipeline"
          color="bg-blue-400"
          glowClass="glow-content"
          index={1}
          icon={
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 20h9" /><path d="M16.376 3.622a1 1 0 0 1 3.002 3.002L7.368 18.635a2 2 0 0 1-.855.506l-2.872.838.838-2.872a2 2 0 0 1 .506-.855z" />
            </svg>
          }
          metrics={[
            { label: "Weekly Schedule", value: "5 slots" },
            { label: "Cost per Article", value: "$0.09" },
            { label: "Models Used", value: 3 },
            { label: "Languages", value: "EN + ZH" },
          ]}
        />
        <BotCard
          name="CommunityBot"
          status="Discord + WeChat"
          color="bg-emerald-400"
          glowClass="glow-community"
          index={2}
          icon={
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#10b981" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
            </svg>
          }
          metrics={[
            { label: "Messages Today", value: communityStats?.total_messages ?? 0 },
            { label: "Auto-Resolved", value: communityStats?.auto_resolved ?? 0 },
            { label: "Escalated", value: communityStats?.escalated ?? 0 },
            { label: "Resolution Rate", value: communityStats ? `${communityStats.resolution_rate.toFixed(0)}%` : "—" },
          ]}
        />
        <BotCard
          name="AnalyticsBot"
          status="Weekly reports"
          color="bg-purple-400"
          glowClass="glow-analytics"
          index={3}
          icon={
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#a855f7" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M3 3v18h18" /><path d="M18 17V9" /><path d="M13 17V5" /><path d="M8 17v-3" />
            </svg>
          }
          metrics={[
            { label: "Reports Generated", value: 0 },
            { label: "Action Items", value: 0 },
            { label: "Schedule", value: "Sun 9pm" },
            { label: "Coverage", value: "4 bots" },
          ]}
        />
      </div>

      {/* Bottom info bar */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.6, duration: 0.5 }}
        className="mt-8 flex items-center justify-between px-5 py-3 rounded-xl bg-white/[0.02] border border-white/[0.04]"
      >
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 text-[11px] text-zinc-500">
            <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 pulse-dot" />
            All systems operational
          </div>
          <div className="w-px h-3 bg-white/[0.06]" />
          <span className="text-[11px] text-zinc-600 font-mono">
            12 keywords monitored
          </span>
        </div>
        <span className="text-[11px] text-zinc-600 font-mono">
          sox.bot v0.4.0
        </span>
      </motion.div>
    </div>
  );
}
