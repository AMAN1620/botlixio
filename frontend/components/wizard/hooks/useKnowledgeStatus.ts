"use client";

import { useEffect, useRef, useState } from "react";
import { knowledgeApi, KnowledgeStatusResponse, IndexingStatus } from "@/lib/agents-api";

interface UseKnowledgeStatusResult {
  status: IndexingStatus;
  data: KnowledgeStatusResponse | null;
}

/**
 * Polls GET /agents/{agentId}/knowledge/{knowledgeId}/status every 3s.
 * Stops automatically once status is "indexed" or "failed".
 */
export function useKnowledgeStatus(
  agentId: string,
  knowledgeId: string,
  initialStatus: IndexingStatus
): UseKnowledgeStatusResult {
  const [status, setStatus] = useState<IndexingStatus>(initialStatus);
  const [data, setData] = useState<KnowledgeStatusResponse | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (status === "indexed" || status === "failed") return;

    intervalRef.current = setInterval(async () => {
      try {
        const res = await knowledgeApi.getStatus(agentId, knowledgeId);
        setStatus(res.data.indexing_status);
        setData(res.data);
        if (res.data.indexing_status === "indexed" || res.data.indexing_status === "failed") {
          if (intervalRef.current) clearInterval(intervalRef.current);
        }
      } catch {
        // swallow — backend may be briefly unavailable
      }
    }, 3000);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [agentId, knowledgeId, status]);

  return { status, data };
}
