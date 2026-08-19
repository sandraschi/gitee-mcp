import { BookOpen, Github, HelpCircle, Server, Terminal } from "lucide-react";

const SECTIONS = [
  {
    icon: Server,
    title: "Architecture",
    items: [
      "Backend: FastMCP 3.4.4 + FastAPI on 127.0.0.1:11161 (REST /api/*, MCP streamable at /mcp)",
      "Frontend: React + Vite + Tailwind (dark) on 127.0.0.1:11162",
      "Dual transport: stdio by default; HTTP when MCP_PORT/PORT is set",
      "Gitee v5 API with anonymous + token tiers; responses cached 10 min (data/cache)",
    ],
  },
  {
    icon: BookOpen,
    title: "Data sources",
    items: [
      "Repos/readme/languages/commits/branches/contents: gitee.com/api/v5 (anonymous)",
      "User search: v5 /search/users (anonymous)",
      "Repo search + top-starred: v5 /search/repositories (needs GITEE_TOKEN)",
      "Humming radar: computed from live seed-repo activity (Gitee has no public trending API)",
    ],
  },
  {
    icon: Terminal,
    title: "Environment",
    items: [
      "GITEE_TOKEN - free personal access token, unlocks search tier",
      "GITEE_LLM_BASE_URL - Ollama default http://127.0.0.1:11434/v1",
      "GITEE_LLM_MODEL - translation model, default qwen2.5:7b",
      "GITEE_SEED_REPOS - comma-separated radar seeds",
      "GITEE_WEBHOOK_SECRET - webhook receiver secret",
    ],
  },
  {
    icon: HelpCircle,
    title: "Troubleshooting",
    items: [
      "Rate limit: wait for the hourly window or set a token",
      "auth_required: set GITEE_TOKEN, restart the server",
      "Translation gloss only: start Ollama (ollama serve; ollama pull qwen2.5:7b)",
      "Webapp offline: backend on 11161 must be up (start.bat starts both)",
      "Full guide: docs/TROUBLESHOOTING.md",
    ],
  },
];

export default function Help() {
  return (
    <div data-testid="help-page" className="mx-auto max-w-4xl">
      <h2 className="text-xl font-bold">Help</h2>
      <p className="mt-1 text-sm text-zinc-400">
        Gitee MCP - bridge to China's largest open-source platform. Anonymous tier works out of the
        box; a free token unlocks search.
      </p>
      <div className="mt-6 grid gap-4 md:grid-cols-2">
        {SECTIONS.map((s) => (
          <div
            key={s.title}
            data-testid={`help-section-${s.title.toLowerCase().replace(/\s+/g, "-")}`}
            className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-4"
          >
            <h3 className="flex items-center gap-2 text-sm font-semibold text-amber-400">
              <s.icon className="h-4 w-4" /> {s.title}
            </h3>
            <ul className="mt-2 space-y-1.5 text-xs leading-relaxed text-zinc-400">
              {s.items.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
        ))}
      </div>
      <a
        href="https://github.com/sandraschi/gitee-mcp"
        target="_blank"
        rel="noreferrer"
        data-testid="help-repo-link"
        className="mt-6 inline-flex items-center gap-1.5 text-sm text-amber-400 hover:underline"
      >
        <Github className="h-4 w-4" /> github.com/sandraschi/gitee-mcp
      </a>
    </div>
  );
}
