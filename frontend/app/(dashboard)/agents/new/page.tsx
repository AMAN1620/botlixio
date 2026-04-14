"use client";

import { useState, useCallback, useEffect } from "react";
import WizardLayout from "@/components/wizard/WizardLayout";
import Step1Config, { Step1Data } from "@/components/wizard/Step1Config";
import Step2Knowledge from "@/components/wizard/Step2Knowledge";
import Step3Tools, { Step3Data } from "@/components/wizard/Step3Tools";
import Step4Deploy from "@/components/wizard/Step4Deploy";
import { agentsApi, knowledgeApi, KnowledgeResponse } from "@/lib/agents-api";
import { authApi } from "@/lib/api";

const SESSION_KEY = "botlixio_wizard_agent_id";

const DEFAULT_STEP1: Step1Data = {
  name: "",
  description: "",
  tone: "friendly",
  welcome_message: "Hi! How can I help you today?",
  fallback_message: "I'm not able to help with that right now. Please try again later.",
};

const DEFAULT_STEP3: Step3Data = {
  model: "gpt-4o",
  temperature: 0.7,
  max_tokens: 1024,
  enabled_tools: [],
};

export default function NewAgentPage() {
  // ── Step navigation ──────────────────────────────────────────────────────────
  const [step, setStep] = useState(1);
  const [isRestoring, setIsRestoring] = useState(true);

  // ── Step 1 state ─────────────────────────────────────────────────────────────
  const [step1, setStep1] = useState<Step1Data>(DEFAULT_STEP1);
  const [step1Error, setStep1Error] = useState<string | null>(null);
  const [isSavingStep1, setIsSavingStep1] = useState(false);

  // ── Created agent ─────────────────────────────────────────────────────────────
  const [agentId, setAgentId] = useState<string | null>(null);
  const [userId, setUserId] = useState<string>("");

  // ── Step 2 knowledge ─────────────────────────────────────────────────────────
  const [knowledgeSources, setKnowledgeSources] = useState<KnowledgeResponse[]>([]);

  const handleSourceAdded = useCallback((source: KnowledgeResponse) => {
    setKnowledgeSources((prev) => [source, ...prev]);
  }, []);

  const handleSourceDeleted = useCallback((id: string) => {
    setKnowledgeSources((prev) => prev.filter((s) => s.id !== id));
  }, []);

  // ── Step 3 state ─────────────────────────────────────────────────────────────
  const [step3, setStep3] = useState<Step3Data>(DEFAULT_STEP3);
  const [isSavingStep3, setIsSavingStep3] = useState(false);

  // ── Step 4 state ─────────────────────────────────────────────────────────────
  const [embedSnippet, setEmbedSnippet] = useState("");
  const [isDeploying, setIsDeploying] = useState(false);
  const [isLive, setIsLive] = useState(false);

  // ── Restore from sessionStorage on mount ─────────────────────────────────────
  useEffect(() => {
    async function restore() {
      // Always fetch the current user's ID
      try {
        const { data: me } = await authApi.me();
        setUserId(me.data.id);
      } catch {
        // Not fatal — WhatsApp pairing just won't work without it
      }

      const savedId = sessionStorage.getItem(SESSION_KEY);
      if (!savedId) {
        setIsRestoring(false);
        return;
      }
      try {
        const { data: agent } = await agentsApi.get(savedId);
        // Restore step 1 data from saved agent
        setAgentId(agent.id);
        setStep1({
          name: agent.name,
          description: agent.description ?? "",
          tone: agent.tone,
          welcome_message: agent.welcome_message ?? DEFAULT_STEP1.welcome_message,
          fallback_message: agent.fallback_message ?? DEFAULT_STEP1.fallback_message,
        });
        setStep3((prev) => ({
          ...prev,
          model: agent.model,
          temperature: agent.temperature,
          max_tokens: agent.max_tokens,
        }));
        // Restore knowledge sources
        const { data: knowledge } = await knowledgeApi.list(agent.id);
        setKnowledgeSources(knowledge.data);
        // If agent was already deployed, jump to step 4
        if (agent.status === "live") {
          setIsLive(true);
          const { data: embed } = await agentsApi.embedCode(agent.id);
          setEmbedSnippet(embed.snippet);
          setStep(4);
        } else {
          // Resume at step 2 (knowledge) since config is already saved
          setStep(2);
        }
      } catch {
        // Saved agent no longer exists — start fresh
        sessionStorage.removeItem(SESSION_KEY);
      } finally {
        setIsRestoring(false);
      }
    }
    restore();
  }, []);

  // ── Handlers ──────────────────────────────────────────────────────────────────

  const handleStep1Change = useCallback(
    (partial: Partial<Step1Data>) => setStep1((prev) => ({ ...prev, ...partial })),
    []
  );

  const handleStep3Change = useCallback(
    (partial: Partial<Step3Data>) => setStep3((prev) => ({ ...prev, ...partial })),
    []
  );

  // ── Next / Back ───────────────────────────────────────────────────────────────

  async function handleNext() {
    if (step === 1) {
      if (!step1.name.trim()) {
        setStep1Error("Agent name is required.");
        return;
      }
      setStep1Error(null);
      setIsSavingStep1(true);
      try {
        if (agentId) {
          await agentsApi.update(agentId, {
            name: step1.name,
            description: step1.description,
            tone: step1.tone,
            welcome_message: step1.welcome_message,
            fallback_message: step1.fallback_message,
          });
        } else {
          const { data } = await agentsApi.create({
            name: step1.name,
            description: step1.description,
            tone: step1.tone,
            welcome_message: step1.welcome_message,
            fallback_message: step1.fallback_message,
          });
          setAgentId(data.id);
          sessionStorage.setItem(SESSION_KEY, data.id);
        }
        setStep(2);
      } catch (err: unknown) {
        const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
        setStep1Error(msg ?? "Failed to save — please try again.");
      } finally {
        setIsSavingStep1(false);
      }
      return;
    }

    if (step === 2) {
      setStep(3);
      return;
    }

    if (step === 3) {
      if (!agentId) return;
      setIsSavingStep3(true);
      try {
        await agentsApi.update(agentId, {
          model: step3.model,
          temperature: step3.temperature,
          max_tokens: step3.max_tokens,
        });
        const { data } = await agentsApi.embedCode(agentId);
        setEmbedSnippet(data.snippet);
        setStep(4);
      } catch {
        setStep(4);
      } finally {
        setIsSavingStep3(false);
      }
      return;
    }
  }

  function handleBack() {
    if (step > 1) setStep((s) => s - 1);
  }

  async function handleDeploy() {
    if (!agentId) return;
    setIsDeploying(true);
    try {
      await agentsApi.deploy(agentId);
      setIsLive(true);
      if (!embedSnippet) {
        const { data } = await agentsApi.embedCode(agentId);
        setEmbedSnippet(data.snippet);
      }
      // Clear session — wizard is complete
      sessionStorage.removeItem(SESSION_KEY);
    } catch {
      // Ignore — user can retry
    } finally {
      setIsDeploying(false);
    }
  }

  // ── Wizard nav labels ─────────────────────────────────────────────────────────

  const isSaving = isSavingStep1 || isSavingStep3;
  const nextLabel =
    step === 1
      ? isSavingStep1 ? "Saving…" : "Next →"
      : step === 3
      ? isSavingStep3 ? "Saving…" : "Next →"
      : "Next →";

  const hideNext = step === 4;

  // ── Render ────────────────────────────────────────────────────────────────────

  if (isRestoring) {
    return (
      <div className="min-h-screen bg-page-bg flex items-center justify-center">
        <svg className="w-6 h-6 animate-spin text-brand" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
        </svg>
      </div>
    );
  }

  return (
    <WizardLayout
      currentStep={step}
      onNext={handleNext}
      onBack={handleBack}
      isSaving={isSaving}
      nextLabel={nextLabel}
      hideNext={hideNext}
    >
      {step === 1 && (
        <Step1Config data={step1} onChange={handleStep1Change} error={step1Error} />
      )}

      {step === 2 && agentId && (
        <Step2Knowledge
          agentId={agentId}
          sources={knowledgeSources}
          onSourceAdded={handleSourceAdded}
          onSourceDeleted={handleSourceDeleted}
        />
      )}

      {step === 3 && (
        <Step3Tools data={step3} onChange={handleStep3Change} />
      )}

      {step === 4 && agentId && (
        <Step4Deploy
          agentId={agentId}
          agentName={step1.name}
          userId={userId}
          embedSnippet={embedSnippet}
          knowledgeSources={knowledgeSources}
          onDeploy={handleDeploy}
          isDeploying={isDeploying}
          isLive={isLive}
        />
      )}
    </WizardLayout>
  );
}
