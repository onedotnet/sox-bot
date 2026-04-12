"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchDashboardStats } from "@/lib/api";

interface DashboardStats {
  total_leads: number;
  pending_review: number;
  published: number;
  enterprise_leads: number;
}

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats>({
    total_leads: 0,
    pending_review: 0,
    published: 0,
    enterprise_leads: 0,
  });

  useEffect(() => {
    fetchDashboardStats().then(setStats).catch(console.error);
  }, []);

  const cards = [
    { title: "待审核", value: stats.pending_review, color: "text-yellow-400" },
    { title: "已发布", value: stats.published, color: "text-green-400" },
    { title: "企业线索", value: stats.enterprise_leads, color: "text-red-400" },
    { title: "总线索", value: stats.total_leads, color: "text-blue-400" },
  ];

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">sox.bot Dashboard</h1>
      <div className="grid grid-cols-4 gap-4">
        {cards.map((card) => (
          <Card key={card.title} className="bg-zinc-900 border-zinc-800">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-zinc-400">{card.title}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className={`text-3xl font-bold ${card.color}`}>{card.value}</p>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
