import {
  type DigestResult,
  type GraphNode,
  type MirrorResult,
  type Mover,
  type WatchEntry,
  api,
} from "@/lib/api";
import { GitFork, Globe, ListVideo, RefreshCw, Share2, Star, Trash2 } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

function MoverList({ movers, empty }: { movers: Mover[]; empty: string }) {
  if (movers.length === 0) return <p className="text-sm text-zinc-500">{empty}</p>;
  return (
    <ul className="space-y-1.5">
      {movers.map((m) => (
        <li key={m.full_name} className="flex flex-wrap items-center gap-2 text-sm">
          <span className="font-mono text-amber-400">{m.full_name}</span>
          <span className={m.delta >= 0 ? "text-green-400" : "text-red-400"}>
            {m.delta >= 0 ? "+" : ""}
            {m.delta.toFixed(2)}
          </span>
          <span className="text-xs text-zinc-500">
            {m.current_score.toFixed(1)} vs {m.prev_score.toFixed(1)} · stars{" "}
            {m.stars_delta >= 0 ? "+" : ""}
            {m.stars_delta} · forks {m.forks_delta >= 0 ? "+" : ""}
            {m.forks_delta}
          </span>
        </li>
      ))}
    </ul>
  );
}

export default function Ecosystem() {
  const [movers, setMovers] = useState<Mover[]>([]);
  const [moversEmpty, setMoversEmpty] = useState("Loading movers...");
  const [watchlist, setWatchlist] = useState<WatchEntry[]>([]);
  const [newRepo, setNewRepo] = useState("");
  const [watchMsg, setWatchMsg] = useState("");
  const [checking, setChecking] = useState(false);
  const [digest, setDigest] = useState<DigestResult | null>(null);
  const [digestLoading, setDigestLoading] = useState(false);
  const [graph, setGraph] = useState<{
    nodes: GraphNode[];
    edges: { source: string; target: string; relation: string }[];
  } | null>(null);
  const [graphMsg, setGraphMsg] = useState("");
  const [mirror, setMirror] = useState<MirrorResult | null>(null);
  const [mirrorRepo, setMirrorRepo] = useState("");
  const [mirrorLoading, setMirrorLoading] = useState(false);

  const loadWatchlist = useCallback(async () => {
    try {
      const res = await api<{ entries: WatchEntry[] }>("/api/watchlist");
      setWatchlist(res.entries);
    } catch {
      setWatchlist([]);
    }
  }, []);

  const loadMovers = useCallback(async () => {
    try {
      const res = await api<{ movers: Mover[]; note: string }>("/api/explore/momentum");
      setMovers(res.movers);
      if (res.movers.length === 0)
        setMoversEmpty(
          "No momentum history yet - run the radar on separate days to build baselines.",
        );
    } catch {
      setMoversEmpty("Failed to load movers.");
    }
  }, []);

  useEffect(() => {
    void loadMovers();
    void loadWatchlist();
  }, [loadMovers, loadWatchlist]);

  const addRepo = async () => {
    const name = newRepo.trim();
    if (!name) return;
    try {
      await api<{ success: boolean }>("/api/watchlist", {
        method: "POST",
        body: JSON.stringify({ full_name: name }),
      });
      setWatchMsg(`Watching ${name}`);
      setNewRepo("");
      await loadWatchlist();
    } catch (e) {
      setWatchMsg(e instanceof Error ? e.message : "add failed");
    }
  };

  const removeRepo = async (name: string) => {
    await api<{ removed: boolean }>(`/api/watchlist/${encodeURIComponent(name)}`, {
      method: "DELETE",
    });
    await loadWatchlist();
  };

  const runCheck = async () => {
    setChecking(true);
    try {
      const res = await api<{
        entries: { full_name: string; status: string; new_commits: number }[];
        message: string;
      }>("/api/watchlist/check", { method: "POST" });
      setWatchMsg(
        res.message + (res.entries.some((e) => e.status === "changed") ? " - changes found" : ""),
      );
    } catch (e) {
      setWatchMsg(e instanceof Error ? e.message : "check failed");
    } finally {
      setChecking(false);
    }
  };

  const generateDigest = async () => {
    setDigestLoading(true);
    try {
      const res = await api<DigestResult>("/api/ecosystem/digest?days=7");
      setDigest(res);
    } catch (e) {
      setDigestMsg(e instanceof Error ? e.message : "digest failed");
    } finally {
      setDigestLoading(false);
    }
  };
  const [digestMsg, setDigestMsg] = useState("");

  const loadGraph = async () => {
    setGraphMsg("Loading...");
    try {
      const res = await api<{
        nodes: GraphNode[];
        edges: { source: string; target: string; relation: string }[];
      }>("/api/ecosystem/graph?scope=seeds");
      setGraph(res);
      setGraphMsg(`${res.nodes.length} nodes, ${res.edges.length} edges`);
    } catch (e) {
      setGraphMsg(e instanceof Error ? e.message : "graph failed");
    }
  };

  const runMirror = async () => {
    const name = mirrorRepo.trim().replace(/^\//, "").replace(/\/$/, "");
    const [owner, repo] = name.split("/");
    if (!owner || !repo) {
      setMirror({ success: false, on_github: false, owner: "", repo: "", error: "use owner/repo" });
      return;
    }
    setMirrorLoading(true);
    try {
      const res = await api<MirrorResult>(`/api/ecosystem/mirror/${owner}/${repo}`);
      setMirror(res);
    } catch (e) {
      setMirror({
        success: false,
        on_github: false,
        owner,
        repo,
        error: e instanceof Error ? e.message : "mirror failed",
      });
    } finally {
      setMirrorLoading(false);
    }
  };

  const orgGroups = new Map<string, string[]>();
  for (const e of graph?.edges ?? []) {
    if (e.relation !== "owns") continue;
    const list = orgGroups.get(e.source) ?? [];
    list.push(e.target);
    orgGroups.set(e.source, list);
  }

  return (
    <div data-testid="ecosystem-page" className="mx-auto max-w-5xl space-y-6">
      <div>
        <h2 className="flex items-center gap-2 text-xl font-bold">
          <Globe className="h-5 w-5 text-amber-500" /> Ecosystem
        </h2>
        <p className="mt-1 text-sm text-zinc-400">
          What is changing in Chinese OSS: momentum, watchlist, weekly digest, ecosystem graph and
          GitHub mirror comparison.
        </p>
      </div>

      <section className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-5">
        <h3 className="flex items-center gap-2 text-sm font-semibold text-amber-400">
          <Share2 className="h-4 w-4" /> Momentum (7d activity delta)
        </h3>
        <div className="mt-3">
          <MoverList movers={movers.slice(0, 10)} empty={moversEmpty} />
        </div>
      </section>

      <section className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-5">
        <h3 className="flex items-center gap-2 text-sm font-semibold text-amber-400">
          <ListVideo className="h-4 w-4" /> Watchlist
        </h3>
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <input
            data-testid="watchlist-input"
            value={newRepo}
            onChange={(e) => setNewRepo(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && void addRepo()}
            placeholder="owner/repo e.g. dromara/hutool"
            className="w-64 rounded border border-zinc-700 bg-zinc-800 px-3 py-1.5 text-sm text-zinc-100 placeholder-zinc-500"
          />
          <button
            type="button"
            data-testid="watchlist-add"
            onClick={() => void addRepo()}
            className="rounded bg-amber-500 px-3 py-1.5 text-sm font-semibold text-zinc-950 hover:bg-amber-400"
          >
            Watch
          </button>
          <button
            type="button"
            data-testid="watchlist-check"
            onClick={() => void runCheck()}
            disabled={checking || watchlist.length === 0}
            className="flex items-center gap-1.5 rounded border border-zinc-700 px-3 py-1.5 text-sm text-zinc-300 hover:text-amber-400 disabled:opacity-40"
          >
            <RefreshCw className="h-3.5 w-3.5" /> Check
          </button>
        </div>
        {watchMsg && <p className="mt-2 text-xs text-zinc-400">{watchMsg}</p>}
        <ul className="mt-3 space-y-1.5">
          {watchlist.map((w) => (
            <li
              key={w.full_name}
              data-testid="watchlist-entry"
              className="flex items-center gap-2 text-sm"
            >
              <span className="text-zinc-200">{w.full_name}</span>
              {w.min_activity !== null && w.min_activity !== undefined && (
                <span className="text-xs text-zinc-500">min_activity {w.min_activity}</span>
              )}
              <button
                type="button"
                data-testid="watchlist-remove"
                onClick={() => void removeRepo(w.full_name)}
                className="ml-auto text-zinc-500 hover:text-red-400"
                title="Remove"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </li>
          ))}
          {watchlist.length === 0 && (
            <li className="text-sm text-zinc-500">Nothing watched yet.</li>
          )}
        </ul>
      </section>

      <section className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-5">
        <h3 className="text-sm font-semibold text-amber-400">Weekly digest (last 7 days)</h3>
        <button
          type="button"
          data-testid="digest-generate"
          onClick={() => void generateDigest()}
          disabled={digestLoading}
          className="mt-3 rounded bg-amber-500 px-3 py-1.5 text-sm font-semibold text-zinc-950 hover:bg-amber-400 disabled:opacity-40"
        >
          {digestLoading ? "Generating..." : "Generate digest"}
        </button>
        {digestMsg && <p className="mt-2 text-xs text-red-400">{digestMsg}</p>}
        {digest && (
          <pre
            data-testid="digest-output"
            className="mt-3 whitespace-pre-wrap rounded-lg border border-zinc-800 bg-black/50 p-3 font-mono text-xs leading-relaxed text-zinc-300"
          >
            {digest.narrative}
          </pre>
        )}
      </section>

      <section className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-5">
        <h3 className="flex items-center gap-2 text-sm font-semibold text-amber-400">
          <GitFork className="h-4 w-4" /> Ecosystem graph (seed orgs & fork families)
        </h3>
        <button
          type="button"
          data-testid="graph-load"
          onClick={() => void loadGraph()}
          className="mt-3 rounded border border-zinc-700 px-3 py-1.5 text-sm text-zinc-300 hover:text-amber-400"
        >
          Load graph
        </button>
        {graphMsg && <p className="mt-2 text-xs text-zinc-400">{graphMsg}</p>}
        {graph && (
          <div className="mt-3 grid gap-3 md:grid-cols-2">
            {[...orgGroups.entries()].map(([org, repos]) => (
              <div key={org} data-testid="graph-org" className="rounded border border-zinc-800 p-3">
                <div className="text-sm font-semibold text-amber-400">{org}</div>
                <ul className="mt-1 space-y-0.5 text-xs text-zinc-400">
                  {repos.map((r) => (
                    <li key={r}>{r}</li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        )}
      </section>

      <section className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-5">
        <h3 className="flex items-center gap-2 text-sm font-semibold text-amber-400">
          <Star className="h-4 w-4" /> GitHub mirror compare
        </h3>
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <input
            data-testid="mirror-input"
            value={mirrorRepo}
            onChange={(e) => setMirrorRepo(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && void runMirror()}
            placeholder="owner/repo"
            className="w-64 rounded border border-zinc-700 bg-zinc-800 px-3 py-1.5 text-sm text-zinc-100 placeholder-zinc-500"
          />
          <button
            type="button"
            data-testid="mirror-run"
            onClick={() => void runMirror()}
            disabled={mirrorLoading}
            className="rounded bg-amber-500 px-3 py-1.5 text-sm font-semibold text-zinc-950 hover:bg-amber-400 disabled:opacity-40"
          >
            Compare
          </button>
        </div>
        {mirror && (
          <div className="mt-3 text-sm text-zinc-300" data-testid="mirror-result">
            {mirror.error ? (
              <p className="text-red-400">{mirror.error}</p>
            ) : !mirror.on_github ? (
              <p>{mirror.note}</p>
            ) : (
              <div className="space-y-1">
                <p>
                  <span className="text-amber-400">
                    {mirror.owner}/{mirror.repo}
                  </span>{" "}
                  is on both platforms
                </p>
                <p className="text-xs text-zinc-400">
                  GitHub ★ {mirror.github?.stargazers_count ?? "?"} · forks{" "}
                  {mirror.github?.forks_count ?? "?"}
                  {mirror.delta?.stars !== undefined && mirror.delta?.stars !== null && (
                    <>
                      {" "}
                      · Gitee-GitHub star delta{" "}
                      <span className={mirror.delta.stars >= 0 ? "text-green-400" : "text-red-400"}>
                        {mirror.delta.stars >= 0 ? "+" : ""}
                        {mirror.delta.stars}
                      </span>
                    </>
                  )}
                </p>
              </div>
            )}
          </div>
        )}
      </section>
    </div>
  );
}
