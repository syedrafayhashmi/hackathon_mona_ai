import type { Health, ModuleDefinition, RunRecord } from "./types";

// Use same-origin requests by default so clients on other machines do not try
// to resolve `localhost` as the API host. Next.js proxies these paths to the
// API container through its internal Docker network.
export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "";

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
  createRun: (problemId: string, fixtureId: string, files?: File[], message?: string) => {
    const form = new FormData();
    form.set("problem_id", problemId);
    form.set("fixture_id", fixtureId);
    form.set("form_data", message ? JSON.stringify({ message }) : "{}");
    (files ?? []).forEach((f) => form.append("files", f));
    return request<RunRecord>("/api/runs", { method: "POST", body: form });
  },
  approve: (id: string) => request<RunRecord>(`/api/runs/${id}/approve`, { method: "POST" }),
  action: (id: string) => request<RunRecord>(`/api/runs/${id}/simulate-action`, { method: "POST" }),
  reset: () => request<{ status: string }>("/api/demo/reset", { method: "POST" }),
};
