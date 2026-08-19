import { API_BASE, api } from "@/lib/api";
import { Bell, Trash2 } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

interface WebhookEvent {
  id: string;
  ts: string;
  event: string;
  payload: Record<string, unknown>;
}

export default function Inbox() {
  const [events, setEvents] = useState<WebhookEvent[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api<{ events: WebhookEvent[] }>("/api/webhooks/events?limit=30");
      setEvents(res.events);
    } catch {
      setEvents([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const summarize = (e: WebhookEvent) => {
    const p = (e.payload ?? {}) as {
      repository?: { full_name?: string };
      ref?: string;
      total_commits_count?: number;
      user_name?: string;
      starred_by?: { login?: string };
    };
    const repo = p.repository?.full_name || "unknown repo";
    if (e.event === "Push Hook") {
      const branch = (p.ref || "").split("/").pop() || "?";
      return `Push: ${p.total_commits_count ?? 0} commit(s) to ${repo}@${branch}`;
    }
    if (e.event === "Star Hook") return `Star: ${p.starred_by?.login || "?"} starred ${repo}`;
    return `${e.event}: ${repo}`;
  };

  return (
    <div data-testid="inbox-page" className="mx-auto max-w-4xl">
      <div className="flex items-center gap-2">
        <h2 className="flex items-center gap-2 text-xl font-bold">
          <Bell className="h-5 w-5 text-amber-500" /> Webhook inbox
        </h2>
        <button
          type="button"
          onClick={() => {
            void fetch(`${API_BASE}/api/webhooks/events`, { method: "DELETE" })
              .catch(() => {})
              .then(() => load());
          }}
          data-testid="inbox-clear"
          className="ml-auto flex items-center gap-1.5 rounded border border-zinc-700 px-3 py-1 text-xs text-zinc-400 hover:text-white"
        >
          <Trash2 className="h-3.5 w-3.5" /> Clear
        </button>
      </div>
      <p className="mt-1 text-xs text-zinc-500">
        Push / star / fork events from Gitee repo webhooks hitting POST /api/webhooks/gitee.
      </p>
      {loading && <p className="mt-4 text-sm text-zinc-500">Loading...</p>}
      <div className="mt-4 space-y-2" data-testid="inbox-events">
        {events.map((e) => (
          <div
            key={e.id}
            data-testid="inbox-event"
            className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-3"
          >
            <div className="flex items-center gap-2 text-sm">
              <span className="rounded bg-zinc-800 px-1.5 py-0.5 text-[10px] uppercase text-amber-400">
                {e.event}
              </span>
              <span className="text-zinc-300">{summarize(e)}</span>
              <span className="ml-auto text-xs text-zinc-500">{e.ts}</span>
            </div>
          </div>
        ))}
        {!loading && events.length === 0 && (
          <p className="text-sm text-zinc-500">
            No events yet. Configure a repo webhook pointing at
            http://127.0.0.1:11161/api/webhooks/gitee.
          </p>
        )}
      </div>
    </div>
  );
}
