import type { Health } from "@/lib/api";
import { API_BASE } from "@/lib/api";
import { useZoom } from "@/lib/use-zoom";
import {
  Activity,
  BookOpen,
  ChevronLeft,
  ChevronRight,
  Code2,
  Globe,
  HelpCircle,
  Inbox,
  LayoutDashboard,
  MessageSquare,
  Search,
  Settings,
  Terminal,
  TrendingUp,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";

const NAV = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/trending", label: "Trending", icon: TrendingUp },
  { to: "/search", label: "Search", icon: Search },
  { to: "/ecosystem", label: "Ecosystem", icon: Globe },
  { to: "/chat", label: "Chat", icon: MessageSquare },
  { to: "/skills", label: "Skills", icon: BookOpen },
  { to: "/inbox", label: "Inbox", icon: Inbox },
  { to: "/api-docs", label: "API Docs", icon: Code2 },
  { to: "/settings", label: "Settings", icon: Settings },
  { to: "/logs", label: "Logs", icon: Terminal },
  { to: "/help", label: "Help", icon: HelpCircle },
];

async function checkHealth(): Promise<Health | null> {
  try {
    const r = await fetch(`${API_BASE}/api/health`);
    if (!r.ok) return null;
    return (await r.json()) as Health;
  } catch {
    return null;
  }
}

export default function Layout() {
  const [collapsed, setCollapsed] = useState(false);
  const [backend, setBackend] = useState<Health | null>(null);
  const [backendOk, setBackendOk] = useState<boolean | null>(null);
  const [tier, setTier] = useState("anonymous");
  const location = useLocation();
  useZoom();

  const refresh = useCallback(async () => {
    const h = await checkHealth();
    setBackend(h);
    setBackendOk(!!h);
    if (h) setTier(h.tier);
  }, []);

  useEffect(() => {
    void refresh();
    const interval = setInterval(refresh, 15000);
    return () => clearInterval(interval);
  }, [refresh]);

  useEffect(() => {
    let unlisten: (() => void) | undefined;
    (async () => {
      try {
        const { listen } = await import("@tauri-apps/api/event");
        unlisten = await listen<string>("backend-status", (event) => {
          if (event.payload === "ready") void refresh();
          else if (typeof event.payload === "string" && event.payload.startsWith("error:"))
            setBackendOk(false);
        });
      } catch {
        /* not in Tauri - HTTP polling handles it */
      }
    })();
    return () => {
      if (unlisten) unlisten();
    };
  }, [refresh]);

  const pageTitle =
    NAV.find((n) => (n.to === "/" ? location.pathname === "/" : location.pathname.startsWith(n.to)))
      ?.label ?? "Gitee MCP";

  return (
    <div className="flex h-screen bg-zinc-950 text-zinc-100">
      <aside
        data-testid="sidebar"
        className={`flex flex-col border-r border-zinc-800 bg-zinc-900/60 backdrop-blur transition-all ${
          collapsed ? "w-16" : "w-56"
        }`}
      >
        <div className="flex items-center gap-2 px-4 py-4">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded bg-red-600 font-bold text-white">
            G
          </div>
          {!collapsed && (
            <div className="min-w-0">
              <div className="truncate text-sm font-semibold">Gitee MCP</div>
              <div className="text-[10px] text-zinc-500">v0.1.0</div>
            </div>
          )}
        </div>
        <button
          type="button"
          onClick={() => setCollapsed((c) => !c)}
          data-testid="sidebar-toggle"
          className="mx-2 mb-2 flex items-center justify-center gap-1 rounded border border-zinc-800 py-1.5 text-zinc-400 hover:text-white"
          title={collapsed ? "Expand" : "Collapse"}
        >
          {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
        </button>
        <nav className="flex-1 space-y-1 px-2">
          {NAV.map((item) => {
            const active =
              item.to === "/" ? location.pathname === "/" : location.pathname.startsWith(item.to);
            return (
              <NavLink
                key={item.to}
                to={item.to}
                aria-label={item.label}
                data-testid={`nav-${item.label.toLowerCase().replace(" ", "-")}`}
                className={`flex items-center gap-2 rounded px-3 py-2 text-sm transition-colors ${
                  active
                    ? "bg-amber-500/15 text-amber-400"
                    : "text-zinc-400 hover:bg-zinc-800 hover:text-white"
                }`}
              >
                <item.icon className="h-4 w-4 shrink-0" />
                {!collapsed && <span className="truncate">{item.label}</span>}
              </NavLink>
            );
          })}
        </nav>
        <div className="border-t border-zinc-800 p-3">
          <div className="flex items-center gap-2">
            <span
              data-testid="backend-dot"
              className={`h-2.5 w-2.5 rounded-full ${
                backendOk === null ? "bg-zinc-500" : backendOk ? "bg-green-500" : "bg-red-500"
              } animate-pulse`}
            />
            <span className="text-xs text-zinc-400">
              {backendOk === null ? "Connecting..." : backendOk ? "Connected" : "Offline"}
            </span>
          </div>
          <div className="mt-1 text-[10px] uppercase tracking-wide text-zinc-600">
            tier: <span className="text-amber-500">{tier}</span>
          </div>
        </div>
      </aside>

      <div className="flex flex-1 flex-col overflow-hidden">
        <header className="flex items-center justify-between border-b border-zinc-800 bg-zinc-900/40 px-5 py-3">
          <div className="flex items-center gap-2">
            <Activity className="h-4 w-4 text-amber-500" />
            <h1 className="text-sm font-semibold">{pageTitle}</h1>
          </div>
          <div className="flex items-center gap-3 text-xs text-zinc-400">
            {backend && (
              <>
                <span>{backend.version}</span>
                <span>{backend.tool_count} tools</span>
                <span className="rounded bg-zinc-800 px-2 py-0.5">{backend.tier}</span>
              </>
            )}
          </div>
        </header>
        <main className="flex-1 overflow-y-auto p-5">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
