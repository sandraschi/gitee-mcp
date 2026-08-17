import { type Health, api } from "@/lib/api";
import { useLlmStore } from "@/store/llm";
import { CheckCircle2, KeyRound, XCircle } from "lucide-react";
import { useEffect, useState } from "react";

export default function Settings() {
  const [health, setHealth] = useState<Health | null>(null);
  const {
    providers,
    selectedProvider,
    availableModels,
    selectedModel,
    probe,
    setProvider,
    setModel,
  } = useLlmStore();

  useEffect(() => {
    void api<Health>("/api/health")
      .then(setHealth)
      .catch(() => setHealth(null));
  }, []);

  return (
    <div data-testid="settings-page" className="mx-auto max-w-3xl space-y-6">
      <section className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-5">
        <h2 className="text-sm font-semibold text-amber-400">Backend health</h2>
        <div className="mt-3 grid grid-cols-2 gap-3 text-sm md:grid-cols-4">
          <div>
            <div className="text-xs text-zinc-500">Server</div>
            <div data-testid="settings-server">{health?.server ?? "-"}</div>
          </div>
          <div>
            <div className="text-xs text-zinc-500">Version</div>
            <div>{health?.version ?? "-"}</div>
          </div>
          <div>
            <div className="text-xs text-zinc-500">Tools</div>
            <div data-testid="settings-tools">{health?.tool_count ?? "-"}</div>
          </div>
          <div>
            <div className="text-xs text-zinc-500">Uptime (s)</div>
            <div>{health?.uptime_seconds ?? "-"}</div>
          </div>
        </div>
      </section>

      <section className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-5">
        <h2 className="flex items-center gap-2 text-sm font-semibold text-amber-400">
          <KeyRound className="h-4 w-4" /> Gitee account
        </h2>
        <div className="mt-3 flex items-center gap-2 text-sm">
          {health?.configured ? (
            <>
              <CheckCircle2 className="h-4 w-4 text-green-500" />
              <span data-testid="token-state">
                Token configured - full tier (search, top lists)
              </span>
            </>
          ) : (
            <>
              <XCircle className="h-4 w-4 text-red-500" />
              <span data-testid="token-state">Anonymous tier - repo search locked</span>
            </>
          )}
        </div>
        <p className="mt-2 text-xs text-zinc-500">
          Set <code className="rounded bg-zinc-800 px-1">GITEE_TOKEN</code> in the repo{" "}
          <code className="rounded bg-zinc-800 px-1">.env</code> - free at{" "}
          <a
            className="text-amber-400 hover:underline"
            href="https://gitee.com/profile/personal_access_tokens/new"
            target="_blank"
            rel="noreferrer"
          >
            gitee.com/profile/personal_access_tokens
          </a>
          . Anonymous works (~60 req/hour, cached).
        </p>
      </section>

      <section className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-5">
        <h2 className="text-sm font-semibold text-amber-400">Local intelligence</h2>
        <div className="mt-3 space-y-2">
          {providers.length === 0 && <p className="text-xs text-zinc-500">Probing providers...</p>}
          {providers.map((p) => (
            <div
              key={p.name}
              className="flex items-center gap-2 text-sm"
              data-testid={`provider-${p.name}`}
            >
              {p.status === "detected" ? (
                <CheckCircle2 className="h-4 w-4 text-green-500" />
              ) : (
                <XCircle className="h-4 w-4 text-zinc-600" />
              )}
              <span className="w-28 capitalize">{p.name}</span>
              <span className="text-xs text-zinc-500">:{p.port ?? "custom"}</span>
              <span className={p.status === "detected" ? "text-green-400" : "text-zinc-500"}>
                {p.status === "detected" ? "Detected" : "Not found"}
              </span>
            </div>
          ))}
        </div>
        {providers.length > 0 && (
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            <label className="text-xs text-zinc-400">
              Provider
              <select
                data-testid="llm-provider-select"
                value={selectedProvider}
                onChange={(e) => void setProvider(e.target.value)}
                className="mt-1 w-full rounded border border-zinc-700 bg-zinc-800 px-2 py-1.5 text-sm text-zinc-100"
              >
                {providers.map((p) => (
                  <option key={p.name} value={p.name}>
                    {p.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="text-xs text-zinc-400">
              Model
              <select
                data-testid="llm-model-select"
                value={selectedModel}
                onChange={(e) => setModel(e.target.value)}
                className="mt-1 w-full rounded border border-zinc-700 bg-zinc-800 px-2 py-1.5 text-sm text-zinc-100"
              >
                {availableModels.length === 0 && <option value="">(no models)</option>}
                {availableModels.map((m) => (
                  <option key={m} value={m}>
                    {m}
                  </option>
                ))}
              </select>
            </label>
          </div>
        )}
        <button
          type="button"
          onClick={() => void probe()}
          className="mt-4 rounded border border-zinc-700 px-3 py-1 text-xs text-zinc-300 hover:text-amber-400"
        >
          Re-probe providers
        </button>
      </section>

      <section className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-5">
        <h2 className="text-sm font-semibold text-amber-400">Rate limit (anonymous tier)</h2>
        <div className="mt-2 text-sm text-zinc-300">
          Gitee anonymous budget is 60 requests/hour. Responses are cached 10 minutes.
        </div>
      </section>
    </div>
  );
}
