import { type Health, api } from "@/lib/api";
import { BookOpen, Cpu, Gauge, Server, Sparkles, TrendingUp } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

export default function Dashboard() {
  const [health, setHealth] = useState<Health | null>(null);
  const [retry, setRetry] = useState(0);

  // biome-ignore lint/correctness/useExhaustiveDependencies: retry dep intentionally re-triggers the poll
  useEffect(() => {
    let cancelled = false;
    const delays = [1000, 2000, 4000, 8000, 16000];
    let timer: ReturnType<typeof setTimeout>;
    const attempt = async (i: number) => {
      try {
        const h = await api<Health>("/api/health");
        if (!cancelled) setHealth(h);
      } catch {
        if (!cancelled) {
          timer = setTimeout(
            () => void attempt(Math.min(i + 1, delays.length - 1)),
            delays[Math.min(i, delays.length - 1)],
          );
        }
      }
    };
    void attempt(0);
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [retry]);

  const uptime = health ? Math.floor(health.uptime_seconds / 60) : 0;
  const configured = !!health?.configured;

  return (
    <div data-testid="dashboard" className="mx-auto max-w-5xl">
      <section className="rounded-xl border border-zinc-800 bg-gradient-to-br from-zinc-900 to-zinc-950 p-8">
        <h2 className="text-3xl font-bold">
          What is <span className="text-amber-400">humming</span> on Gitee?
        </h2>
        <p className="mt-2 max-w-2xl text-sm text-zinc-400">
          Live radar of China's biggest open-source platform: real commit activity, star and fork
          momentum, Chinese descriptions translated to English by your local LLM.
        </p>
        <div className="mt-5 flex flex-wrap gap-3">
          <Link
            to="/trending"
            data-testid="cta-trending"
            className="flex items-center gap-2 rounded-lg bg-amber-500 px-4 py-2 text-sm font-semibold text-zinc-950 hover:bg-amber-400"
          >
            <TrendingUp className="h-4 w-4" /> Open the radar
          </Link>
          {!configured && (
            <Link
              to="/settings"
              data-testid="onboarding-cue"
              className="flex items-center gap-2 rounded-lg bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-500"
            >
              Complete onboarding - connect Gitee token
            </Link>
          )}
        </div>
      </section>

      <div className="mt-6 grid grid-cols-2 gap-4 md:grid-cols-4">
        <Kpi
          testid="kpi-server"
          icon={<Server className="h-4 w-4" />}
          label="Server"
          value={health?.version ?? "-"}
        />
        <Kpi
          testid="kpi-tools"
          icon={<Sparkles className="h-4 w-4" />}
          label="Tools"
          value={String(health?.tool_count ?? "-")}
        />
        <Kpi
          testid="kpi-tier"
          icon={<Gauge className="h-4 w-4" />}
          label="Tier"
          value={health?.tier === "token" ? "token" : "anonymous"}
          accent={health?.tier === "token"}
        />
        <Kpi
          testid="kpi-uptime"
          icon={<Cpu className="h-4 w-4" />}
          label="Uptime (min)"
          value={String(uptime)}
        />
      </div>

      <div className="mt-6 grid gap-4 md:grid-cols-3">
        <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-4">
          <h3 className="flex items-center gap-2 text-sm font-semibold text-amber-400">
            <BookOpen className="h-4 w-4" /> Radar source
          </h3>
          <p className="mt-2 text-xs leading-relaxed text-zinc-400">
            Gitee has no public trending API. The radar ranks seed repos by live commit recency,
            commit volume and star/forks mass - real data, transparent methodology.
          </p>
        </div>
        <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-4">
          <h3 className="text-sm font-semibold text-amber-400">Translation</h3>
          <p className="mt-2 text-xs leading-relaxed text-zinc-400">
            Chinese descriptions are translated by your local Ollama. No Ollama? A built-in glossary
            glosses common terms - never a fake translation.
          </p>
        </div>
        <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-4">
          <h3 className="text-sm font-semibold text-amber-400">Tiers</h3>
          <p className="mt-2 text-xs leading-relaxed text-zinc-400">
            Anonymous works now (~60 requests/hour, cached). A free Gitee token unlocks repo search,
            top-starred lists and higher limits.
          </p>
        </div>
      </div>

      <button
        type="button"
        onClick={() => setRetry((r) => r + 1)}
        className="mt-4 text-xs text-zinc-500 hover:text-amber-400"
        data-testid="health-retry"
      >
        Retry health check
      </button>
    </div>
  );
}

function Kpi({
  testid,
  icon,
  label,
  value,
  accent = false,
}: { testid: string; icon: React.ReactNode; label: string; value: string; accent?: boolean }) {
  return (
    <div data-testid={testid} className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-4">
      <div
        className={`flex items-center gap-1.5 text-xs ${accent ? "text-green-400" : "text-zinc-500"}`}
      >
        {icon}
        <span>{label}</span>
      </div>
      <div className="mt-1 text-xl font-bold">{value}</div>
    </div>
  );
}
