import { Code2, ExternalLink } from "lucide-react";
import { useEffect, useState } from "react";

const ENDPOINTS = [
  "GET /api/health",
  "GET /api/v1/diagnostics",
  "GET /api/dashboard",
  "GET /api/explore/humming",
  "GET /api/repos/{owner}/{repo}/{surface}",
  "GET /api/search/users",
  "GET /api/search/repos",
  "POST /api/translate",
  "POST /api/webhooks/gitee",
  "POST /api/llm/chat",
  "GET /api/logs",
];

export default function ApiDocs() {
  const [dark, setDark] = useState(true);

  // biome-ignore lint/correctness/useExhaustiveDependencies: dark dep intentionally re-injects theme CSS on toggle
  useEffect(() => {
    const iframe = document.getElementById("swagger-frame") as HTMLIFrameElement | null;
    if (!iframe) return;
    const inject = () => {
      try {
        const doc = iframe.contentDocument;
        if (!doc) return;
        doc.documentElement.style.background = "#09090b";
        const style = doc.createElement("style");
        style.textContent = `
          body { background: #09090b !important; color: #e4e4e7; }
          .swagger-ui .topbar { background: #18181b; }
          .swagger-ui .opblock-summary, .swagger-ui .opblock { background: #18181b; border-color: #3f3f46; }
          .swagger-ui .info .title, .swagger-ui .info p { color: #e4e4e7; }
          .swagger-ui .opblock-summary-method { color: #fff !important; }
          .swagger-ui section.models, .swagger-ui .model-box { background: #18181b; }
        `;
        doc.head.appendChild(style);
      } catch {
        /* cross-origin - fallback to direct link */
      }
    };
    const t = setTimeout(inject, 1200);
    return () => clearTimeout(t);
  }, [dark]);

  return (
    <div data-testid="api-docs-page" className="mx-auto max-w-6xl">
      <div className="flex flex-wrap items-center gap-3">
        <h2 className="flex items-center gap-2 text-xl font-bold">
          <Code2 className="h-5 w-5 text-amber-500" /> API Docs
        </h2>
        <button
          type="button"
          onClick={() => setDark((d) => !d)}
          className="rounded border border-zinc-700 px-2 py-1 text-xs text-zinc-400"
        >
          {dark ? "Dark" : "Light"} theme
        </button>
        <a
          href="http://127.0.0.1:11161/docs"
          target="_blank"
          rel="noreferrer"
          className="ml-auto flex items-center gap-1 rounded bg-amber-500 px-3 py-1 text-xs font-semibold text-zinc-950 hover:bg-amber-400"
        >
          <ExternalLink className="h-3.5 w-3.5" /> Open in browser
        </a>
      </div>

      <div className="mt-3 flex gap-2 overflow-x-auto pb-2">
        {ENDPOINTS.map((e) => (
          <span
            key={e}
            className="shrink-0 rounded bg-zinc-800 px-2 py-1 font-mono text-[10px] text-zinc-400"
          >
            {e}
          </span>
        ))}
      </div>

      <iframe
        id="swagger-frame"
        src="http://127.0.0.1:11161/docs"
        className="h-[70vh] w-full rounded-lg border border-zinc-800 bg-zinc-950"
        title="Swagger UI"
      />
    </div>
  );
}
