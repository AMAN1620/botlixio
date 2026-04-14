import api from "./api";

export type AgentTone = "professional" | "friendly" | "casual" | "empathetic";
export type IndexingStatus = "pending" | "processing" | "indexed" | "failed" | "stale";

export interface AgentResponse {
  id: string;
  user_id: string;
  name: string;
  description: string | null;
  tone: AgentTone;
  welcome_message: string | null;
  fallback_message: string | null;
  primary_color: string | null;
  model: string;
  provider: string;
  temperature: number;
  max_tokens: number;
  status: "draft" | "live" | "paused";
  total_messages: number;
  total_sessions: number;
  created_at: string;
  updated_at: string;
}

export interface CrawledPage {
  url: string;
  title: string;
  char_count: number;
}

export interface KnowledgeResponse {
  id: string;
  agent_id: string;
  source_type: "url" | "file" | "text";
  title: string;
  file_name: string | null;
  file_size: number | null;
  chunk_count: number;
  char_count: number;
  indexing_status: IndexingStatus;
  error_message: string | null;
  indexed_at: string | null;
  root_url: string | null;
  path_filter: string | null;
  max_pages: number | null;
  crawled_pages: CrawledPage[] | null;
  created_at: string;
}

export interface KnowledgeStatusResponse {
  id: string;
  indexing_status: IndexingStatus;
  chunk_count: number;
  error_message: string | null;
  indexed_at: string | null;
  crawled_pages: CrawledPage[] | null;
}

// ─── Agents ──────────────────────────────────────────────────────────────────

export const agentsApi = {
  list() {
    return api.get<{ data: AgentResponse[]; total: number }>("/agents");
  },
  get(id: string) {
    return api.get<AgentResponse>(`/agents/${id}`);
  },
  create(data: {
    name: string;
    description?: string;
    tone?: AgentTone;
    welcome_message?: string;
    fallback_message?: string;
    primary_color?: string;
    model?: string;
    temperature?: number;
    max_tokens?: number;
  }) {
    return api.post<AgentResponse>("/agents", data);
  },
  update(
    id: string,
    data: {
      name?: string;
      description?: string;
      tone?: AgentTone;
      welcome_message?: string;
      fallback_message?: string;
      primary_color?: string;
      model?: string;
      temperature?: number;
      max_tokens?: number;
    }
  ) {
    return api.patch<AgentResponse>(`/agents/${id}`, data);
  },
  delete(id: string) {
    return api.delete(`/agents/${id}`);
  },
  deploy(id: string) {
    return api.post<AgentResponse>(`/agents/${id}/deploy`);
  },
  pause(id: string) {
    return api.post<AgentResponse>(`/agents/${id}/pause`);
  },
  embedCode(id: string) {
    return api.get<{ agent_id: string; agent_name: string; snippet: string }>(
      `/agents/${id}/embed-code`
    );
  },
};

// ─── Knowledge ───────────────────────────────────────────────────────────────

export const knowledgeApi = {
  list(agentId: string) {
    return api.get<{ data: KnowledgeResponse[]; total: number }>(
      `/agents/${agentId}/knowledge`
    );
  },

  /** Start crawling a website. Returns immediately with status=pending. */
  addUrl(
    agentId: string,
    payload: { root_url: string; path_filter?: string; max_pages?: number }
  ) {
    return api.post<KnowledgeResponse>(`/agents/${agentId}/knowledge/url`, payload);
  },

  /** Poll indexing status for a single source. */
  getStatus(agentId: string, knowledgeId: string) {
    return api.get<KnowledgeStatusResponse>(
      `/agents/${agentId}/knowledge/${knowledgeId}/status`
    );
  },

  addText(agentId: string, title: string, content: string) {
    return api.post<KnowledgeResponse>(`/agents/${agentId}/knowledge/text`, {
      title,
      content,
    });
  },

  upload(agentId: string, file: File) {
    const form = new FormData();
    form.append("file", file);
    return api.post<KnowledgeResponse>(`/agents/${agentId}/knowledge/upload`, form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },

  /** Remove one crawled page from a URL source. */
  removePage(agentId: string, knowledgeId: string, url: string) {
    return api.delete(`/agents/${agentId}/knowledge/${knowledgeId}/pages`, {
      data: { url },
    });
  },

  /** Add a specific missing URL to an existing URL source. */
  addPage(agentId: string, knowledgeId: string, url: string) {
    return api.post(`/agents/${agentId}/knowledge/${knowledgeId}/pages`, { url });
  },

  delete(agentId: string, sourceId: string) {
    return api.delete(`/agents/${agentId}/knowledge/${sourceId}`);
  },
};
