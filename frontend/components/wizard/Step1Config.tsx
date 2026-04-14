"use client";

import { AgentTone } from "@/lib/agents-api";

const TONES: { value: AgentTone; label: string; description: string; emoji: string }[] = [
  {
    value: "professional",
    label: "Professional",
    description: "Formal, precise, business language",
    emoji: "💼",
  },
  {
    value: "friendly",
    label: "Friendly",
    description: "Warm, conversational, approachable",
    emoji: "😊",
  },
  {
    value: "casual",
    label: "Casual",
    description: "Relaxed, informal, uses contractions",
    emoji: "👋",
  },
  {
    value: "empathetic",
    label: "Empathetic",
    description: "Supportive, patient, understanding",
    emoji: "🤝",
  },
];

export interface Step1Data {
  name: string;
  description: string;
  tone: AgentTone;
  welcome_message: string;
  fallback_message: string;
}

interface Step1ConfigProps {
  data: Step1Data;
  onChange: (data: Partial<Step1Data>) => void;
  error?: string | null;
}

export default function Step1Config({ data, onChange, error }: Step1ConfigProps) {
  return (
    <div className="space-y-6">
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-3 rounded-lg">
          {error}
        </div>
      )}

      {/* Basic identity */}
      <div className="bg-white rounded-xl border border-slate-200 p-6">
        <h2 className="text-base font-semibold text-slate-900 mb-1">Agent Identity</h2>
        <p className="text-sm text-slate-500 mb-5">Give your agent a name and describe what it does.</p>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">
              Agent Name <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={data.name}
              onChange={(e) => onChange({ name: e.target.value })}
              placeholder="e.g. Support Bot, Sales Assistant"
              className="w-full px-3 py-2.5 text-sm border border-slate-200 rounded-lg focus:outline-none focus:border-brand focus:ring-2 focus:ring-brand/10"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">
              Description
            </label>
            <input
              type="text"
              value={data.description}
              onChange={(e) => onChange({ description: e.target.value })}
              placeholder="e.g. Handles customer support for Acme Co."
              className="w-full px-3 py-2.5 text-sm border border-slate-200 rounded-lg focus:outline-none focus:border-brand focus:ring-2 focus:ring-brand/10"
            />
            <p className="text-xs text-slate-400 mt-1.5">
              Shown in the widget header. Also used to shape the agent&apos;s system prompt.
            </p>
          </div>
        </div>
      </div>

      {/* Tone selector */}
      <div className="bg-white rounded-xl border border-slate-200 p-6">
        <h2 className="text-base font-semibold text-slate-900 mb-1">Tone & Personality</h2>
        <p className="text-sm text-slate-500 mb-5">
          Choose how your agent communicates. This shapes the system prompt automatically.
        </p>

        <div className="grid grid-cols-2 gap-3">
          {TONES.map((tone) => {
            const isSelected = data.tone === tone.value;
            return (
              <button
                key={tone.value}
                type="button"
                onClick={() => onChange({ tone: tone.value })}
                className={`text-left p-4 rounded-xl border-2 transition-all ${
                  isSelected
                    ? "border-brand bg-brand-light"
                    : "border-slate-200 hover:border-slate-300 bg-white"
                }`}
              >
                <div className="flex items-center gap-2 mb-1.5">
                  <span className="text-xl">{tone.emoji}</span>
                  <span className={`text-sm font-semibold ${isSelected ? "text-brand" : "text-slate-800"}`}>
                    {tone.label}
                  </span>
                  {isSelected && (
                    <span className="ml-auto w-4 h-4 rounded-full bg-brand flex items-center justify-center flex-shrink-0">
                      <svg className="w-2.5 h-2.5 text-white" fill="currentColor" viewBox="0 0 12 12">
                        <path d="M10 3L5 8.5 2 5.5" stroke="currentColor" strokeWidth="1.5" fill="none" strokeLinecap="round" strokeLinejoin="round" />
                      </svg>
                    </span>
                  )}
                </div>
                <p className="text-xs text-slate-500">{tone.description}</p>
              </button>
            );
          })}
        </div>
      </div>

      {/* Messages */}
      <div className="bg-white rounded-xl border border-slate-200 p-6">
        <h2 className="text-base font-semibold text-slate-900 mb-1">Default Messages</h2>
        <p className="text-sm text-slate-500 mb-5">What the agent says at key moments.</p>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">
              Welcome Message
            </label>
            <input
              type="text"
              value={data.welcome_message}
              onChange={(e) => onChange({ welcome_message: e.target.value })}
              placeholder="Hi! How can I help you today?"
              className="w-full px-3 py-2.5 text-sm border border-slate-200 rounded-lg focus:outline-none focus:border-brand focus:ring-2 focus:ring-brand/10"
            />
            <p className="text-xs text-slate-400 mt-1.5">
              First message shown when the widget opens.
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">
              Fallback Message
            </label>
            <input
              type="text"
              value={data.fallback_message}
              onChange={(e) => onChange({ fallback_message: e.target.value })}
              placeholder="I'm not able to help with that right now. Please try again later."
              className="w-full px-3 py-2.5 text-sm border border-slate-200 rounded-lg focus:outline-none focus:border-brand focus:ring-2 focus:ring-brand/10"
            />
            <p className="text-xs text-slate-400 mt-1.5">
              Shown when the agent is paused or cannot answer.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
