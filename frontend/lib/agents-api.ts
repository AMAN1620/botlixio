import api from "./api";

export interface AgentResponse {
  id: string;
  user_id: string;
  name: string;
  description: string | null;
  system_prompt: string;
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

export interface KnowledgeResponse {
  id: string;
  agent_id: string;
  source_type: "url" | "file" | "text";
  title: string;
  file_name: string | null;
  file_size: number | null;
  chunk_count: number;
  char_count: number;
  created_at: string;
}

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
    system_prompt?: string;
    welcome_message?: string;
    fallback_message?: string;
    primary_color?: string;
  }) {
    return api.post<AgentResponse>("/agents", data);
  },
  update(id: string, data: Partial<AgentResponse>) {
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

export const knowledgeApi = {
  list(agentId: string) {
    return api.get<{ data: KnowledgeResponse[]; total: number }>(
      `/agents/${agentId}/knowledge`
    );
  },
  addUrl(agentId: string, url: string) {
    return api.post<KnowledgeResponse>(`/agents/${agentId}/knowledge/url`, { url });
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
  delete(agentId: string, sourceId: string) {
    return api.delete(`/agents/${agentId}/knowledge/${sourceId}`);
  },
};
