"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import {
  AnalyticsOverview,
  WeeklyReport,
  fetchAnalyticsOverview,
  fetchWeeklyReports,
  triggerReport,
} from "@/lib/api";

function TrendBadge({ value }: { value: number }) {
  if (value > 0) {
    return (
      <span className="text-xs text-green-400 font-medium">
        ↑ {value.toFixed(1)}%
      </span>
    );
  }
  if (value < 0) {
    return (
      <span className="text-xs text-red-400 font-medium">
        ↓ {Math.abs(value).toFixed(1)}%
      </span>
    );
  }
  return <span className="text-xs text-zinc-500 font-medium">—</span>;
}

function OverviewCard({
  title,
  primary,
  primaryLabel,
  secondary,
  secondaryLabel,
  trend,
}: {
  title: string;
  primary: number | string;
  primaryLabel: string;
  secondary: number | string;
  secondaryLabel: string;
  trend: number;
}) {
  return (
    <Card className="bg-zinc-900 border-zinc-800">
      <CardHeader className="pb-1 pt-4 px-5">
        <div className="flex items-center justify-between">
          <p className="text-xs font-semibold text-zinc-400 uppercase tracking-wider">
            {title}
          </p>
          <TrendBadge value={trend} />
        </div>
      </CardHeader>
      <CardContent className="px-5 pb-4 space-y-2">
        <div>
          <p className="text-2xl font-bold text-zinc-100">{primary}</p>
          <p className="text-xs text-zinc-500">{primaryLabel}</p>
        </div>
        <div>
          <p className="text-lg font-semibold text-zinc-300">{secondary}</p>
          <p className="text-xs text-zinc-500">{secondaryLabel}</p>
        </div>
      </CardContent>
    </Card>
  );
}

function ReportCard({ report }: { report: WeeklyReport }) {
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
    <Card className="bg-zinc-900 border-zinc-800">
      <CardHeader className="pb-2 pt-4 px-5">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-semibold text-zinc-100">
              Week of {weekStart} – {weekEnd}
            </p>
            <div className="flex gap-4 mt-1 text-xs text-zinc-400">
              <span>{report.leads_published} leads published</span>
              <span>{report.content_published} content published</span>
              <span>
                {(report.resolution_rate * 100).toFixed(1)}% resolution rate
              </span>
            </div>
          </div>
          <button
            onClick={() => setExpanded((v) => !v)}
            className="text-xs text-zinc-400 hover:text-zinc-200 px-3 py-1 rounded hover:bg-zinc-800 transition-colors"
          >
            {expanded ? "Collapse" : "Expand"}
          </button>
        </div>
      </CardHeader>

      {expanded && (
        <CardContent className="px-5 pb-5 space-y-4">
          {/* Stats grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {[
              { label: "Leads Discovered", value: report.leads_discovered },
              { label: "Enterprise Leads", value: report.enterprise_leads },
              { label: "Content Generated", value: report.content_generated },
              { label: "Messages Received", value: report.messages_received },
              { label: "Auto-Resolved", value: report.messages_auto_resolved },
              { label: "Escalated", value: report.messages_escalated },
              { label: "Community Leads", value: report.community_leads },
              {
                label: "Content Cost",
                value: `$${(report.content_cost_cents / 100).toFixed(2)}`,
              },
            ].map((item) => (
              <div key={item.label} className="bg-zinc-800 rounded p-3">
                <p className="text-xs text-zinc-400 mb-0.5">{item.label}</p>
                <p className="text-base font-semibold text-zinc-100">
                  {item.value}
                </p>
              </div>
            ))}
          </div>

          {/* Summary */}
          {report.summary && (
            <div className="bg-zinc-800 rounded p-4">
              <p className="text-xs text-zinc-400 mb-2 font-semibold uppercase tracking-wider">
                Summary
              </p>
              <p className="text-sm text-zinc-300 whitespace-pre-line">
                {report.summary}
              </p>
            </div>
          )}

          {/* Action items */}
          {actionItems.length > 0 && (
            <div className="bg-zinc-800 rounded p-4">
              <p className="text-xs text-zinc-400 mb-2 font-semibold uppercase tracking-wider">
                Action Items
              </p>
              <ul className="space-y-1.5">
                {actionItems.map((item, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-zinc-300">
                    <span className="mt-0.5 h-4 w-4 shrink-0 rounded border border-zinc-600 flex items-center justify-center">
                      <span className="h-2 w-2 rounded-sm bg-zinc-600" />
                    </span>
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </CardContent>
      )}
    </Card>
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
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Analytics</h1>
        <Button
          className="bg-zinc-700 hover:bg-zinc-600"
          onClick={handleGenerate}
          disabled={generating}
        >
          {generating ? "Generating..." : "Generate Report"}
        </Button>
      </div>

      {/* Live Overview */}
      <section className="mb-8">
        <h2 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider mb-3">
          Live Overview
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <OverviewCard
            title="Scout"
            primary={overview?.scout_pending ?? "—"}
            primaryLabel="Pending leads"
            secondary={overview?.scout_published_this_week ?? "—"}
            secondaryLabel="Published this week"
            trend={overview?.leads_trend ?? 0}
          />
          <OverviewCard
            title="Content"
            primary={overview?.content_drafts ?? "—"}
            primaryLabel="Drafts"
            secondary={overview?.content_scheduled ?? "—"}
            secondaryLabel="Scheduled"
            trend={overview?.content_trend ?? 0}
          />
          <OverviewCard
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
        <h2 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider mb-3">
          Weekly Reports
        </h2>

        {loadingReports && (
          <p className="text-zinc-500 text-center py-12">Loading reports...</p>
        )}

        {!loadingReports && (
          <div className="space-y-3">
            {reports.map((report) => (
              <ReportCard key={report.id} report={report} />
            ))}
            {reports.length === 0 && (
              <p className="text-zinc-500 text-center py-12">
                No reports yet. Click &quot;Generate Report&quot; to create one.
              </p>
            )}
          </div>
        )}
      </section>
    </div>
  );
}
