"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { agentsApi, type AgentResponse } from "@/lib/agents-api";

const statusColors = {
  draft: "bg-slate-100 text-slate-600",
  live: "bg-green-100 text-green-700",
  paused: "bg-amber-100 text-amber-700",
};

export default function AgentsPage() {
  const [agents, setAgents] = useState<AgentResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [togglingId, setTogglingId] = useState<string | null>(null);

  const load = async () => {
    try {
      const { data } = await agentsApi.list();
      setAgents(data.data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const toggle = async (agent: AgentResponse) => {
    setTogglingId(agent.id);
    try {
      const updated =
        agent.status === "live"
          ? await agentsApi.pause(agent.id)
          : await agentsApi.deploy(agent.id);
      setAgents((prev) => prev.map((a) => (a.id === agent.id ? updated.data : a)));
    } catch {
      alert("Failed to update agent status.");
    } finally {
      setTogglingId(null);
    }
  };

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center text-slate-400">
        Loading agents…
      </div>
    );
  }

  return (
    <div>
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-black tracking-tight text-slate-900">Agents</h1>
          <p className="mt-1 text-slate-500">Build and manage your AI support agents</p>
        </div>
        <Link
          href="/agents/new"
          className="rounded-xl bg-brand px-6 py-3 text-sm font-bold text-white hover:bg-brand/90"
        >
          + New Agent
        </Link>
      </div>

      {agents.length === 0 ? (
        <div className="flex flex-col items-center gap-6 rounded-2xl border-2 border-dashed border-slate-200 py-24 text-center">
          <div className="flex size-16 items-center justify-center rounded-full bg-brand-light">
            <svg className="size-8 text-brand" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M8.625 9.75a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0H8.25m4.125 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0H12m4.125 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0h-.375m-13.5 3.01c0 1.6 1.123 2.994 2.707 3.227 1.087.16 2.185.283 3.293.369V21l4.184-4.183a1.14 1.14 0 0 1 .778-.332 48.294 48.294 0 0 0 5.83-.498c1.585-.233 2.708-1.626 2.708-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0 0 12 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018Z" />
            </svg>
          </div>
          <div>
            <p className="text-lg font-bold text-slate-900">No agents yet</p>
            <p className="mt-1 text-slate-500">Create your first customer support bot</p>
          </div>
          <Link
            href="/agents/new"
            className="rounded-xl bg-brand px-8 py-3 font-bold text-white hover:bg-brand/90"
          >
            Create Agent
          </Link>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {agents.map((agent) => (
            <div
              key={agent.id}
              className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"
            >
              <div className="mb-4 flex items-start justify-between">
                <div className="flex size-11 items-center justify-center rounded-xl bg-brand-light">
                  <svg className="size-5 text-brand" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M8.625 9.75a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0H8.25m4.125 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0H12m4.125 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 0 1-2.555-.337A5.972 5.972 0 0 1 5.41 20.97a5.969 5.969 0 0 1-.474-.065 4.48 4.48 0 0 0 .978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25Z" />
                  </svg>
                </div>
                <span className={`rounded-full px-2.5 py-1 text-xs font-semibold capitalize ${statusColors[agent.status]}`}>
                  {agent.status}
                </span>
              </div>

              <h3 className="font-bold text-slate-900">{agent.name}</h3>
              <p className="mt-1 text-sm text-slate-500 line-clamp-2">
                {agent.description || agent.system_prompt}
              </p>

              <div className="mt-4 flex items-center gap-4 text-xs text-slate-400">
                <span>{agent.total_messages} messages</span>
                <span>{agent.total_sessions} sessions</span>
              </div>

              <div className="mt-4 flex gap-2">
                <Link
                  href={`/agents/${agent.id}`}
                  className="flex-1 rounded-lg border border-slate-200 py-2 text-center text-sm font-medium text-slate-700 hover:bg-slate-50"
                >
                  Manage
                </Link>
                <button
                  onClick={() => toggle(agent)}
                  disabled={togglingId === agent.id}
                  className={`flex-1 rounded-lg py-2 text-sm font-medium ${
                    agent.status === "live"
                      ? "border border-amber-200 text-amber-700 hover:bg-amber-50"
                      : "bg-brand text-white hover:bg-brand/90"
                  }`}
                >
                  {togglingId === agent.id
                    ? "…"
                    : agent.status === "live"
                    ? "Pause"
                    : "Deploy"}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
