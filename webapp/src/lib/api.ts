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
  momentum?: number | null;
  momentum_7d?: number | null;
  surge?: boolean;
  stars_delta_7d?: number | null;
  forks_delta_7d?: number | null;
  recent_commits: { sha: string; message: string; date: string; author: string }[];
}

export interface RadarResponse {
  success: boolean;
  message: string;
  data: {
    repos: RadarRepo[];
    total: number;
    dead_seeds: string[];
    throttled_seeds: string[];
    rate_limited: boolean;
    tier: string;
    generated_at: string;
  };
}

export interface Mover {
  full_name: string;
  delta: number;
  current_score: number;
  prev_score: number;
  stars_delta: number;
  forks_delta: number;
}

export interface WatchEntry {
  full_name: string;
  min_activity: number | null;
  added_at: number;
}

export interface GraphNode {
  id: string;
  kind: "org" | "repo";
  label: string;
}

export interface GraphEdge {
  source: string;
  target: string;
  relation: string;
}

export interface DigestResult {
  success: boolean;
  days: number;
  narrative: string;
  movers: Mover[];
  polished: boolean;
}

export interface MirrorResult {
  success: boolean;
  on_github: boolean;
  owner: string;
  repo: string;
  github?: {
    stargazers_count: number;
    forks_count: number;
    pushed_at: string;
    description: string | null;
    language: string | null;
    html_url: string;
  };
  gitee?: {
    stargazers_count: number | null;
    forks_count: number | null;
    pushed_at: string | null;
  };
  delta?: { stars: number | null; forks: number | null } | null;
  note?: string;
  error?: string;
}
