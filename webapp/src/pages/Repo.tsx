import { api } from "@/lib/api";
import {
  ExternalLink,
  FileCode2,
  Folder,
  GitBranch,
  GitCommitHorizontal,
  Languages,
  Star,
} from "lucide-react";
import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import { Link, useParams } from "react-router-dom";

interface RepoDetails {
  full_name: string;
  html_url: string;
  description: string;
  language: string | null;
  stargazers_count: number;
  forks_count: number;
  watchers_count: number;
  open_issues_count: number;
  license: string | null;
  homepage: string;
  pushed_at: string;
  created_at: string;
  default_branch: string;
}

interface Commit {
  sha: string;
  commit: { message: string; author: { name: string; date: string } };
}

interface ContentItem {
  type: "file" | "dir";
  name: string;
  path: string;
}

export default function Repo() {
  const { owner = "", name = "" } = useParams();
  const [details, setDetails] = useState<RepoDetails | null>(null);
  const [readme, setReadme] = useState<string>("");
  const [languages, setLanguages] = useState<{ language: string; percent: number }[]>([]);
  const [commits, setCommits] = useState<Commit[]>([]);
  const [contents, setContents] = useState<ContentItem[]>([]);
  const [branches, setBranches] = useState<string[]>([]);
  const [activeTab, setActiveTab] = useState<"readme" | "commits" | "files" | "branches">("readme");
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    setError("");
    const load = async () => {
      try {
        const [d, l, c, co, b] = await Promise.all([
          api<{ data: RepoDetails }>(`/api/repos/${owner}/${name}/details`),
          api<{ data: { language: string; percent: number }[] }>(
            `/api/repos/${owner}/${name}/languages`,
          ),
          api<{ data: string }>(`/api/repos/${owner}/${name}/readme`),
          api<{ data: Commit[] }>(`/api/repos/${owner}/${name}/commits?limit=10`),
          api<{ data: string[] }>(`/api/repos/${owner}/${name}/branches`),
        ]);
        if (cancelled) return;
        setDetails(d.data);
        setLanguages(l.data);
        setReadme(c.data ?? "");
        setCommits(co.data);
        setBranches(b.data);
        if (c.data) await loadContents("");
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "failed to load repo");
      }
    };
    void load();
    return () => {
      cancelled = true;
    };
  }, [owner, name]);

  const loadContents = async (path: string) => {
    try {
      const res = await api<{ data: ContentItem[] }>(
        `/api/repos/${owner}/${name}/contents${path ? `?path=${encodeURIComponent(path)}` : ""}`,
      );
      setContents(res.data);
    } catch {
      setContents([]);
    }
  };

  if (error) return <p className="text-sm text-red-400">{error}</p>;
  if (!details) return <p className="text-sm text-zinc-500">Loading repo...</p>;

  return (
    <div data-testid="repo-page" className="mx-auto max-w-5xl">
      <div className="flex flex-wrap items-start gap-3">
        <div className="min-w-0 flex-1">
          <Link to="/trending" className="text-xs text-zinc-500 hover:text-amber-400">
            ← radar
          </Link>
          <h2 className="mt-1 text-2xl font-bold text-amber-400">{details.full_name}</h2>
          <p className="mt-1 text-sm text-zinc-300">{details.description || "(no description)"}</p>
          <div className="mt-2 flex flex-wrap gap-3 text-xs text-zinc-400">
            <span className="flex items-center gap-1">
              <Star className="h-3.5 w-3.5 text-amber-500" />{" "}
              {details.stargazers_count.toLocaleString()}
            </span>
            <span>{details.forks_count.toLocaleString()} forks</span>
            <span>{details.watchers_count.toLocaleString()} watchers</span>
            <span>{details.open_issues_count} open issues</span>
            {details.language && (
              <span className="rounded bg-zinc-800 px-1.5 py-0.5 uppercase">
                {details.language}
              </span>
            )}
            {details.license && <span>{details.license}</span>}
            <span>pushed {details.pushed_at}</span>
            <span>default: {details.default_branch}</span>
          </div>
          {details.homepage && (
            <a
              href={details.homepage}
              target="_blank"
              rel="noreferrer"
              className="mt-2 inline-flex items-center gap-1 text-xs text-amber-400 hover:underline"
            >
              <ExternalLink className="h-3 w-3" /> {details.homepage}
            </a>
          )}
        </div>
      </div>

      {languages.length > 0 && (
        <div className="mt-4 rounded-lg border border-zinc-800 bg-zinc-900/50 p-3">
          <div className="mb-1.5 flex items-center gap-1.5 text-xs text-zinc-400">
            <Languages className="h-3.5 w-3.5" /> Languages
          </div>
          <div className="flex h-2 overflow-hidden rounded bg-zinc-800">
            {languages.map((l) => (
              <div
                key={l.language}
                style={{ width: `${l.percent}%` }}
                className="bg-amber-500/70"
                title={`${l.language} ${l.percent}%`}
              />
            ))}
          </div>
          <div className="mt-1.5 flex flex-wrap gap-3 text-[11px] text-zinc-400">
            {languages.slice(0, 8).map((l) => (
              <span key={l.language}>
                {l.language} {l.percent}%
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="mt-4 flex gap-1 border-b border-zinc-800">
        {(
          [
            ["readme", "README"],
            ["commits", "Commits"],
            ["files", "Files"],
            ["branches", "Branches"],
          ] as const
        ).map(([tab, label]) => (
          <button
            type="button"
            key={tab}
            data-testid={`tab-${tab}`}
            onClick={() => {
              setActiveTab(tab);
              if (tab === "files") void loadContents("");
            }}
            className={`border-b-2 px-3 py-1.5 text-sm ${activeTab === tab ? "border-amber-500 text-amber-400" : "border-transparent text-zinc-400 hover:text-white"}`}
          >
            {label}
          </button>
        ))}
      </div>

      <div className="mt-3">
        {activeTab === "readme" && (
          <div className="prose-dark max-w-none rounded-lg border border-zinc-800 bg-zinc-900/50 p-5">
            {readme ? (
              <ReactMarkdown>{readme}</ReactMarkdown>
            ) : (
              <p className="text-sm text-zinc-500">No README.</p>
            )}
          </div>
        )}
        {activeTab === "commits" && (
          <div className="space-y-2">
            {commits.map((c) => (
              <div key={c.sha} className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-3">
                <div className="flex items-center gap-2 text-sm">
                  <GitCommitHorizontal className="h-3.5 w-3.5 text-amber-500" />
                  <span className="truncate">{c.commit.message.split("\n")[0]}</span>
                </div>
                <div className="mt-1 text-xs text-zinc-500">
                  {c.commit.author.name} · {c.commit.author.date}
                </div>
              </div>
            ))}
          </div>
        )}
        {activeTab === "files" && (
          <div className="rounded-lg border border-zinc-800 bg-zinc-900/50">
            {contents.map((item) => (
              <div
                key={item.path}
                className="flex items-center gap-2 border-b border-zinc-800/60 px-3 py-2 text-sm last:border-0"
              >
                {item.type === "dir" ? (
                  <Folder className="h-4 w-4 text-amber-500" />
                ) : (
                  <FileCode2 className="h-4 w-4 text-zinc-500" />
                )}
                <span className="text-zinc-300">{item.name}</span>
              </div>
            ))}
            {contents.length === 0 && (
              <p className="p-3 text-sm text-zinc-500">Empty or inaccessible.</p>
            )}
          </div>
        )}
        {activeTab === "branches" && (
          <div className="space-y-1.5">
            {branches.map((b) => (
              <div
                key={b}
                className="flex items-center gap-2 rounded-lg border border-zinc-800 bg-zinc-900/50 px-3 py-2 text-sm"
              >
                <GitBranch className="h-3.5 w-3.5 text-amber-500" /> {b}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
