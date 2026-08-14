// 极简 API 封装
const BASE = "/api";

async function req<T>(path: string, opts?: RequestInit): Promise<T> {
  const res = await fetch(BASE + path, {
    headers: { "Content-Type": "application/json" },
    ...opts,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      detail = (await res.json()).detail ?? detail;
    } catch {}
    throw new Error(detail);
  }
  return res.json();
}

import type { Dashboard, Distillation, LLMConfig, Novel, Skill, StyleProfile } from "./types";

export const api = {
  dashboard: () => req<Dashboard>("/dashboard"),

  novels: () => req<Novel[]>("/novels"),
  createNovel: (body: Partial<Novel> & { content?: string; tags?: string[] }) =>
    req<Novel>("/novels", { method: "POST", body: JSON.stringify(body) }),
  uploadNovel: async (form: FormData) => {
    const res = await fetch(BASE + "/novels/upload", { method: "POST", body: form });
    if (!res.ok) throw new Error((await res.json()).detail ?? "上传失败");
    return (await res.json()) as Novel;
  },
  deleteNovel: (id: number) => req<{ ok: boolean }>(`/novels/${id}`, { method: "DELETE" }),
  distill: (id: number) => req<Distillation>(`/novels/${id}/distill`, { method: "POST" }),
  distillation: (id: number) => req<Distillation>(`/novels/${id}/distillation`),

  styles: () => req<StyleProfile[]>("/styles"),
  style: (id: number) => req<StyleProfile>(`/styles/${id}`),
  cluster: (name: string, novel_ids: number[], description = "") =>
    req<StyleProfile>("/styles/cluster", {
      method: "POST",
      body: JSON.stringify({ name, novel_ids, description }),
    }),
  deleteStyle: (id: number) => req<{ ok: boolean }>(`/styles/${id}`, { method: "DELETE" }),

  skills: () => req<Skill[]>("/skills"),
  exportSkill: (profileId: number, version = "v1.0", name = "") =>
    req<Skill>(`/skills/from-profile/${profileId}`, {
      method: "POST",
      body: JSON.stringify({ version, name }),
    }),
  previewSkill: (id: number) => req<{ files: Record<string, string> }>(`/skills/${id}/preview`),
  downloadSkillUrl: (id: number) => `${BASE}/skills/${id}/download`,
  deleteSkill: (id: number) => req<{ ok: boolean }>(`/skills/${id}`, { method: "DELETE" }),

  llmConfig: () => req<LLMConfig>("/settings/llm"),
  updateLlmConfig: (body: { api_key?: string | null; model?: string; base_url?: string }) =>
    req<LLMConfig>("/settings/llm", { method: "PUT", body: JSON.stringify(body) }),
  testLlm: () => req<{ ok: boolean; message: string }>("/settings/llm/test", { method: "POST" }),
};
