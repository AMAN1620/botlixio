"use client";

import { useEffect, useRef, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { agentsApi, knowledgeApi, type AgentResponse, type KnowledgeResponse } from "@/lib/agents-api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL?.replace("/api/v1", "") || "http://localhost:8000";

type Tab = "overview" | "knowledge" | "embed" | "test";

/* ── Overview Tab ── */
function OverviewTab({ agent, onDeploy, onPause }: { agent: AgentResponse; onDeploy: () => void; onPause: () => void }) {
  return (
    <div className="flex flex-col gap-6">
      <div className="grid gap-4 md:grid-cols-3">
        {[
          { label: "Status", value: <span className={`font-bold capitalize ${agent.status === "live" ? "text-green-600" : agent.status === "paused" ? "text-amber-600" : "text-slate-500"}`}>{agent.status}</span> },
          { label: "Total Messages", value: agent.total_messages.toLocaleString() },
          { label: "Total Sessions", value: agent.total_sessions.toLocaleString() },
        ].map((s) => (
          <div key={s.label} className="rounded-2xl border border-slate-200 bg-white p-5">
            <p className="text-sm text-slate-500">{s.label}</p>
            <div className="mt-1 text-2xl font-black text-slate-900">{s.value}</div>
          </div>
        ))}
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-6">
        <h3 className="mb-4 font-bold text-slate-900">Configuration</h3>
        <dl className="grid gap-3 md:grid-cols-2">
          {[
            ["Model", agent.model],
            ["Temperature", agent.temperature],
            ["Max Tokens", agent.max_tokens],
            ["Brand Color", agent.primary_color || "—"],
          ].map(([k, v]) => (
            <div key={k as string}>
              <dt className="text-xs text-slate-400 uppercase tracking-wide">{k}</dt>
              <dd className="mt-0.5 font-medium text-slate-900">{String(v)}</dd>
            </div>
          ))}
        </dl>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-6">
        <h3 className="mb-3 font-bold text-slate-900">System Prompt</h3>
        <p className="text-sm leading-relaxed text-slate-600">{agent.system_prompt}</p>
      </div>

      <div className="flex gap-3">
        {agent.status !== "live" && (
          <button
            onClick={onDeploy}
            className="rounded-xl bg-green-600 px-6 py-3 font-bold text-white hover:bg-green-700"
          >
            Deploy Agent
          </button>
        )}
        {agent.status === "live" && (
          <button
            onClick={onPause}
            className="rounded-xl border border-amber-300 px-6 py-3 font-bold text-amber-700 hover:bg-amber-50"
          >
            Pause Agent
          </button>
        )}
      </div>
    </div>
  );
}

/* ── Knowledge Tab ── */
function KnowledgeTab({ agentId }: { agentId: string }) {
  const [sources, setSources] = useState<KnowledgeResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeForm, setActiveForm] = useState<"url" | "text" | "file" | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [url, setUrl] = useState("");
  const [textTitle, setTextTitle] = useState("");
  const [textContent, setTextContent] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  const load = async () => {
    const { data } = await knowledgeApi.list(agentId);
    setSources(data.data);
    setLoading(false);
  };
  useEffect(() => { load(); }, [agentId]);

  const addUrl = async () => {
    if (!url.trim()) return;
    setSubmitting(true);
    try {
      await knowledgeApi.addUrl(agentId, url.trim());
      setUrl("");
      setActiveForm(null);
      await load();
    } catch { alert("Failed to crawl URL. Make sure it's publicly accessible."); }
    finally { setSubmitting(false); }
  };

  const addText = async () => {
    if (!textTitle.trim() || !textContent.trim()) return;
    setSubmitting(true);
    try {
      await knowledgeApi.addText(agentId, textTitle.trim(), textContent.trim());
      setTextTitle(""); setTextContent("");
      setActiveForm(null);
      await load();
    } catch { alert("Failed to add text."); }
    finally { setSubmitting(false); }
  };

  const uploadFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setSubmitting(true);
    try {
      await knowledgeApi.upload(agentId, file);
      setActiveForm(null);
      await load();
    } catch { alert("Failed to upload file."); }
    finally { setSubmitting(false); if (fileRef.current) fileRef.current.value = ""; }
  };

  const remove = async (sourceId: string) => {
    if (!confirm("Remove this knowledge source?")) return;
    await knowledgeApi.delete(agentId, sourceId);
    setSources((s) => s.filter((x) => x.id !== sourceId));
  };

  const sourceIcon = (t: string) => t === "url" ? "🌐" : t === "file" ? "📄" : "📝";

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap gap-3">
        {(["url", "text", "file"] as const).map((f) => (
          <button
            key={f}
            onClick={() => setActiveForm(activeForm === f ? null : f)}
            className={`rounded-xl px-5 py-2.5 text-sm font-bold ${activeForm === f ? "bg-brand text-white" : "border border-slate-200 bg-white text-slate-700 hover:bg-slate-50"}`}
          >
            {f === "url" ? "+ Add URL" : f === "text" ? "+ Add Text" : "+ Upload File"}
          </button>
        ))}
      </div>

      {activeForm === "url" && (
        <div className="rounded-2xl border border-slate-200 bg-white p-5">
          <p className="mb-3 text-sm font-semibold text-slate-700">Website URL</p>
          <p className="mb-3 text-xs text-slate-400">We&apos;ll crawl this page and extract content automatically</p>
          <div className="flex gap-3">
            <input
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://example.com/about"
              className="flex-1 rounded-xl border border-slate-200 px-4 py-2.5 text-sm outline-none focus:border-brand"
            />
            <button
              onClick={addUrl}
              disabled={submitting}
              className="rounded-xl bg-brand px-5 py-2.5 text-sm font-bold text-white disabled:opacity-50"
            >
              {submitting ? "Crawling…" : "Crawl"}
            </button>
          </div>
        </div>
      )}

      {activeForm === "text" && (
        <div className="rounded-2xl border border-slate-200 bg-white p-5">
          <p className="mb-3 text-sm font-semibold text-slate-700">Raw Text</p>
          <div className="flex flex-col gap-3">
            <input
              value={textTitle}
              onChange={(e) => setTextTitle(e.target.value)}
              placeholder="Title (e.g. FAQ, Return Policy)"
              className="rounded-xl border border-slate-200 px-4 py-2.5 text-sm outline-none focus:border-brand"
            />
            <textarea
              value={textContent}
              onChange={(e) => setTextContent(e.target.value)}
              rows={6}
              placeholder="Paste your text content here…"
              className="rounded-xl border border-slate-200 px-4 py-2.5 text-sm outline-none focus:border-brand"
            />
            <button
              onClick={addText}
              disabled={submitting}
              className="self-end rounded-xl bg-brand px-5 py-2.5 text-sm font-bold text-white disabled:opacity-50"
            >
              {submitting ? "Saving…" : "Add Text"}
            </button>
          </div>
        </div>
      )}

      {activeForm === "file" && (
        <div className="rounded-2xl border border-slate-200 bg-white p-5">
          <p className="mb-2 text-sm font-semibold text-slate-700">Upload Document</p>
          <p className="mb-3 text-xs text-slate-400">Supported: PDF, DOCX, TXT, CSV — max 10 MB</p>
          <input
            ref={fileRef}
            type="file"
            accept=".pdf,.docx,.txt,.csv"
            onChange={uploadFile}
            disabled={submitting}
            className="text-sm"
          />
          {submitting && <p className="mt-2 text-sm text-slate-500">Uploading and processing…</p>}
        </div>
      )}

      {loading ? (
        <p className="text-center text-slate-400">Loading…</p>
      ) : sources.length === 0 ? (
        <div className="rounded-2xl border-2 border-dashed border-slate-200 py-16 text-center">
          <p className="font-bold text-slate-400">No knowledge sources yet</p>
          <p className="mt-1 text-sm text-slate-400">Add URLs, text, or files to train your bot</p>
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          {sources.map((s) => (
            <div key={s.id} className="flex items-center justify-between rounded-2xl border border-slate-200 bg-white p-4">
              <div className="flex items-center gap-3">
                <span className="text-2xl">{sourceIcon(s.source_type)}</span>
                <div>
                  <p className="font-medium text-slate-900 line-clamp-1">{s.title}</p>
                  <p className="text-xs text-slate-400">
                    {s.chunk_count} chunks · {s.char_count.toLocaleString()} chars
                  </p>
                </div>
              </div>
              <button
                onClick={() => remove(s.id)}
                className="rounded-lg border border-red-200 px-3 py-1.5 text-xs font-medium text-red-600 hover:bg-red-50"
              >
                Remove
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

/* ── Embed Tab ── */
function EmbedTab({ agentId }: { agentId: string }) {
  const [snippet, setSnippet] = useState("");
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    agentsApi.embedCode(agentId).then(({ data }) => setSnippet(data.snippet));
  }, [agentId]);

  const copy = () => {
    navigator.clipboard.writeText(snippet);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="flex flex-col gap-6">
      <div className="rounded-2xl border border-slate-200 bg-white p-6">
        <h3 className="mb-2 font-bold text-slate-900">Embed on your website</h3>
        <p className="mb-5 text-sm text-slate-500">
          Copy and paste this snippet just before the closing <code className="rounded bg-slate-100 px-1">&lt;/body&gt;</code> tag of your website.
        </p>
        <pre className="overflow-x-auto rounded-xl bg-slate-900 p-4 text-sm text-slate-100 leading-relaxed">
          {snippet || "Loading…"}
        </pre>
        <button
          onClick={copy}
          className={`mt-4 rounded-xl px-6 py-3 font-bold ${copied ? "bg-green-600 text-white" : "bg-brand text-white hover:bg-brand/90"}`}
        >
          {copied ? "✓ Copied!" : "Copy Snippet"}
        </button>
      </div>

      <div className="rounded-2xl border border-amber-100 bg-amber-50 p-5">
        <p className="text-sm font-semibold text-amber-800">⚠ Deploy your agent first</p>
        <p className="mt-1 text-sm text-amber-700">
          The widget only appears on live agents. Deploy the agent from the Overview tab before testing on your site.
        </p>
      </div>
    </div>
  );
}

/* ── Test Chat Tab ── */
function TestChatTab({ agentId }: { agentId: string }) {
  const [messages, setMessages] = useState<{ role: string; content: string; sources?: string[] }[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = async () => {
    const text = input.trim();
    if (!text || loading) return;
    setInput("");
    setMessages((m) => [...m, { role: "user", content: text }]);
    setLoading(true);

    try {
      const resp = await fetch(`${API_BASE}/api/v1/widget/${agentId}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, session_id: sessionId }),
      });
      const data = await resp.json();
      if (data.session_id) setSessionId(data.session_id);
      setMessages((m) => [...m, { role: "assistant", content: data.reply || "Error", sources: data.sources || [] }]);
    } catch {
      setMessages((m) => [...m, { role: "assistant", content: "Connection error." }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col gap-4">
      <div className="rounded-2xl border border-slate-200 bg-white p-4">
        <p className="mb-3 text-sm font-semibold text-slate-700">Test Chat</p>
        <p className="text-xs text-slate-400 mb-4">This simulates what visitors will see. Agent must be live to respond with AI answers.</p>

        <div className="flex flex-col gap-3 min-h-[240px] max-h-[360px] overflow-y-auto mb-4">
          {messages.length === 0 && (
            <p className="text-center text-sm text-slate-300 mt-10">Send a message to test your bot</p>
          )}
          {messages.map((m, i) => (
            <div key={i} className={`flex flex-col ${m.role === "user" ? "items-end" : "items-start"}`}>
              <div
                className={`max-w-[75%] rounded-2xl px-4 py-2.5 text-sm ${
                  m.role === "user"
                    ? "bg-brand text-white rounded-br-sm"
                    : "bg-slate-100 text-slate-900 rounded-bl-sm"
                }`}
              >
                {m.content}
              </div>
              {m.role === "assistant" && m.sources && m.sources.length > 0 && (
                <div className="mt-1 flex flex-wrap gap-1 max-w-[75%]">
                  {m.sources.map((src, si) => (
                    <span key={si} className="inline-flex items-center gap-1 rounded-full border border-slate-200 bg-white px-2 py-0.5 text-xs text-slate-500">
                      <svg className="size-3 shrink-0" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M13.19 8.688a4.5 4.5 0 0 1 1.242 7.244l-4.5 4.5a4.5 4.5 0 0 1-6.364-6.364l1.757-1.757m13.35-.622 1.757-1.757a4.5 4.5 0 0 0-6.364-6.364l-4.5 4.5a4.5 4.5 0 0 0 1.242 7.244" />
                      </svg>
                      <span className="truncate max-w-[200px]">{src}</span>
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
          {loading && (
            <div className="flex justify-start">
              <div className="rounded-2xl rounded-bl-sm bg-slate-100 px-4 py-2.5 text-sm text-slate-400">
                Typing…
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="flex gap-2 border-t border-slate-100 pt-3">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && send()}
            placeholder="Type a test message…"
            className="flex-1 rounded-xl border border-slate-200 px-4 py-2.5 text-sm outline-none focus:border-brand"
          />
          <button
            onClick={send}
            disabled={loading}
            className="rounded-xl bg-brand px-5 py-2.5 text-sm font-bold text-white disabled:opacity-50"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}

/* ── Main Page ── */
export default function AgentDetailPage() {
  const params = useParams();
  const agentId = params.id as string;
  const [agent, setAgent] = useState<AgentResponse | null>(null);
  const [tab, setTab] = useState<Tab>("overview");

  useEffect(() => {
    agentsApi.get(agentId).then(({ data }) => setAgent(data));
  }, [agentId]);

  const deploy = async () => {
    try {
      const { data } = await agentsApi.deploy(agentId);
      setAgent(data);
    } catch (e) {
      alert("Deploy failed: " + (e as Error).message);
    }
  };
  const pause = async () => {
    try {
      const { data } = await agentsApi.pause(agentId);
      setAgent(data);
    } catch (e) {
      alert("Pause failed: " + (e as Error).message);
    }
  };

  if (!agent) {
    return (
      <div className="flex h-64 items-center justify-center text-slate-400">Loading…</div>
    );
  }

  const tabs: { id: Tab; label: string }[] = [
    { id: "overview", label: "Overview" },
    { id: "knowledge", label: "Knowledge" },
    { id: "embed", label: "Embed Code" },
    { id: "test", label: "Test Chat" },
  ];

  return (
    <div>
      <div className="mb-6">
        <Link href="/agents" className="text-sm text-slate-500 hover:text-brand">
          ← Agents
        </Link>
        <div className="mt-4 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-black tracking-tight text-slate-900">{agent.name}</h1>
            {agent.description && (
              <p className="mt-1 text-slate-500">{agent.description}</p>
            )}
          </div>
          <span
            className={`rounded-full px-3 py-1 text-sm font-semibold capitalize ${
              agent.status === "live"
                ? "bg-green-100 text-green-700"
                : agent.status === "paused"
                ? "bg-amber-100 text-amber-700"
                : "bg-slate-100 text-slate-600"
            }`}
          >
            {agent.status}
          </span>
        </div>
      </div>

      <div className="mb-6 flex gap-1 border-b border-slate-200">
        {tabs.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`px-5 py-2.5 text-sm font-semibold ${
              tab === t.id
                ? "border-b-2 border-brand text-brand"
                : "text-slate-500 hover:text-slate-900"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === "overview" && <OverviewTab agent={agent} onDeploy={deploy} onPause={pause} />}
      {tab === "knowledge" && <KnowledgeTab agentId={agentId} />}
      {tab === "embed" && <EmbedTab agentId={agentId} />}
      {tab === "test" && <TestChatTab agentId={agentId} />}
    </div>
  );
}
