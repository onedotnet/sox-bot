"use client";

import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { ContentItem, fetchContent, updateContent, generateContent } from "@/lib/api";

const TABS = [
  { label: "Drafts", status: "draft" },
  { label: "Review", status: "review" },
  { label: "Scheduled", status: "scheduled" },
  { label: "Published", status: "published" },
] as const;

type TabStatus = (typeof TABS)[number]["status"];

export default function ContentPage() {
  const [activeTab, setActiveTab] = useState<TabStatus>("draft");
  const [items, setItems] = useState<ContentItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editTitle, setEditTitle] = useState("");
  const [editBody, setEditBody] = useState("");
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [showGenerate, setShowGenerate] = useState(false);
  const [genKeyword, setGenKeyword] = useState("");
  const [genType, setGenType] = useState("blog_post");
  const [genLang, setGenLang] = useState("en");
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    setLoading(true);
    fetchContent({ status: activeTab })
      .then(setItems)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [activeTab]);

  const handleApprove = async (item: ContentItem) => {
    await updateContent(item.id, { status: "scheduled" });
    setItems((prev) => prev.filter((i) => i.id !== item.id));
  };

  const handleReject = async (id: number) => {
    await updateContent(id, { status: "draft" });
    setItems((prev) => prev.filter((i) => i.id !== id));
  };

  const handleEditSave = async (id: number) => {
    await updateContent(id, { title: editTitle, body: editBody });
    setItems((prev) =>
      prev.map((i) => (i.id === id ? { ...i, title: editTitle, body: editBody } : i))
    );
    setEditingId(null);
  };

  const handleGenerate = async () => {
    if (!genKeyword.trim()) return;
    setGenerating(true);
    try {
      await generateContent({ seo_keyword: genKeyword, content_type: genType, language: genLang });
      setShowGenerate(false);
      setGenKeyword("");
      // Refresh if on drafts tab
      if (activeTab === "draft") {
        fetchContent({ status: "draft" }).then(setItems).catch(console.error);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setGenerating(false);
    }
  };

  const qualityColor = (passed: boolean) =>
    passed ? "bg-green-700 text-green-100" : "bg-red-800 text-red-100";

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Content Management</h1>
        <Button className="bg-green-600 hover:bg-green-700" onClick={() => setShowGenerate((v) => !v)}>
          {showGenerate ? "Cancel" : "Generate New"}
        </Button>
      </div>

      {showGenerate && (
        <Card className="bg-zinc-900 border-zinc-800 mb-6">
          <CardContent className="pt-4 space-y-3">
            <div className="flex gap-3 flex-wrap">
              <div className="flex-1 min-w-48">
                <label className="text-xs text-zinc-400 mb-1 block">SEO Keyword</label>
                <Input
                  value={genKeyword}
                  onChange={(e) => setGenKeyword(e.target.value)}
                  placeholder="e.g. AI chatbot integration"
                  className="bg-zinc-800 border-zinc-700"
                />
              </div>
              <div>
                <label className="text-xs text-zinc-400 mb-1 block">Content Type</label>
                <select
                  value={genType}
                  onChange={(e) => setGenType(e.target.value)}
                  className="bg-zinc-800 border border-zinc-700 rounded px-3 py-2 text-sm text-zinc-100 h-10"
                >
                  <option value="blog_post">Blog Post</option>
                  <option value="twitter_thread">Twitter Thread</option>
                  <option value="linkedin_post">LinkedIn Post</option>
                  <option value="reddit_post">Reddit Post</option>
                </select>
              </div>
              <div>
                <label className="text-xs text-zinc-400 mb-1 block">Language</label>
                <select
                  value={genLang}
                  onChange={(e) => setGenLang(e.target.value)}
                  className="bg-zinc-800 border border-zinc-700 rounded px-3 py-2 text-sm text-zinc-100 h-10"
                >
                  <option value="en">English</option>
                  <option value="zh">Chinese</option>
                  <option value="es">Spanish</option>
                  <option value="fr">French</option>
                  <option value="de">German</option>
                </select>
              </div>
              <div className="flex items-end">
                <Button
                  onClick={handleGenerate}
                  disabled={generating || !genKeyword.trim()}
                  className="bg-green-600 hover:bg-green-700"
                >
                  {generating ? "Generating..." : "Generate"}
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Tab navigation */}
      <div className="flex gap-1 mb-4 border-b border-zinc-800 pb-2">
        {TABS.map((tab) => (
          <button
            key={tab.status}
            onClick={() => setActiveTab(tab.status)}
            className={`px-4 py-1.5 rounded text-sm font-medium transition-colors ${
              activeTab === tab.status
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
          {items.map((item) => (
            <Card key={item.id} className="bg-zinc-900 border-zinc-800">
              <CardHeader className="flex flex-row items-start justify-between pb-2">
                <div className="space-y-1 flex-1 mr-4">
                  {editingId === item.id ? (
                    <Input
                      value={editTitle}
                      onChange={(e) => setEditTitle(e.target.value)}
                      className="bg-zinc-800 border-zinc-700 font-semibold"
                    />
                  ) : (
                    <h3 className="font-semibold text-zinc-100">{item.title}</h3>
                  )}
                  <div className="flex flex-wrap gap-1.5 mt-1">
                    <Badge variant="outline" className="text-xs">{item.content_type}</Badge>
                    <Badge variant="outline" className="text-xs">{item.language}</Badge>
                    <Badge variant="outline" className="text-xs">{item.target_platform}</Badge>
                    {item.seo_keyword && (
                      <Badge variant="outline" className="text-xs text-green-400 border-green-800">
                        {item.seo_keyword}
                      </Badge>
                    )}
                    <span className={`text-xs px-2 py-0.5 rounded ${qualityColor(item.quality_passed)}`}>
                      {item.quality_passed ? "QA Passed" : "QA Failed"}
                    </span>
                  </div>
                  {item.quality_notes && (
                    <p className="text-xs text-zinc-500 mt-1">{item.quality_notes}</p>
                  )}
                </div>
                <div className="text-xs text-zinc-500 whitespace-nowrap">
                  {new Date(item.created_at).toLocaleDateString()}
                </div>
              </CardHeader>

              <CardContent className="space-y-3">
                {editingId === item.id ? (
                  <div className="space-y-2">
                    <Textarea
                      value={editBody}
                      onChange={(e) => setEditBody(e.target.value)}
                      rows={8}
                      className="bg-zinc-800 border-zinc-700 text-sm"
                    />
                    <div className="flex gap-2">
                      <Button size="sm" className="bg-green-600 hover:bg-green-700" onClick={() => handleEditSave(item.id)}>
                        Save
                      </Button>
                      <Button size="sm" variant="outline" onClick={() => setEditingId(null)}>
                        Cancel
                      </Button>
                    </div>
                  </div>
                ) : (
                  expandedId === item.id && (
                    <div className="bg-zinc-800 rounded p-3">
                      <p className="text-sm text-zinc-300 whitespace-pre-wrap">{item.body}</p>
                    </div>
                  )
                )}

                <div className="flex flex-wrap gap-2">
                  {activeTab === "review" && (
                    <Button
                      size="sm"
                      className="bg-green-600 hover:bg-green-700"
                      onClick={() => handleApprove(item)}
                    >
                      Approve
                    </Button>
                  )}
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => {
                      setEditingId(item.id);
                      setEditTitle(item.title);
                      setEditBody(item.body);
                      setExpandedId(null);
                    }}
                  >
                    Edit
                  </Button>
                  {activeTab === "review" && (
                    <Button
                      size="sm"
                      variant="ghost"
                      className="text-red-400 hover:text-red-300"
                      onClick={() => handleReject(item.id)}
                    >
                      Reject
                    </Button>
                  )}
                  <Button
                    size="sm"
                    variant="ghost"
                    className="text-zinc-400"
                    onClick={() => setExpandedId((prev) => (prev === item.id ? null : item.id))}
                  >
                    {expandedId === item.id ? "Hide" : "View Body"}
                  </Button>
                  {item.published_url && (
                    <a
                      href={item.published_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs text-blue-400 hover:underline self-center"
                    >
                      View Published
                    </a>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}

          {items.length === 0 && (
            <p className="text-zinc-500 text-center py-12">No {activeTab} content items.</p>
          )}
        </div>
      )}
    </div>
  );
}
