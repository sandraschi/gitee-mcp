import { api } from "@/lib/api";
import { KeyRound, Search as SearchIcon } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";

interface UserHit {
  login: string;
  name: string;
  html_url: string;
  remark: string;
}

interface RepoHit {
  full_name: string;
  html_url: string;
  description: string;
  language: string | null;
  stargazers_count: number;
  forks_count: number;
  pushed_at: string;
}

export default function Search() {
  const [mode, setMode] = useState<"users" | "repos">("users");
  const [query, setQuery] = useState("");
  const [users, setUsers] = useState<UserHit[]>([]);
  const [repos, setRepos] = useState<RepoHit[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const run = async () => {
    if (!query.trim()) return;
    setLoading(true);
    setError("");
    setUsers([]);
    setRepos([]);
    try {
      if (mode === "users") {
        const res = await api<{ data: UserHit[]; count: number }>(
          `/api/search/users?q=${encodeURIComponent(query)}&limit=15`,
        );
        setUsers(res.data);
      } else {
        const res = await api<{
          data: RepoHit[];
          count: number;
          success: boolean;
          error?: string;
          error_type?: string;
        }>(`/api/search/repos?q=${encodeURIComponent(query)}&limit=15`);
        if (!res.success) {
          setError(res.error || "search failed");
        } else {
          setRepos(res.data);
        }
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "search failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div data-testid="search-page" className="mx-auto max-w-5xl">
      <h2 className="text-xl font-bold">Search Gitee</h2>
      <div className="mt-3 flex flex-wrap items-center gap-2">
        <div className="flex overflow-hidden rounded-lg border border-zinc-700">
          {(["users", "repos"] as const).map((m) => (
            <button
              type="button"
              key={m}
              data-testid={`mode-${m}`}
              onClick={() => {
                setMode(m);
                setError("");
              }}
              className={`px-4 py-1.5 text-sm ${mode === m ? "bg-amber-500 font-semibold text-zinc-950" : "bg-zinc-800 text-zinc-300"}`}
            >
              {m}
            </button>
          ))}
        </div>
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && void run()}
          data-testid="search-input"
          placeholder={mode === "users" ? "Gitee login or name..." : "repo keyword..."}
          className="w-72 rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-1.5 text-sm text-zinc-100 placeholder-zinc-500"
        />
        <button
          type="button"
          onClick={() => void run()}
          data-testid="search-submit"
          className="flex items-center gap-1.5 rounded-lg bg-amber-500 px-4 py-1.5 text-sm font-semibold text-zinc-950 hover:bg-amber-400"
        >
          <SearchIcon className="h-4 w-4" /> Search
        </button>
      </div>

      {mode === "repos" && (
        <div className="mt-3 flex items-start gap-2 rounded-lg border border-zinc-800 bg-zinc-900/50 p-3 text-xs text-zinc-400">
          <KeyRound className="mt-0.5 h-3.5 w-3.5 shrink-0 text-amber-500" />
          <span>
            Repo search needs the free Gitee token tier (anonymous search returns nothing on Gitee's
            side). Set
            <code className="mx-1 rounded bg-zinc-800 px-1">GITEE_TOKEN</code> in .env, or use the
            radar for anonymous discovery.
          </span>
        </div>
      )}

      {error && <p className="mt-3 text-sm text-red-400">{error}</p>}
      {loading && <p className="mt-3 text-sm text-zinc-500">Searching Gitee...</p>}

      <div className="mt-4 space-y-2">
        {users.map((u) => (
          <a
            key={u.login}
            href={u.html_url}
            target="_blank"
            rel="noreferrer"
            className="block rounded-lg border border-zinc-800 bg-zinc-900/50 p-3 hover:border-amber-500/50"
          >
            <div className="text-sm font-semibold text-amber-400">{u.login}</div>
            <div className="text-xs text-zinc-400">
              {u.name} {u.remark && `| ${u.remark}`}
            </div>
          </a>
        ))}
        {repos.map((r) => {
          const [owner, name] = r.full_name.split("/");
          return (
            <Link
              key={r.full_name}
              to={`/repo/${owner}/${name}`}
              className="block rounded-lg border border-zinc-800 bg-zinc-900/50 p-3 hover:border-amber-500/50"
            >
              <div className="flex items-center gap-2 text-sm">
                <span className="font-semibold text-amber-400">{r.full_name}</span>
                {r.language && (
                  <span className="rounded bg-zinc-800 px-1.5 text-[10px] uppercase text-zinc-400">
                    {r.language}
                  </span>
                )}
                <span className="ml-auto text-xs text-zinc-500">
                  ★ {r.stargazers_count.toLocaleString()}
                </span>
              </div>
              <p className="mt-1 truncate text-xs text-zinc-400">
                {r.description || "(no description)"}
              </p>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
