"use client";

import { useRef, useState } from "react";
import { knowledgeApi, KnowledgeResponse, IndexingStatus, CrawledPage } from "@/lib/agents-api";
import { useKnowledgeStatus } from "./hooks/useKnowledgeStatus";

// ─── Status badge ─────────────────────────────────────────────────────────────

function StatusBadge({ status }: { status: IndexingStatus }) {
  const map: Record<IndexingStatus, { label: string; className: string }> = {
    pending:    { label: "Pending",    className: "bg-slate-100 text-slate-500" },
    processing: { label: "Crawling…",  className: "bg-yellow-50 text-yellow-700 animate-pulse" },
    indexed:    { label: "Indexed",    className: "bg-green-50 text-green-700" },
    failed:     { label: "Failed",     className: "bg-red-50 text-red-700" },
    stale:      { label: "Stale",      className: "bg-orange-50 text-orange-600" },
  };
  const { label, className } = map[status] ?? map.pending;
  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${className}`}>
      {status === "processing" && (
        <span className="inline-block w-2 h-2 rounded-full bg-yellow-500 mr-1 animate-pulse" />
      )}
      {label}
    </span>
  );
}

// ─── Single source card (with live status polling) ────────────────────────────

function SourceCard({
  agentId,
  source,
  onDelete,
}: {
  agentId: string;
  source: KnowledgeResponse;
  onDelete: (id: string) => void;
}) {
  const { status, data } = useKnowledgeStatus(agentId, source.id, source.indexing_status);
  const crawledPages = data?.crawled_pages ?? source.crawled_pages ?? [];
  const [showPages, setShowPages] = useState(false);
  const [removingUrl, setRemovingUrl] = useState<string | null>(null);
  const [addPageUrl, setAddPageUrl] = useState("");
  const [showAddPage, setShowAddPage] = useState(false);

  const typeIcon: Record<string, string> = { url: "🌐", file: "📄", text: "✏️" };

  async function handleRemovePage(url: string) {
    setRemovingUrl(url);
    try {
      await knowledgeApi.removePage(agentId, source.id, url);
    } finally {
      setRemovingUrl(null);
    }
  }

  async function handleAddPage() {
    if (!addPageUrl.trim()) return;
    await knowledgeApi.addPage(agentId, source.id, addPageUrl.trim());
    setAddPageUrl("");
    setShowAddPage(false);
  }

  return (
    <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
      <div className="flex items-center gap-3 px-4 py-3">
        <span className="text-lg">{typeIcon[source.source_type] ?? "📁"}</span>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-slate-800 truncate">{source.title}</p>
          <p className="text-xs text-slate-400 mt-0.5">
            {source.source_type === "file" && source.file_size
              ? `${(source.file_size / 1024).toFixed(0)} KB`
              : source.source_type === "url" && source.max_pages
              ? `Up to ${source.max_pages} pages`
              : "Text snippet"}
          </p>
        </div>
        <StatusBadge status={status} />
        {status === "indexed" && source.source_type === "url" && crawledPages.length > 0 && (
          <button
            onClick={() => setShowPages((p) => !p)}
            className="text-xs text-brand font-medium hover:underline ml-1"
          >
            {showPages ? "Hide pages" : `${crawledPages.length} pages`}
          </button>
        )}
        <button
          onClick={() => onDelete(source.id)}
          className="p-1.5 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors ml-1"
          title="Delete source"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
        </button>
      </div>

      {/* Error message */}
      {status === "failed" && data?.error_message && (
        <div className="px-4 pb-3 text-xs text-red-600 bg-red-50 border-t border-red-100 py-2">
          {data.error_message}
        </div>
      )}

      {/* Crawled pages list */}
      {showPages && crawledPages.length > 0 && (
        <div className="border-t border-slate-100 px-4 py-3 space-y-1.5 bg-slate-50">
          {crawledPages.map((page: CrawledPage) => (
            <div key={page.url} className="flex items-center gap-2 text-xs">
              <span className="flex-1 text-slate-600 truncate">{page.title}</span>
              <span className="text-slate-400 flex-shrink-0">
                {(page.char_count / 1000).toFixed(1)}k chars
              </span>
              <button
                onClick={() => handleRemovePage(page.url)}
                disabled={removingUrl === page.url}
                className="text-slate-400 hover:text-red-500 flex-shrink-0 disabled:opacity-50"
                title="Remove this page"
              >
                ✕
              </button>
            </div>
          ))}

          {/* Add missing page */}
          {showAddPage ? (
            <div className="flex gap-2 pt-1">
              <input
                type="text"
                value={addPageUrl}
                onChange={(e) => setAddPageUrl(e.target.value)}
                placeholder="https://example.com/missing-page"
                className="flex-1 text-xs px-2 py-1.5 border border-slate-200 rounded focus:outline-none focus:border-brand"
              />
              <button
                onClick={handleAddPage}
                className="px-3 py-1.5 text-xs font-medium text-white bg-brand rounded"
              >
                Add
              </button>
              <button
                onClick={() => setShowAddPage(false)}
                className="px-2 py-1.5 text-xs text-slate-500"
              >
                Cancel
              </button>
            </div>
          ) : (
            <button
              onClick={() => setShowAddPage(true)}
              className="text-xs text-brand font-medium hover:underline pt-1"
            >
              + Add missing page
            </button>
          )}
        </div>
      )}
    </div>
  );
}

// ─── URL tab ──────────────────────────────────────────────────────────────────

function UrlTab({
  agentId,
  onAdded,
}: {
  agentId: string;
  onAdded: (source: KnowledgeResponse) => void;
}) {
  const [rootUrl, setRootUrl] = useState("");
  const [pathFilter, setPathFilter] = useState("");
  const [maxPages, setMaxPages] = useState(10);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleCrawl() {
    if (!rootUrl.trim()) return;
    setError(null);
    setLoading(true);
    try {
      const res = await knowledgeApi.addUrl(agentId, {
        root_url: rootUrl.trim(),
        path_filter: pathFilter.trim() || undefined,
        max_pages: maxPages,
      });
      onAdded(res.data);
      setRootUrl("");
      setPathFilter("");
      setMaxPages(10);
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      setError(e?.response?.data?.detail ?? "Failed to start crawl. Check the URL and try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-slate-700 mb-1.5">Website URL</label>
        <input
          type="url"
          value={rootUrl}
          onChange={(e) => setRootUrl(e.target.value)}
          placeholder="https://example.com"
          className="w-full px-3 py-2.5 text-sm border border-slate-200 rounded-lg focus:outline-none focus:border-brand focus:ring-2 focus:ring-brand/10"
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1.5">
            Path filter{" "}
            <span className="font-normal text-slate-400">(optional)</span>
          </label>
          <input
            type="text"
            value={pathFilter}
            onChange={(e) => setPathFilter(e.target.value)}
            placeholder="/docs"
            className="w-full px-3 py-2.5 text-sm border border-slate-200 rounded-lg focus:outline-none focus:border-brand focus:ring-2 focus:ring-brand/10"
          />
          <p className="text-xs text-slate-400 mt-1">Only crawl pages under this path.</p>
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1.5">
            Max pages{" "}
            <span className="font-normal text-slate-400">(1–20)</span>
          </label>
          <input
            type="number"
            min={1}
            max={20}
            value={maxPages}
            onChange={(e) => setMaxPages(Math.min(20, Math.max(1, Number(e.target.value))))}
            className="w-full px-3 py-2.5 text-sm border border-slate-200 rounded-lg focus:outline-none focus:border-brand focus:ring-2 focus:ring-brand/10"
          />
        </div>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <button
        onClick={handleCrawl}
        disabled={loading || !rootUrl.trim()}
        className="w-full py-2.5 text-sm font-semibold text-white bg-brand rounded-lg hover:bg-brand/90 disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2"
      >
        {loading ? (
          <>
            <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
            </svg>
            Starting crawl…
          </>
        ) : (
          "Start Crawling →"
        )}
      </button>

      <p className="text-xs text-slate-400 text-center">
        Returns immediately — crawl happens in the background. Review pages once indexed.
      </p>
    </div>
  );
}

// ─── File tab ─────────────────────────────────────────────────────────────────

function FileTab({
  agentId,
  onAdded,
}: {
  agentId: string;
  onAdded: (source: KnowledgeResponse) => void;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleFiles(files: FileList | null) {
    if (!files || files.length === 0) return;
    setError(null);
    setUploading(true);
    try {
      for (const file of Array.from(files)) {
        const res = await knowledgeApi.upload(agentId, file);
        onAdded(res.data);
      }
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      setError(e?.response?.data?.detail ?? "Upload failed.");
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="space-y-4">
      <div
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => { e.preventDefault(); setDragging(false); handleFiles(e.dataTransfer.files); }}
        onClick={() => inputRef.current?.click()}
        className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-colors ${
          dragging ? "border-brand bg-brand-light" : "border-slate-200 hover:border-slate-300 hover:bg-slate-50"
        }`}
      >
        <input
          ref={inputRef}
          type="file"
          multiple
          accept=".pdf,.txt,.docx,.csv"
          className="hidden"
          onChange={(e) => handleFiles(e.target.files)}
        />
        <div className="text-3xl mb-3">📁</div>
        <p className="text-sm font-medium text-slate-700">
          {uploading ? "Uploading…" : "Drop files here or click to browse"}
        </p>
        <p className="text-xs text-slate-400 mt-1.5">
          Supports PDF, TXT, DOCX, CSV — max 10 MB per file
        </p>
      </div>
      {error && <p className="text-sm text-red-600">{error}</p>}
    </div>
  );
}

// ─── Text tab ─────────────────────────────────────────────────────────────────

function TextTab({
  agentId,
  onAdded,
}: {
  agentId: string;
  onAdded: (source: KnowledgeResponse) => void;
}) {
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleAdd() {
    if (!title.trim() || !content.trim()) return;
    setError(null);
    setLoading(true);
    try {
      const res = await knowledgeApi.addText(agentId, title.trim(), content.trim());
      onAdded(res.data);
      setTitle("");
      setContent("");
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      setError(e?.response?.data?.detail ?? "Failed to add text.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-slate-700 mb-1.5">Title</label>
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="e.g. FAQ Answers, Pricing Info"
          className="w-full px-3 py-2.5 text-sm border border-slate-200 rounded-lg focus:outline-none focus:border-brand focus:ring-2 focus:ring-brand/10"
        />
      </div>
      <div>
        <label className="block text-sm font-medium text-slate-700 mb-1.5">Content</label>
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          rows={8}
          placeholder="Paste your text content here…"
          className="w-full px-3 py-2.5 text-sm border border-slate-200 rounded-lg focus:outline-none focus:border-brand focus:ring-2 focus:ring-brand/10 resize-none"
        />
        <p className="text-xs text-slate-400 mt-1">{content.length.toLocaleString()} / 100,000 characters</p>
      </div>
      {error && <p className="text-sm text-red-600">{error}</p>}
      <button
        onClick={handleAdd}
        disabled={loading || !title.trim() || !content.trim()}
        className="w-full py-2.5 text-sm font-semibold text-white bg-brand rounded-lg hover:bg-brand/90 disabled:opacity-60 disabled:cursor-not-allowed"
      >
        {loading ? "Adding…" : "Add Text →"}
      </button>
    </div>
  );
}

// ─── Main Step2 component ─────────────────────────────────────────────────────

type KnowledgeTab = "url" | "file" | "text";

interface Step2KnowledgeProps {
  agentId: string;
  sources: KnowledgeResponse[];
  onSourceAdded: (source: KnowledgeResponse) => void;
  onSourceDeleted: (id: string) => void;
}

export default function Step2Knowledge({
  agentId,
  sources,
  onSourceAdded,
  onSourceDeleted,
}: Step2KnowledgeProps) {
  const [activeTab, setActiveTab] = useState<KnowledgeTab>("url");

  const TABS: { key: KnowledgeTab; label: string; icon: string }[] = [
    { key: "url",  label: "Website URL",  icon: "🌐" },
    { key: "file", label: "Upload Files", icon: "📄" },
    { key: "text", label: "Paste Text",   icon: "✏️" },
  ];

  async function handleDelete(id: string) {
    try {
      await knowledgeApi.delete(agentId, id);
      onSourceDeleted(id);
    } catch {
      // ignore
    }
  }

  const pendingCount = sources.filter(
    (s) => s.indexing_status === "pending" || s.indexing_status === "processing"
  ).length;

  return (
    <div className="space-y-6">
      {/* Add source card */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        {/* Tabs */}
        <div className="flex border-b border-slate-200">
          {TABS.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`flex-1 flex items-center justify-center gap-2 py-3 text-sm font-medium transition-colors ${
                activeTab === tab.key
                  ? "text-brand border-b-2 border-brand bg-brand-light"
                  : "text-slate-500 hover:text-slate-700 hover:bg-slate-50"
              }`}
            >
              <span>{tab.icon}</span>
              <span>{tab.label}</span>
            </button>
          ))}
        </div>

        <div className="p-6">
          {activeTab === "url"  && <UrlTab  agentId={agentId} onAdded={onSourceAdded} />}
          {activeTab === "file" && <FileTab agentId={agentId} onAdded={onSourceAdded} />}
          {activeTab === "text" && <TextTab agentId={agentId} onAdded={onSourceAdded} />}
        </div>
      </div>

      {/* Source list */}
      {sources.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-slate-700">
              Knowledge Sources ({sources.length})
            </h3>
            {pendingCount > 0 && (
              <span className="text-xs text-yellow-700 bg-yellow-50 px-2 py-1 rounded-full font-medium">
                {pendingCount} indexing…
              </span>
            )}
          </div>
          <div className="space-y-2">
            {sources.map((source) => (
              <SourceCard
                key={source.id}
                agentId={agentId}
                source={source}
                onDelete={handleDelete}
              />
            ))}
          </div>
        </div>
      )}

      {sources.length === 0 && (
        <div className="text-center py-8 text-slate-400">
          <div className="text-4xl mb-3">📭</div>
          <p className="text-sm">No knowledge sources yet.</p>
          <p className="text-xs mt-1">Add a website, upload a file, or paste text above.</p>
        </div>
      )}
    </div>
  );
}
