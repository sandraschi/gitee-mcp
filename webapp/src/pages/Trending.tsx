import { type RadarRepo, type RadarResponse, api } from "@/lib/api";
import { GitCommitHorizontal, GitFork, Languages, Star } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";

const LANGUAGES = [
  "",
  "Python",
  "Java",
  "Go",
  "Rust",
  "TypeScript",
  "Vue",
  "JavaScript",
  "C",
  "C++",
];

export default function Trending() {
  const [repos, setRepos] = useState<RadarRepo[]>([]);
  const [language, setLanguage] = useState("");
  const [translate, setTranslate] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const q = new URLSearchParams({ limit: "20", translate: String(translate) });
      if (language) q.set("language", language);
      const res = await api<RadarResponse>(`/api/explore/humming?${q}`);
      setRepos(res.data.repos);
      setMessage(res.message);
    } catch (e) {
      setError(e instanceof Error ? e.message : "failed to load radar");
    } finally {
      setLoading(false);
    }
  }, [language, translate]);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <div data-testid="trending-page" className="mx-auto max-w-5xl">
      <div className="flex flex-wrap items-center gap-3">
        <h2 className="text-xl font-bold">Humming radar</h2>
        <select
          data-testid="language-filter"
          value={language}
          onChange={(e) => setLanguage(e.target.value)}
          className="rounded border border-zinc-700 bg-zinc-800 px-2 py-1 text-sm text-zinc-100"
        >
          {LANGUAGES.map((l) => (
            <option key={l} value={l}>
              {l || "All languages"}
            </option>
          ))}
        </select>
        <label className="flex items-center gap-1.5 text-sm text-zinc-400">
          <input
            type="checkbox"
            data-testid="translate-toggle"
            checked={translate}
            onChange={(e) => setTranslate(e.target.checked)}
            className="accent-amber-500"
          />
          <Languages className="h-3.5 w-3.5" /> Translate (zh → en)
        </label>
        <button
          type="button"
          onClick={() => void load()}
          data-testid="radar-refresh"
          className="ml-auto rounded border border-zinc-700 px-3 py-1 text-sm text-zinc-300 hover:border-amber-500 hover:text-amber-400"
        >
          Refresh
        </button>
      </div>

      {message && <p className="mt-2 text-xs text-zinc-500">{message}</p>}
      {error && <p className="mt-2 text-sm text-red-400">{error}</p>}
      {loading && <p className="mt-4 text-sm text-zinc-500">Fetching live Gitee data...</p>}

      <div className="mt-4 space-y-3">
        {repos.map((repo) => (
          <RepoCard key={repo.full_name} repo={repo} />
        ))}
        {!loading && !error && repos.length === 0 && (
          <p className="text-sm text-zinc-500">No repos match this filter.</p>
        )}
      </div>
    </div>
  );
}

function RepoCard({ repo }: { repo: RadarRepo }) {
  const [owner, name] = repo.full_name.split("/");
  return (
    <Link
      to={`/repo/${owner}/${name}`}
      data-testid="repo-card"
      className="block rounded-lg border border-zinc-800 bg-zinc-900/50 p-4 transition-colors hover:border-amber-500/50"
    >
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-sm font-semibold text-amber-400">{repo.full_name}</span>
        {repo.language && (
          <span className="rounded bg-zinc-800 px-1.5 py-0.5 text-[10px] uppercase text-zinc-400">
            {repo.language}
          </span>
        )}
        <span className="ml-auto flex items-center gap-3 text-xs text-zinc-400">
          <span className="flex items-center gap-1">
            <Star className="h-3 w-3 text-amber-500" /> {repo.stargazers_count.toLocaleString()}
          </span>
          <span className="flex items-center gap-1">
            <GitFork className="h-3 w-3" /> {repo.forks_count.toLocaleString()}
          </span>
          <span className="flex items-center gap-1 text-green-400">
            <GitCommitHorizontal className="h-3 w-3" /> {repo.activity_score}
          </span>
        </span>
      </div>
      <p className="mt-1.5 text-sm text-zinc-300">{repo.description || "(no description)"}</p>
      {repo.translation && repo.need_translation && (
        <p className="mt-1 text-sm italic text-emerald-400">→ {repo.translation}</p>
      )}
      {repo.recent_commits[0] && (
        <p className="mt-2 truncate text-xs text-zinc-500">
          latest: {repo.recent_commits[0].message} - {repo.recent_commits[0].author} (
          {repo.recent_commits[0].date})
        </p>
      )}
    </Link>
  );
}
