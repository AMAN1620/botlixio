"use client";

const MODELS = [
  {
    id: "gpt-4o",
    label: "GPT-4o",
    provider: "OpenAI",
    description: "Most capable — best reasoning and instruction following",
    badge: "Recommended",
  },
  {
    id: "gpt-4o-mini",
    label: "GPT-4o Mini",
    provider: "OpenAI",
    description: "Fast and cost-efficient — great for high-volume support",
    badge: null,
  },
  {
    id: "claude-sonnet-4-6",
    label: "Claude Sonnet 4.6",
    provider: "Anthropic",
    description: "Excellent at nuanced writing and complex instructions",
    badge: null,
  },
];

const TOOLS = [
  {
    id: "web_search",
    label: "Web Search",
    description: "Let the agent look up current information from the web",
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-4.35-4.35M17 11A6 6 0 1 1 5 11a6 6 0 0 1 12 0z" />
      </svg>
    ),
  },
  {
    id: "lead_catcher",
    label: "Lead Catcher",
    description: "Capture visitor name, email, and phone during chat",
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M16 12a4 4 0 1 1-8 0 4 4 0 0 1 8 0zm0 0v1.5a2.5 2.5 0 0 0 5 0V12a9 9 0 1 0-9 9m4.5-1.206a8.959 8.959 0 0 1-4.5 1.207" />
      </svg>
    ),
  },
  {
    id: "weather",
    label: "Weather",
    description: "Answer questions about current weather for any location",
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 15a4.5 4.5 0 0 0 9 0 4.5 4.5 0 0 0-1.523-3.357A5.25 5.25 0 0 0 6.75 4.5a5.25 5.25 0 0 0-5.25 5.25A5.25 5.25 0 0 0 2.25 15zm17.25 0a4.5 4.5 0 0 0-4.5-4.5 4.479 4.479 0 0 0-1.523.265A5.243 5.243 0 0 0 15 9.75a5.25 5.25 0 0 0-1.523 3.393A4.5 4.5 0 0 0 19.5 15z" />
      </svg>
    ),
  },
];

export interface Step3Data {
  model: string;
  temperature: number;
  max_tokens: number;
  enabled_tools: string[];
}

interface Step3ToolsProps {
  data: Step3Data;
  onChange: (data: Partial<Step3Data>) => void;
}

function ToggleTool({
  tool,
  enabled,
  onToggle,
}: {
  tool: (typeof TOOLS)[number];
  enabled: boolean;
  onToggle: () => void;
}) {
  return (
    <div
      className={`flex items-start gap-4 p-4 rounded-xl border-2 transition-all cursor-pointer ${
        enabled ? "border-brand bg-brand-light" : "border-slate-200 bg-white hover:border-slate-300"
      }`}
      onClick={onToggle}
    >
      <div className={`mt-0.5 flex-shrink-0 ${enabled ? "text-brand" : "text-slate-400"}`}>
        {tool.icon}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between gap-2">
          <span className={`text-sm font-semibold ${enabled ? "text-brand" : "text-slate-800"}`}>
            {tool.label}
          </span>
          {/* Toggle switch */}
          <div
            className={`relative flex-shrink-0 w-10 h-5 rounded-full transition-colors ${
              enabled ? "bg-brand" : "bg-slate-200"
            }`}
          >
            <div
              className={`absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white shadow transition-transform ${
                enabled ? "translate-x-5" : "translate-x-0"
              }`}
            />
          </div>
        </div>
        <p className="text-xs text-slate-500 mt-0.5">{tool.description}</p>
      </div>
    </div>
  );
}

export default function Step3Tools({ data, onChange }: Step3ToolsProps) {
  function toggleTool(toolId: string) {
    const current = data.enabled_tools;
    const next = current.includes(toolId)
      ? current.filter((t) => t !== toolId)
      : [...current, toolId];
    onChange({ enabled_tools: next });
  }

  return (
    <div className="space-y-6">
      {/* Model selector */}
      <div className="bg-white rounded-xl border border-slate-200 p-6">
        <h2 className="text-base font-semibold text-slate-900 mb-1">AI Model</h2>
        <p className="text-sm text-slate-500 mb-5">
          Choose the language model that powers your agent.
        </p>

        <div className="space-y-3">
          {MODELS.map((model) => {
            const isSelected = data.model === model.id;
            return (
              <button
                key={model.id}
                type="button"
                onClick={() => onChange({ model: model.id })}
                className={`w-full text-left flex items-start gap-4 p-4 rounded-xl border-2 transition-all ${
                  isSelected
                    ? "border-brand bg-brand-light"
                    : "border-slate-200 hover:border-slate-300 bg-white"
                }`}
              >
                {/* Radio dot */}
                <div
                  className={`mt-0.5 flex-shrink-0 w-4 h-4 rounded-full border-2 flex items-center justify-center ${
                    isSelected ? "border-brand" : "border-slate-300"
                  }`}
                >
                  {isSelected && <div className="w-2 h-2 rounded-full bg-brand" />}
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span
                      className={`text-sm font-semibold ${
                        isSelected ? "text-brand" : "text-slate-800"
                      }`}
                    >
                      {model.label}
                    </span>
                    <span className="text-xs text-slate-400">{model.provider}</span>
                    {model.badge && (
                      <span className="text-xs font-medium bg-brand/10 text-brand px-2 py-0.5 rounded-full">
                        {model.badge}
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-slate-500 mt-0.5">{model.description}</p>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Temperature */}
      <div className="bg-white rounded-xl border border-slate-200 p-6">
        <div className="flex items-center justify-between mb-1">
          <h2 className="text-base font-semibold text-slate-900">Temperature</h2>
          <span className="text-sm font-semibold text-brand tabular-nums">
            {data.temperature.toFixed(1)}
          </span>
        </div>
        <p className="text-sm text-slate-500 mb-5">
          Lower = more precise and deterministic. Higher = more creative and varied.
        </p>

        <input
          type="range"
          min={0}
          max={1}
          step={0.1}
          value={data.temperature}
          onChange={(e) => onChange({ temperature: parseFloat(e.target.value) })}
          className="w-full accent-brand"
        />
        <div className="flex justify-between text-xs text-slate-400 mt-1.5">
          <span>0.0 — Precise</span>
          <span>1.0 — Creative</span>
        </div>
      </div>

      {/* Max tokens */}
      <div className="bg-white rounded-xl border border-slate-200 p-6">
        <div className="flex items-center justify-between mb-1">
          <h2 className="text-base font-semibold text-slate-900">Max Response Length</h2>
          <span className="text-sm font-semibold text-brand tabular-nums">
            {data.max_tokens} tokens
          </span>
        </div>
        <p className="text-sm text-slate-500 mb-5">
          Maximum number of tokens the agent can use per reply (~750 tokens ≈ 500 words).
        </p>

        <input
          type="range"
          min={256}
          max={4096}
          step={256}
          value={data.max_tokens}
          onChange={(e) => onChange({ max_tokens: parseInt(e.target.value, 10) })}
          className="w-full accent-brand"
        />
        <div className="flex justify-between text-xs text-slate-400 mt-1.5">
          <span>256 — Brief</span>
          <span>4096 — Detailed</span>
        </div>
      </div>

      {/* Tools */}
      <div className="bg-white rounded-xl border border-slate-200 p-6">
        <h2 className="text-base font-semibold text-slate-900 mb-1">Tools</h2>
        <p className="text-sm text-slate-500 mb-5">
          Give your agent extra capabilities beyond its knowledge base.
        </p>

        <div className="space-y-3">
          {TOOLS.map((tool) => (
            <ToggleTool
              key={tool.id}
              tool={tool}
              enabled={data.enabled_tools.includes(tool.id)}
              onToggle={() => toggleTool(tool.id)}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
