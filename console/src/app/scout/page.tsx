"use client";

import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
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
}

export default function ScoutPage() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editText, setEditText] = useState("");

  useEffect(() => {
    fetchLeads({ status: "pending_review" }).then(setLeads).catch(console.error);
  }, []);

  const handleApprove = async (lead: Lead) => {
    await updateLead(lead.id, { status: "approved" });
    await publishLead(lead.id);
    setLeads((prev) => prev.filter((l) => l.id !== lead.id));
  };

  const handleDismiss = async (id: number) => {
    await updateLead(id, { status: "dismissed" });
    setLeads((prev) => prev.filter((l) => l.id !== id));
  };

  const handleEditSave = async (id: number) => {
    await updateLead(id, { edited_reply: editText, status: "approved" });
    await publishLead(id);
    setLeads((prev) => prev.filter((l) => l.id !== id));
    setEditingId(null);
  };

  const priorityColor: Record<string, string> = {
    high: "bg-red-600",
    medium: "bg-yellow-600",
    low: "bg-zinc-600",
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">ScoutBot - 线索审核</h1>
      <div className="space-y-4">
        {leads.map((lead) => (
          <Card key={lead.id} className="bg-zinc-900 border-zinc-800">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <div className="flex items-center gap-2">
                <Badge variant="outline">{lead.source}</Badge>
                <Badge className={priorityColor[lead.priority] ?? "bg-zinc-600"}>{lead.priority}</Badge>
                <Badge variant="outline">{lead.intent}</Badge>
                <span className="text-sm text-zinc-400">Score: {lead.relevance_score}</span>
              </div>
              <a href={lead.source_url} target="_blank" rel="noopener noreferrer" className="text-sm text-blue-400 hover:underline">
                @{lead.author}
              </a>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="bg-zinc-800 rounded p-3">
                <p className="text-sm text-zinc-300 whitespace-pre-wrap">{lead.original_text}</p>
              </div>

              {editingId === lead.id ? (
                <div className="space-y-2">
                  <Textarea
                    value={editText}
                    onChange={(e) => setEditText(e.target.value)}
                    rows={6}
                    className="bg-zinc-800"
                  />
                  <div className="flex gap-2">
                    <Button size="sm" onClick={() => handleEditSave(lead.id)}>Save & Publish</Button>
                    <Button size="sm" variant="outline" onClick={() => setEditingId(null)}>Cancel</Button>
                  </div>
                </div>
              ) : (
                <div className="bg-zinc-800/50 rounded p-3 border border-zinc-700">
                  <p className="text-xs text-zinc-500 mb-1">AI 建议回复:</p>
                  <p className="text-sm text-zinc-300 whitespace-pre-wrap">{lead.suggested_reply}</p>
                </div>
              )}

              <div className="flex gap-2">
                <Button size="sm" className="bg-green-600 hover:bg-green-700" onClick={() => handleApprove(lead)}>
                  Publish
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => {
                    setEditingId(lead.id);
                    setEditText(lead.suggested_reply);
                  }}
                >
                  Edit
                </Button>
                <Button size="sm" variant="ghost" className="text-red-400" onClick={() => handleDismiss(lead.id)}>
                  Dismiss
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
        {leads.length === 0 && (
          <p className="text-zinc-500 text-center py-12">No pending leads. ScoutBot is scanning...</p>
        )}
      </div>
    </div>
  );
}
