"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  VideoItem,
  fetchVideos,
  generateVideo,
  generatePromo,
  uploadToYouTube,
  getVideoStreamUrl,
} from "@/lib/api";

function VideoIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#ef4444" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polygon points="23 7 16 12 23 17 23 7" />
      <rect x="1" y="5" width="15" height="14" rx="2" ry="2" />
    </svg>
  );
}

const TYPE_COLORS: Record<string, { bg: string; text: string }> = {
  short: { bg: "bg-amber-500/10 border-amber-500/20", text: "text-amber-400" },
  tutorial: { bg: "bg-blue-500/10 border-blue-500/20", text: "text-blue-400" },
  promo: { bg: "bg-purple-500/10 border-purple-500/20", text: "text-purple-400" },
};

export default function VideoPage() {
  const [videos, setVideos] = useState<VideoItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [showGenerate, setShowGenerate] = useState(false);
  const [topic, setTopic] = useState("");
  const [videoType, setVideoType] = useState("tip");
  const [language, setLanguage] = useState("en");
  const [generating, setGenerating] = useState(false);
  const [uploadingId, setUploadingId] = useState<string | null>(null);
  const [playingId, setPlayingId] = useState<string | null>(null);
  const [uploadTitle, setUploadTitle] = useState("");
  const [uploadDesc, setUploadDesc] = useState("");
  const [toast, setToast] = useState<{ msg: string; type: "ok" | "info" | "error" } | null>(null);

  const showToast = (msg: string, type: "ok" | "info" | "error" = "ok") => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 5000);
  };

  useEffect(() => {
    fetchVideos()
      .then(setVideos)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const handleGenerate = async () => {
    if (!topic.trim()) return;
    setGenerating(true);
    try {
      await generateVideo({ topic, video_type: videoType, language });
      showToast("Video generation queued. Refresh in ~60s.", "info");
      setShowGenerate(false);
      setTopic("");
    } catch {
      showToast("Generation failed", "error");
    } finally {
      setGenerating(false);
    }
  };

  const handleGeneratePromo = async () => {
    setGenerating(true);
    try {
      await generatePromo();
      showToast("Promo video generation queued. Refresh in ~90s.", "info");
    } catch {
      showToast("Generation failed", "error");
    } finally {
      setGenerating(false);
    }
  };

  const handleUpload = async (video: VideoItem) => {
    if (!uploadTitle.trim()) return;
    try {
      const res = await uploadToYouTube({
        video_path: video.path,
        title: uploadTitle,
        description: uploadDesc || `SoxAI - ${uploadTitle}\n\nhttps://www.soxai.io`,
      });
      if (res.url) {
        showToast(`Uploaded: ${res.url}`);
        window.open(res.url, "_blank");
      } else {
        showToast(res.detail || "Upload failed", "error");
      }
    } catch {
      showToast("Upload failed", "error");
    }
    setUploadingId(null);
  };

  const refreshList = () => {
    setLoading(true);
    fetchVideos().then(setVideos).catch(console.error).finally(() => setLoading(false));
  };

  return (
    <div className="p-8 max-w-[1200px] mx-auto">
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-red-500/10 flex items-center justify-center">
              <VideoIcon />
            </div>
            <h1 className="text-xl font-bold tracking-tight text-white">Video Pipeline</h1>
          </div>
          <div className="flex gap-2">
            <Button variant="ghost" className="text-xs text-zinc-400" onClick={refreshList}>Refresh</Button>
            <Button
              className="bg-purple-500/90 hover:bg-purple-500 text-white font-semibold text-xs px-4"
              onClick={handleGeneratePromo}
              disabled={generating}
            >
              {generating ? "Queued..." : "Generate Promo"}
            </Button>
            <Button
              className="bg-red-500/90 hover:bg-red-500 text-white font-semibold text-xs px-4"
              onClick={() => setShowGenerate((v) => !v)}
            >
              {showGenerate ? "Cancel" : "Generate Short"}
            </Button>
          </div>
        </div>
        <p className="text-sm text-zinc-500 mt-1 ml-9">Generate, preview, and upload videos to YouTube</p>
      </motion.div>

      {/* Generate form */}
      <AnimatePresence>
        {showGenerate && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="mb-6 overflow-hidden"
          >
            <div className="rounded-xl border border-red-500/10 bg-[#111113] p-5">
              <div className="flex gap-3 flex-wrap items-end">
                <div className="flex-1 min-w-[250px]">
                  <label className="text-[11px] text-zinc-500 mb-1 block uppercase tracking-wider font-medium">Topic</label>
                  <Input
                    value={topic}
                    onChange={(e) => setTopic(e.target.value)}
                    placeholder="e.g. AI API pricing comparison 2026"
                    className="bg-white/[0.03] border-white/[0.08] text-[13px]"
                  />
                </div>
                <div>
                  <label className="text-[11px] text-zinc-500 mb-1 block uppercase tracking-wider font-medium">Type</label>
                  <select
                    value={videoType}
                    onChange={(e) => setVideoType(e.target.value)}
                    className="bg-white/[0.03] border border-white/[0.08] rounded-lg px-3 py-2 text-[13px] text-zinc-100 h-9"
                  >
                    <option value="tip">Quick Tip</option>
                    <option value="code_demo">Code Demo</option>
                    <option value="news">News</option>
                    <option value="comparison">Comparison</option>
                    <option value="tutorial">Tutorial</option>
                  </select>
                </div>
                <div>
                  <label className="text-[11px] text-zinc-500 mb-1 block uppercase tracking-wider font-medium">Language</label>
                  <select
                    value={language}
                    onChange={(e) => setLanguage(e.target.value)}
                    className="bg-white/[0.03] border border-white/[0.08] rounded-lg px-3 py-2 text-[13px] text-zinc-100 h-9"
                  >
                    <option value="en">English</option>
                    <option value="zh">Chinese</option>
                  </select>
                </div>
                <Button
                  className="bg-red-500/90 hover:bg-red-500 text-white font-semibold text-xs px-6 h-9"
                  onClick={handleGenerate}
                  disabled={generating || !topic.trim()}
                >
                  {generating ? "Queued..." : "Generate"}
                </Button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Video list */}
      {loading && (
        <div className="text-center py-20">
          <div className="w-6 h-6 border-2 border-red-500/30 border-t-red-400 rounded-full animate-spin mx-auto" />
          <p className="text-zinc-500 text-xs mt-3">Loading videos...</p>
        </div>
      )}

      {!loading && (
        <div className="space-y-3">
          <AnimatePresence>
            {videos.map((video, i) => {
              const typeStyle = TYPE_COLORS[video.type] ?? TYPE_COLORS.short;
              const isUploading = uploadingId === video.id;
              const date = new Date(video.created_at * 1000);

              return (
                <motion.div
                  key={video.id}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.05 }}
                  className="card-hover rounded-xl border border-white/[0.06] bg-[#111113] overflow-hidden"
                >
                  <div className="p-5">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-lg bg-red-500/10 flex items-center justify-center">
                          <VideoIcon />
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-semibold text-white">{video.filename}</span>
                            <span className={`text-[10px] px-2 py-0.5 rounded-full border font-semibold uppercase tracking-wider ${typeStyle.bg} ${typeStyle.text}`}>
                              {video.type}
                            </span>
                          </div>
                          <p className="text-[11px] text-zinc-600">
                            {video.id} &middot; {video.size_kb} KB &middot; {date.toLocaleString()}
                          </p>
                        </div>
                      </div>
                      <div className="flex gap-2">
                        {!isUploading && (
                          <>
                            <Button
                              size="sm"
                              variant="ghost"
                              className="text-xs text-zinc-400 hover:text-white px-3"
                              onClick={() => setPlayingId(playingId === video.id ? null : video.id)}
                            >
                              {playingId === video.id ? "Close" : "▶ Play"}
                            </Button>
                            <Button
                              size="sm"
                              className="bg-red-500/80 hover:bg-red-500 text-white font-semibold text-xs px-4"
                              onClick={() => {
                                setUploadingId(video.id);
                                setUploadTitle(`SoxAI — ${video.type === "promo" ? "Product Overview" : "Quick Tip"}`);
                                setUploadDesc(`Try free: https://console.soxai.io/register\nDocs: https://docs.soxai.io`);
                              }}
                            >
                              Upload to YouTube
                            </Button>
                          </>
                        )}
                      </div>
                    </div>

                    {/* Video player */}
                    <AnimatePresence>
                      {playingId === video.id && (
                        <motion.div
                          initial={{ opacity: 0, height: 0 }}
                          animate={{ opacity: 1, height: "auto" }}
                          exit={{ opacity: 0, height: 0 }}
                          className="mb-3 flex justify-center"
                        >
                          <div className={`rounded-lg overflow-hidden border border-white/[0.06] ${video.type === "promo" ? "w-full max-w-[640px]" : "w-[240px]"}`}>
                            <video
                              src={getVideoStreamUrl(video.id)}
                              controls
                              autoPlay
                              className="w-full"
                              style={{ maxHeight: video.type === "promo" ? "360px" : "426px" }}
                            />
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>

                    {/* Upload form */}
                    <AnimatePresence>
                      {isUploading && (
                        <motion.div
                          initial={{ opacity: 0, height: 0 }}
                          animate={{ opacity: 1, height: "auto" }}
                          exit={{ opacity: 0, height: 0 }}
                          className="space-y-3 mt-3 pt-3 border-t border-white/[0.06]"
                        >
                          <div>
                            <label className="text-[11px] text-zinc-500 mb-1 block">Title</label>
                            <Input
                              value={uploadTitle}
                              onChange={(e) => setUploadTitle(e.target.value)}
                              className="bg-white/[0.03] border-white/[0.08] text-[13px]"
                            />
                          </div>
                          <div>
                            <label className="text-[11px] text-zinc-500 mb-1 block">Description</label>
                            <Textarea
                              value={uploadDesc}
                              onChange={(e) => setUploadDesc(e.target.value)}
                              rows={3}
                              className="bg-white/[0.03] border-white/[0.08] text-[13px]"
                            />
                          </div>
                          <div className="flex gap-2">
                            <Button
                              size="sm"
                              className="bg-red-500/90 hover:bg-red-500 text-white font-semibold text-xs px-4"
                              onClick={() => handleUpload(video)}
                            >
                              Upload
                            </Button>
                            <Button size="sm" variant="ghost" className="text-xs text-zinc-500" onClick={() => setUploadingId(null)}>
                              Cancel
                            </Button>
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                </motion.div>
              );
            })}
          </AnimatePresence>

          {videos.length === 0 && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-center py-20">
              <div className="w-16 h-16 rounded-2xl bg-red-500/5 border border-red-500/10 flex items-center justify-center mx-auto mb-4">
                <VideoIcon />
              </div>
              <p className="text-zinc-500 text-sm">No videos yet</p>
              <p className="text-zinc-600 text-xs mt-1">Generate your first video above</p>
            </motion.div>
          )}
        </div>
      )}

      {/* Toast */}
      <AnimatePresence>
        {toast && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            className={`fixed bottom-6 right-6 px-4 py-2.5 rounded-lg text-sm font-medium shadow-lg ${
              toast.type === "ok" ? "bg-emerald-500/90 text-white"
                : toast.type === "info" ? "bg-amber-500/90 text-black"
                : "bg-red-500/90 text-white"
            }`}
          >
            {toast.msg}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
