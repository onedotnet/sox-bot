"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/button";
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


const CONTENT_TYPE_COLORS: Record<string, { bg: string; text: string }> = {
  seo_article: { bg: "bg-blue-500/10 border-blue-500/20", text: "text-blue-400" },
  industry_brief: { bg: "bg-sky-500/10 border-sky-500/20", text: "text-sky-400" },
  tutorial: { bg: "bg-emerald-500/10 border-emerald-500/20", text: "text-emerald-400" },
  comparison: { bg: "bg-purple-500/10 border-purple-500/20", text: "text-purple-400" },
  changelog: { bg: "bg-amber-500/10 border-amber-500/20", text: "text-amber-400" },
  social_post: { bg: "bg-orange-500/10 border-orange-500/20", text: "text-orange-400" },
};

function ContentIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 20h9" />
      <path d="M16.5 3.5a2.121 2.121 0 013 3L7 19l-4 1 1-4L16.5 3.5z" />
    </svg>
  );
}

function ContentCard({
  item,
  index,
  activeTab,
  isEditing,
  isExpanded,
  editTitle,
  editBody,
  setEditTitle,
  setEditBody,
  onEdit,
  onEditSave,
  onEditCancel,
  onApprove,
  onReject,
  onPublish,
  onToggleExpand,
}: {
  item: ContentItem;
  index: number;
  activeTab: TabStatus;
  isEditing: boolean;
  isExpanded: boolean;
  editTitle: string;
  editBody: string;
  setEditTitle: (v: string) => void;
  setEditBody: (v: string) => void;
  onEdit: () => void;
  onEditSave: () => void;
  onEditCancel: () => void;
  onApprove: () => void;
  onReject: () => void;
  onPublish: () => void;
  onToggleExpand: () => void;
}) {
  const typeStyle = CONTENT_TYPE_COLORS[item.content_type] ?? { bg: "bg-zinc-500/10 border-zinc-500/20", text: "text-zinc-400" };

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
      <div className="h-[2px] bg-blue-500/60" />

      <div className="px-5 pt-4 pb-3">
        {/* Header row */}
        <div className="flex items-start justify-between gap-4 mb-3">
          <div className="flex-1 min-w-0">
            {isEditing ? (
              <Input
                value={editTitle}
                onChange={(e) => setEditTitle(e.target.value)}
                className="bg-white/[0.04] border-white/[0.08] font-semibold text-white focus:border-blue-500/40"
              />
            ) : (
              <h3 className="font-semibold text-white leading-snug">{item.title}</h3>
            )}
          </div>
          {/* QA dot + date */}
          <div className="flex items-center gap-2.5 flex-shrink-0 pt-0.5">
            <div className="flex items-center gap-1.5">
              <div className={`w-2 h-2 rounded-full ${item.quality_passed ? "bg-emerald-400" : "bg-red-400"}`} />
              <span className={`text-[11px] font-medium ${item.quality_passed ? "text-emerald-400" : "text-red-400"}`}>
                {item.quality_passed ? "QA Pass" : "QA Fail"}
              </span>
            </div>
            <span className="text-[11px] text-zinc-600">
              {new Date(item.created_at).toLocaleDateString()}
            </span>
          </div>
        </div>

        {/* Badges */}
        <div className="flex flex-wrap gap-1.5 mb-3">
          <span className={`text-[10px] px-2 py-0.5 rounded-full border font-semibold uppercase tracking-wider ${typeStyle.bg} ${typeStyle.text}`}>
            {item.content_type.replace("_", " ")}
          </span>
          <span className="text-[10px] px-2 py-0.5 rounded-full border border-white/[0.08] bg-white/[0.03] text-zinc-400 font-medium uppercase tracking-wider">
            {item.language}
          </span>
          <span className="text-[10px] px-2 py-0.5 rounded-full border border-white/[0.08] bg-white/[0.03] text-zinc-400 font-medium uppercase tracking-wider">
            {item.target_platform}
          </span>
          {item.seo_keyword && (
            <span className="text-[10px] px-2 py-0.5 rounded-full border border-blue-500/20 bg-blue-500/[0.08] text-blue-400 font-medium">
              {item.seo_keyword}
            </span>
          )}
        </div>

        {item.quality_notes && (
          <p className="text-[11px] text-zinc-500 mb-3 pl-1 border-l-2 border-zinc-700">{item.quality_notes}</p>
        )}

        {/* Body content (edit or expand) */}
        <AnimatePresence>
          {isEditing && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              className="space-y-2 mb-3"
            >
              <Textarea
                value={editBody}
                onChange={(e) => setEditBody(e.target.value)}
                rows={8}
                className="bg-white/[0.03] border-white/[0.08] text-[13px] text-zinc-300 focus:border-blue-500/30 rounded-lg"
              />
              <div className="flex gap-2">
                <Button
                  size="sm"
                  className="bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs px-4"
                  onClick={onEditSave}
                >
                  Save
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  className="text-xs text-zinc-500"
                  onClick={onEditCancel}
                >
                  Cancel
                </Button>
              </div>
            </motion.div>
          )}
          {!isEditing && isExpanded && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              className="mb-3"
            >
              <div className="rounded-lg bg-white/[0.02] border border-white/[0.04] p-3.5">
                <p className="text-[13px] text-zinc-400 leading-relaxed whitespace-pre-wrap">{item.body}</p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Action bar */}
        <div className="flex flex-wrap items-center gap-2">
          {activeTab === "review" && (
            <Button
              size="sm"
              className="bg-emerald-500/90 hover:bg-emerald-500 text-black font-semibold text-xs px-4 rounded-lg"
              onClick={onApprove}
            >
              Approve
            </Button>
          )}
          {(activeTab === "scheduled" || activeTab === "draft" || activeTab === "review") && (
            <Button
              size="sm"
              className="bg-blue-500/90 hover:bg-blue-500 text-white font-semibold text-xs px-4 rounded-lg"
              onClick={onPublish}
            >
              Publish to Blog
            </Button>
          )}
          {!isEditing && (
            <Button
              size="sm"
              variant="ghost"
              className="text-xs text-zinc-400 hover:text-white px-3"
              onClick={onEdit}
            >
              Edit
            </Button>
          )}
          {activeTab === "review" && (
            <Button
              size="sm"
              variant="ghost"
              className="text-xs text-red-500 hover:text-red-400 px-3"
              onClick={onReject}
            >
              Reject
            </Button>
          )}
          {!isEditing && (
            <Button
              size="sm"
              variant="ghost"
              className="text-xs text-zinc-500 hover:text-zinc-300 px-3"
              onClick={onToggleExpand}
            >
              {isExpanded ? "Hide" : "View Body"}
            </Button>
          )}
          {item.published_url && (
            <a
              href={item.published_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-[11px] text-blue-400 hover:text-blue-300 hover:underline ml-auto"
            >
              View Published ↗
            </a>
          )}
        </div>
      </div>
    </motion.div>
  );
}

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
  const [genType, setGenType] = useState("seo_article");
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

  const handlePublish = async (item: ContentItem) => {
    const { publishContent } = await import("@/lib/api");
    const res = await publishContent(item.id);
    if (res.status === "published") {
      setItems((prev) => prev.filter((i) => i.id !== item.id));
    } else {
      // Copy body to clipboard as fallback
      try { await navigator.clipboard.writeText(item.body); } catch {}
      alert(res.detail || "Publish failed. Content copied to clipboard.");
    }
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
      if (activeTab === "draft") {
        fetchContent({ status: "draft" }).then(setItems).catch(console.error);
      }
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
            <div className="w-7 h-7 rounded-lg bg-blue-500/10 flex items-center justify-center">
              <ContentIcon />
            </div>
            <h1 className="text-xl font-bold tracking-tight text-white">ContentBot</h1>
          </div>
          <p className="text-sm text-zinc-500 mt-1 ml-9">Review, edit, and publish AI-generated content</p>
        </div>
        <Button
          onClick={() => setShowGenerate((v) => !v)}
          className={`text-xs font-semibold px-4 rounded-lg transition-all ${
            showGenerate
              ? "bg-white/[0.06] hover:bg-white/[0.08] text-zinc-300"
              : "bg-blue-600 hover:bg-blue-500 text-white"
          }`}
        >
          {showGenerate ? "Cancel" : "Generate New"}
        </Button>
      </motion.div>

      {/* Generate form */}
      <AnimatePresence>
        {showGenerate && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="mb-5"
          >
            <div className="rounded-xl border border-blue-500/[0.12] bg-blue-500/[0.04] p-4">
              <p className="text-xs font-semibold text-blue-400 uppercase tracking-wider mb-3">New Content Request</p>
              <div className="flex gap-3 flex-wrap">
                <div className="flex-1 min-w-48">
                  <label className="text-[11px] text-zinc-500 mb-1.5 block font-medium uppercase tracking-wider">SEO Keyword</label>
                  <Input
                    value={genKeyword}
                    onChange={(e) => setGenKeyword(e.target.value)}
                    placeholder="e.g. AI chatbot integration"
                    className="bg-white/[0.04] border-white/[0.08] focus:border-blue-500/40 text-sm"
                  />
                </div>
                <div>
                  <label className="text-[11px] text-zinc-500 mb-1.5 block font-medium uppercase tracking-wider">Content Type</label>
                  <select
                    value={genType}
                    onChange={(e) => setGenType(e.target.value)}
                    className="bg-[#111113] border border-white/[0.08] rounded-lg px-3 py-2 text-sm text-zinc-200 h-10 focus:outline-none focus:border-blue-500/40"
                  >
                    <option value="seo_article">SEO Article</option>
                    <option value="industry_brief">Industry Brief</option>
                    <option value="tutorial">Tutorial</option>
                    <option value="comparison">Comparison</option>
                    <option value="changelog">Changelog</option>
                    <option value="social_post">Social Post</option>
                  </select>
                </div>
                <div>
                  <label className="text-[11px] text-zinc-500 mb-1.5 block font-medium uppercase tracking-wider">Language</label>
                  <select
                    value={genLang}
                    onChange={(e) => setGenLang(e.target.value)}
                    className="bg-[#111113] border border-white/[0.08] rounded-lg px-3 py-2 text-sm text-zinc-200 h-10 focus:outline-none focus:border-blue-500/40"
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
                    className="bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs px-5 h-10 rounded-lg"
                  >
                    {generating ? "Generating..." : "Generate"}
                  </Button>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Tab navigation */}
      <div className="flex gap-1.5 mb-5">
        {TABS.map((tab) => (
          <button
            key={tab.status}
            onClick={() => setActiveTab(tab.status)}
            className={`px-4 py-1.5 rounded-full text-xs font-semibold transition-all ${
              activeTab === tab.status
                ? "bg-blue-600 text-white shadow-lg shadow-blue-900/30"
                : "text-zinc-500 hover:text-zinc-300 bg-white/[0.03] border border-white/[0.06] hover:border-white/[0.10]"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content list */}
      {loading && (
        <div className="text-center py-20">
          <div className="w-6 h-6 border-2 border-blue-500/30 border-t-blue-400 rounded-full animate-spin mx-auto" />
          <p className="text-zinc-500 text-xs mt-3">Loading content...</p>
        </div>
      )}

      {!loading && (
        <div className="space-y-3">
          <AnimatePresence>
            {items.map((item, i) => (
              <ContentCard
                key={item.id}
                item={item}
                index={i}
                activeTab={activeTab}
                isEditing={editingId === item.id}
                isExpanded={expandedId === item.id}
                editTitle={editTitle}
                editBody={editBody}
                setEditTitle={setEditTitle}
                setEditBody={setEditBody}
                onEdit={() => {
                  setEditingId(item.id);
                  setEditTitle(item.title);
                  setEditBody(item.body);
                  setExpandedId(null);
                }}
                onEditSave={() => handleEditSave(item.id)}
                onEditCancel={() => setEditingId(null)}
                onApprove={() => handleApprove(item)}
                onReject={() => handleReject(item.id)}
                onPublish={() => handlePublish(item)}
                onToggleExpand={() =>
                  setExpandedId((prev) => (prev === item.id ? null : item.id))
                }
              />
            ))}
          </AnimatePresence>

          {items.length === 0 && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.2 }}
              className="text-center py-20"
            >
              <div className="w-16 h-16 rounded-2xl bg-blue-500/5 border border-blue-500/10 flex items-center justify-center mx-auto mb-4">
                <ContentIcon />
              </div>
              <p className="text-zinc-500 text-sm">No {activeTab} content items.</p>
              <p className="text-zinc-600 text-xs mt-1">ContentBot is generating new material...</p>
            </motion.div>
          )}
        </div>
      )}
    </div>
  );
}
