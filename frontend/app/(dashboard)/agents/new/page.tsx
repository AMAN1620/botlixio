"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { agentsApi } from "@/lib/agents-api";

export default function NewAgentPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [form, setForm] = useState({
    name: "",
    description: "",
    system_prompt:
      "You are a helpful customer support assistant. Answer questions based on the knowledge base provided. Be concise, friendly, and accurate.",
    welcome_message: "Hi! How can I help you today?",
    fallback_message:
      "I'm sorry, I didn't understand that. Could you rephrase your question?",
    primary_color: "#2513EC",
  });

  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
    setForm((f) => ({ ...f, [k]: e.target.value }));

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.name.trim()) { setError("Agent name is required"); return; }
    setLoading(true);
    setError("");
    try {
      const { data } = await agentsApi.create(form);
      router.push(`/agents/${data.id}`);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || "Failed to create agent");
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-2xl">
      <div className="mb-8">
        <Link href="/agents" className="text-sm text-slate-500 hover:text-brand">
          ← Back to Agents
        </Link>
        <h1 className="mt-4 text-3xl font-black tracking-tight text-slate-900">
          Create Agent
        </h1>
        <p className="mt-1 text-slate-500">
          Set up your customer support bot. You can add knowledge after creation.
        </p>
      </div>

      <form onSubmit={submit} className="flex flex-col gap-6">
        {error && (
          <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}

        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="mb-5 text-lg font-bold text-slate-900">Basic Info</h2>

          <div className="flex flex-col gap-4">
            <div>
              <label className="mb-1.5 block text-sm font-semibold text-slate-700">
                Agent Name *
              </label>
              <input
                value={form.name}
                onChange={set("name")}
                placeholder="e.g. Support Bot, Sales Assistant"
                className="w-full rounded-xl border border-slate-200 px-4 py-3 text-sm outline-none focus:border-brand"
              />
            </div>

            <div>
              <label className="mb-1.5 block text-sm font-semibold text-slate-700">
                Description
              </label>
              <input
                value={form.description}
                onChange={set("description")}
                placeholder="Brief description of what this bot does"
                className="w-full rounded-xl border border-slate-200 px-4 py-3 text-sm outline-none focus:border-brand"
              />
            </div>

            <div>
              <label className="mb-1.5 block text-sm font-semibold text-slate-700">
                Brand Color
              </label>
              <div className="flex items-center gap-3">
                <input
                  type="color"
                  value={form.primary_color}
                  onChange={set("primary_color")}
                  className="h-10 w-16 cursor-pointer rounded-lg border border-slate-200"
                />
                <span className="text-sm text-slate-500">{form.primary_color}</span>
              </div>
            </div>
          </div>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="mb-5 text-lg font-bold text-slate-900">Personality</h2>

          <div className="flex flex-col gap-4">
            <div>
              <label className="mb-1.5 block text-sm font-semibold text-slate-700">
                System Prompt
              </label>
              <p className="mb-2 text-xs text-slate-400">
                Instructions that define how your bot behaves
              </p>
              <textarea
                value={form.system_prompt}
                onChange={set("system_prompt")}
                rows={4}
                className="w-full rounded-xl border border-slate-200 px-4 py-3 text-sm outline-none focus:border-brand"
              />
            </div>

            <div>
              <label className="mb-1.5 block text-sm font-semibold text-slate-700">
                Welcome Message
              </label>
              <input
                value={form.welcome_message}
                onChange={set("welcome_message")}
                className="w-full rounded-xl border border-slate-200 px-4 py-3 text-sm outline-none focus:border-brand"
              />
            </div>

            <div>
              <label className="mb-1.5 block text-sm font-semibold text-slate-700">
                Fallback Message
              </label>
              <p className="mb-2 text-xs text-slate-400">
                Shown when the bot can&apos;t answer
              </p>
              <input
                value={form.fallback_message}
                onChange={set("fallback_message")}
                className="w-full rounded-xl border border-slate-200 px-4 py-3 text-sm outline-none focus:border-brand"
              />
            </div>
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="rounded-xl bg-brand py-4 text-center font-bold text-white disabled:opacity-50 hover:bg-brand/90"
        >
          {loading ? "Creating…" : "Create Agent"}
        </button>
      </form>
    </div>
  );
}
