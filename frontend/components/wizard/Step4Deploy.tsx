"use client";

import { useState } from "react";
import { IndexingStatus, KnowledgeResponse } from "@/lib/agents-api";
import WhatsAppConnect from "@/components/WhatsAppConnect";

interface Step4DeployProps {
  agentId: string;
  agentName: string;
  userId: string;
  embedSnippet: string;
  knowledgeSources: KnowledgeResponse[];
  onDeploy: () => void;
  isDeploying: boolean;
  isLive: boolean;
}

function StatusIcon({ status }: { status: IndexingStatus }) {
  if (status === "indexed") {
    return (
      <svg className="w-4 h-4 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
      </svg>
    );
  }
  if (status === "failed") {
    return (
      <svg className="w-4 h-4 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
      </svg>
    );
  }
  // pending / processing / stale
  return (
    <svg className="w-4 h-4 text-amber-500 animate-spin" fill="none" viewBox="0 0 24 24">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
    </svg>
  );
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <button
      type="button"
      onClick={copy}
      className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-600 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors"
    >
      {copied ? (
        <>
          <svg className="w-3.5 h-3.5 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
          </svg>
          Copied!
        </>
      ) : (
        <>
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <rect x="9" y="9" width="13" height="13" rx="2" />
            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
          </svg>
          Copy
        </>
      )}
    </button>
  );
}

export default function Step4Deploy({
  agentId,
  agentName,
  userId,
  embedSnippet,
  knowledgeSources,
  onDeploy,
  isDeploying,
  isLive,
}: Step4DeployProps) {
  const pendingSources = knowledgeSources.filter(
    (s) => s.indexing_status === "pending" || s.indexing_status === "processing"
  );
  const failedSources = knowledgeSources.filter((s) => s.indexing_status === "failed");
  const hasPending = pendingSources.length > 0;

  return (
    <div className="space-y-6">
      {/* Status summary */}
      {isLive ? (
        <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-5 flex items-start gap-3">
          <div className="w-8 h-8 rounded-full bg-emerald-100 flex items-center justify-center flex-shrink-0">
            <svg className="w-4 h-4 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <div>
            <p className="text-sm font-semibold text-emerald-800">{agentName} is live!</p>
            <p className="text-sm text-emerald-700 mt-0.5">
              Your agent is now accepting conversations. Embed it on your site or share the link.
            </p>
          </div>
        </div>
      ) : (
        <div className={`border rounded-xl p-5 flex items-start gap-3 ${hasPending ? "bg-amber-50 border-amber-200" : "bg-slate-50 border-slate-200"}`}>
          <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${hasPending ? "bg-amber-100" : "bg-slate-100"}`}>
            {hasPending ? (
              <svg className="w-4 h-4 text-amber-600 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
            ) : (
              <svg className="w-4 h-4 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0z" />
              </svg>
            )}
          </div>
          <div>
            <p className={`text-sm font-semibold ${hasPending ? "text-amber-800" : "text-slate-700"}`}>
              {hasPending
                ? `${pendingSources.length} knowledge source${pendingSources.length > 1 ? "s" : ""} still indexing`
                : "Ready to go live"}
            </p>
            <p className={`text-sm mt-0.5 ${hasPending ? "text-amber-700" : "text-slate-500"}`}>
              {hasPending
                ? "You can still deploy now — the agent will answer using indexed sources and pick up remaining ones automatically."
                : "All knowledge sources are indexed. Click Go Live to start accepting conversations."}
            </p>
          </div>
        </div>
      )}

      {/* Knowledge source checklist */}
      {knowledgeSources.length > 0 && (
        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <h2 className="text-base font-semibold text-slate-900 mb-4">Knowledge Sources</h2>
          <ul className="space-y-2.5">
            {knowledgeSources.map((source) => (
              <li key={source.id} className="flex items-center gap-3">
                <StatusIcon status={source.indexing_status} />
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-slate-800 truncate">{source.title}</p>
                  <p className="text-xs text-slate-400 capitalize">
                    {source.source_type}
                    {source.indexing_status === "indexed" && source.chunk_count > 0
                      ? ` · ${source.chunk_count} chunks`
                      : source.indexing_status === "failed"
                      ? ` · ${source.error_message ?? "failed"}`
                      : ` · ${source.indexing_status}`}
                  </p>
                </div>
              </li>
            ))}
          </ul>

          {failedSources.length > 0 && (
            <p className="text-xs text-red-600 mt-4">
              {failedSources.length} source{failedSources.length > 1 ? "s" : ""} failed to index. You can remove
              them in the Knowledge step and re-add if needed.
            </p>
          )}
        </div>
      )}

      {/* Go Live button */}
      {!isLive && (
        <div className="bg-white rounded-xl border border-slate-200 p-6 text-center">
          <div className="w-14 h-14 rounded-full bg-brand/10 flex items-center justify-center mx-auto mb-4">
            <svg className="w-7 h-7 text-brand" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M5.25 5.653c0-.856.917-1.398 1.667-.986l11.54 6.348a1.125 1.125 0 0 1 0 1.971l-11.54 6.347a1.125 1.125 0 0 1-1.667-.985V5.653z" />
            </svg>
          </div>
          <h3 className="text-base font-semibold text-slate-900 mb-1">Deploy {agentName}</h3>
          <p className="text-sm text-slate-500 mb-5">
            Your agent will go live and start accepting conversations immediately.
          </p>
          <button
            type="button"
            onClick={onDeploy}
            disabled={isDeploying}
            className="px-8 py-2.5 text-sm font-semibold text-white bg-brand rounded-lg hover:bg-brand/90 disabled:opacity-60 disabled:cursor-not-allowed flex items-center gap-2 mx-auto"
          >
            {isDeploying && (
              <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
            )}
            {isDeploying ? "Deploying…" : "Go Live →"}
          </button>
        </div>
      )}

      {/* Embed code */}
      <div className="bg-white rounded-xl border border-slate-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-base font-semibold text-slate-900">Embed Code</h2>
            <p className="text-sm text-slate-500 mt-0.5">
              Add this snippet to your website&apos;s <code className="text-xs bg-slate-100 px-1 py-0.5 rounded">&lt;body&gt;</code> tag.
            </p>
          </div>
          <CopyButton text={embedSnippet} />
        </div>
        <pre className="bg-slate-900 text-slate-100 text-xs rounded-lg p-4 overflow-x-auto whitespace-pre-wrap break-all leading-relaxed">
          {embedSnippet}
        </pre>
      </div>

      {/* WhatsApp channel */}
      <div className="bg-white rounded-xl border border-slate-200 p-6">
        <WhatsAppConnect agentId={agentId} userId={userId} />
      </div>

      {/* Dashboard link (post-deploy) */}
      {isLive && (
        <div className="text-center pb-4">
          <a
            href={`/agents/${agentId}`}
            className="inline-flex items-center gap-2 px-6 py-2.5 text-sm font-semibold text-white bg-brand rounded-lg hover:bg-brand/90"
          >
            View Agent Dashboard →
          </a>
        </div>
      )}
    </div>
  );
}
