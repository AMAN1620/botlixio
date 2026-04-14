"use client";

const STEPS = [
  { number: 1, label: "Basic Config" },
  { number: 2, label: "Knowledge" },
  { number: 3, label: "Tools & Model" },
  { number: 4, label: "Deploy" },
];

interface WizardLayoutProps {
  currentStep: number;
  children: React.ReactNode;
  onNext: () => void;
  onBack: () => void;
  isSaving?: boolean;
  nextLabel?: string;
  hideNext?: boolean;
}

export default function WizardLayout({
  currentStep,
  children,
  onNext,
  onBack,
  isSaving = false,
  nextLabel,
  hideNext = false,
}: WizardLayoutProps) {
  const isFirst = currentStep === 1;
  const isLast = currentStep === 4;

  return (
    <div className="min-h-screen bg-page-bg">
      {/* Header */}
      <div className="bg-white border-b border-slate-200 px-6 py-4">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-lg font-semibold text-slate-900">Create New Agent</h1>
            <p className="text-sm text-slate-500 mt-0.5">
              Step {currentStep} of {STEPS.length} — {STEPS[currentStep - 1].label}
            </p>
          </div>
          <a href="/agents" className="text-sm text-slate-500 hover:text-slate-700">
            Cancel
          </a>
        </div>
      </div>

      {/* Step indicator */}
      <div className="bg-white border-b border-slate-200 px-6 py-4">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center gap-0">
            {STEPS.map((step, i) => {
              const done = step.number < currentStep;
              const active = step.number === currentStep;
              return (
                <div key={step.number} className="flex items-center flex-1 last:flex-none">
                  <div className="flex items-center gap-2">
                    <div
                      className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold flex-shrink-0 ${
                        done
                          ? "bg-brand text-white"
                          : active
                          ? "bg-brand text-white ring-4 ring-brand/20"
                          : "bg-slate-100 text-slate-400"
                      }`}
                    >
                      {done ? (
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                        </svg>
                      ) : (
                        step.number
                      )}
                    </div>
                    <span
                      className={`text-sm hidden sm:block ${
                        active ? "font-semibold text-slate-900" : done ? "text-slate-600" : "text-slate-400"
                      }`}
                    >
                      {step.label}
                    </span>
                  </div>
                  {i < STEPS.length - 1 && (
                    <div className={`flex-1 h-px mx-3 ${done ? "bg-brand" : "bg-slate-200"}`} />
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-4xl mx-auto px-6 py-8">
        {children}
      </div>

      {/* Footer nav */}
      <div className="bg-white border-t border-slate-200 px-6 py-4 sticky bottom-0">
        <div className="max-w-4xl mx-auto flex justify-between items-center">
          <button
            onClick={onBack}
            disabled={isFirst}
            className="px-5 py-2 text-sm font-medium text-slate-600 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            ← Back
          </button>

          {!hideNext && (
            <button
              onClick={onNext}
              disabled={isSaving}
              className="px-6 py-2 text-sm font-semibold text-white bg-brand rounded-lg hover:bg-brand/90 disabled:opacity-60 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {isSaving && (
                <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                </svg>
              )}
              {nextLabel ?? (isLast ? "Go Live →" : "Next →")}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
