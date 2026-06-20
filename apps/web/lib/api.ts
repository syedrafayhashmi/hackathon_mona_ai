import type { Health, ModuleDefinition, RunRecord } from "./types";

export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, { ...init, cache: "no-store" });
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(body.detail || "Request failed");
  }
  return response.json();
}

export const api = {
  modules: () => request<ModuleDefinition[]>("/api/modules"),
  runs: () => request<RunRecord[]>("/api/runs"),
  health: () => request<Health>("/health"),
  createRun: (problemId: string, fixtureId: string, file?: File) => {
    const form = new FormData();
    form.set("problem_id", problemId);
    form.set("fixture_id", fixtureId);
    form.set("form_data", "{}");
    if (file) form.set("file", file);
    return request<RunRecord>("/api/runs", { method: "POST", body: form });
  },
  approve: (id: string) => request<RunRecord>(`/api/runs/${id}/approve`, { method: "POST" }),
  action: (id: string) => request<RunRecord>(`/api/runs/${id}/simulate-action`, { method: "POST" }),
  reset: () => request<{ status: string }>("/api/demo/reset", { method: "POST" }),
};

