/** API base for the gitee-mcp backend (REST on 11161). */
export const API_BASE = "http://127.0.0.1:11161";

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!r.ok) {
    throw new Error(`HTTP ${r.status} on ${path}`);
  }
  return (await r.json()) as T;
}

export interface Health {
  status: string;
  server: string;
  version: string;
  uptime_seconds: number;
  tool_count: number;
  configured: boolean;
  tier: string;
  providers: {
    gitee: { tier: string; configured: boolean };
    llm: { available: boolean; base_url: string; model: string };
  };
}

export interface RadarRepo {
  full_name: string;
  owner: string;
  html_url: string;
  description: string;
  translation: string;
  need_translation: boolean;
  language: string | null;
  stargazers_count: number;
  forks_count: number;
  watchers_count: number;
  pushed_at: string;
  activity_score: number;
  recent_commits: { sha: string; message: string; date: string; author: string }[];
}

export interface RadarResponse {
  success: boolean;
  message: string;
  data: {
    repos: RadarRepo[];
    total: number;
    dead_seeds: string[];
    tier: string;
    generated_at: string;
  };
}
