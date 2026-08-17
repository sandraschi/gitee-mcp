import { useLlmStore } from "@/store/llm";
import { Download, Eraser, Send, Volume2 } from "lucide-react";
import { useEffect, useRef, useState } from "react";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  ts?: string;
}

const HISTORY_KEY = "gitee-mcp-chat-history";
const PERSONALITY_KEY = "gitee-mcp-chat-personality";

const PERSONALITIES: Record<string, { label: string; prompt: string }> = {
  research: {
    label: "Research Assistant",
    prompt:
      "You are a meticulous research assistant focused on the Chinese open-source ecosystem. Answer concisely with evidence from your tools.",
  },
  reviewer: {
    label: "Expert Reviewer",
    prompt:
      "You are a critical expert reviewer. Evaluate projects, code and claims rigorously; point out weaknesses and risks.",
  },
  summarizer: {
    label: "Quick Summarizer",
    prompt:
      "You are a summarizer. Provide crisp, structured summaries with bullet points and key takeaways only.",
  },
  custom: { label: "Custom", prompt: "" },
};

export default function Chat() {
  const [messages, setMessages] = useState<ChatMessage[]>(() => {
    try {
      const saved = localStorage.getItem(HISTORY_KEY);
      return saved ? (JSON.parse(saved) as ChatMessage[]) : [];
    } catch {
      return [];
    }
  });
  const [input, setInput] = useState("");
  const [thinking, setThinking] = useState(false);
  const [skillName, setSkillName] = useState("gitee-expert");
  const [skillContent, setSkillContent] = useState("");
  const [personalityId, setPersonalityId] = useState(
    () => localStorage.getItem(PERSONALITY_KEY) || "research",
  );
  const [customPrompt, setCustomPrompt] = useState("");
  const [error, setError] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);
  const probe = useLlmStore((s) => s.probe);
  const providers = useLlmStore((s) => s.providers);
  const selectedModel = useLlmStore((s) => s.selectedModel);

  useEffect(() => {
    localStorage.setItem(HISTORY_KEY, JSON.stringify(messages.slice(-100)));
  }, [messages]);

  useEffect(() => {
    void probe();
  }, [probe]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [skills, content] = await Promise.all([
          fetch("http://127.0.0.1:11161/api/skills").then((r) => r.json()),
          fetch("http://127.0.0.1:11161/api/skills/gitee-expert").then((r) => r.text()),
        ]);
        if (cancelled) return;
        setSkillName(skills.skills?.[0]?.name ?? "gitee-expert");
        setSkillContent(content);
      } catch {
        setSkillContent("");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  // biome-ignore lint/correctness/useExhaustiveDependencies: scroll intent is to re-run on message/thinking change
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, thinking]);

  const buildSystemPrompt = () => {
    if (personalityId === "custom")
      return customPrompt || skillContent || "You are a helpful assistant.";
    const role = PERSONALITIES[personalityId]?.prompt ?? "";
    return `${skillContent}\n\n---\n\n## Role\n${role}`;
  };

  const send = async (text?: string) => {
    const content = (text ?? input).trim();
    if (!content || thinking) return;
    setInput("");
    setError("");
    const next = [...messages, { role: "user" as const, content, ts: new Date().toISOString() }];
    setMessages(next);
    setThinking(true);
    try {
      const r = await fetch("http://127.0.0.1:11161/api/llm/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model: selectedModel,
          messages: [{ role: "system", content: buildSystemPrompt() }, ...next],
        }),
      });
      const body = await r.json();
      if (!body.success) throw new Error(body.error || "LLM unreachable");
      setMessages((m) => [
        ...m,
        { role: "assistant", content: body.message, ts: new Date().toISOString() },
      ]);
    } catch (e) {
      setError(e instanceof Error ? e.message : "LLM error");
      setMessages((m) => [
        ...m,
        {
          role: "assistant",
          content: `Error: ${e instanceof Error ? e.message : "LLM error"}`,
          ts: new Date().toISOString(),
        },
      ]);
    } finally {
      setThinking(false);
    }
  };

  const exportChat = () => {
    if (messages.length === 0) return;
    const text = messages.map((m) => `[${m.ts ?? ""}] ${m.role}: ${m.content}`).join("\n\n");
    const blob = new Blob([text], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `gitee-mcp-chat-${new Date().toISOString().slice(0, 19).replace(/[:T]/g, "-")}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const clear = () => {
    setMessages([]);
    localStorage.removeItem(HISTORY_KEY);
  };

  const llmUp = providers.some((p) => p.status === "detected");

  return (
    <div data-testid="chat-page" className="mx-auto flex h-full max-w-4xl flex-col">
      <div
        data-testid="chat-controls"
        className="flex flex-wrap items-center gap-2 border-b border-zinc-800 pb-3"
      >
        <span className="text-xs text-zinc-500">
          skill: <span className="text-amber-400">{skillName}</span>
        </span>
        <select
          data-testid="personality-select"
          value={personalityId}
          onChange={(e) => {
            setPersonalityId(e.target.value);
            localStorage.setItem(PERSONALITY_KEY, e.target.value);
          }}
          className="rounded border border-zinc-700 bg-zinc-800 px-2 py-1 text-sm text-zinc-100"
        >
          {Object.entries(PERSONALITIES).map(([id, p]) => (
            <option key={id} value={id}>
              {p.label}
            </option>
          ))}
        </select>
        <span
          className={`flex items-center gap-1.5 text-xs ${llmUp ? "text-green-400" : "text-red-400"}`}
        >
          <span className="h-2 w-2 rounded-full bg-current" />{" "}
          {llmUp ? "Ollama on :11434" : "No local LLM detected"}
        </span>
        <span className="text-xs text-zinc-500">model: {selectedModel || "default"}</span>
        <div className="ml-auto flex gap-1.5">
          <button
            type="button"
            data-testid="chat-export"
            onClick={exportChat}
            disabled={messages.length === 0}
            title="Export .txt"
            className="rounded border border-zinc-700 p-1.5 text-zinc-400 hover:text-white disabled:opacity-30"
          >
            <Download className="h-4 w-4" />
          </button>
          <button
            type="button"
            data-testid="chat-clear"
            onClick={clear}
            disabled={messages.length === 0}
            title="Clear"
            className="rounded border border-zinc-700 p-1.5 text-zinc-400 hover:text-white disabled:opacity-30"
          >
            <Eraser className="h-4 w-4" />
          </button>
        </div>
      </div>

      {personalityId === "custom" && (
        <textarea
          value={customPrompt}
          onChange={(e) => setCustomPrompt(e.target.value)}
          placeholder="Your custom system prompt (skill content is replaced by this)."
          className="mt-2 h-20 rounded border border-zinc-700 bg-zinc-800 p-2 text-xs text-zinc-100"
        />
      )}

      <div data-testid="chat-messages" className="mt-3 flex-1 space-y-3 overflow-y-auto pb-3">
        {messages.length === 0 && (
          <div data-testid="example-prompts" className="mt-6 grid gap-2 sm:grid-cols-2">
            {[
              "What is humming on Gitee right now?",
              "Summarize the top Java repos from the radar.",
              "Which Chinese open-source projects do low-code?",
              "What did dromara commit this week?",
            ].map((p) => (
              <button
                type="button"
                key={p}
                onClick={() => void send(p)}
                className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-3 text-left text-sm text-zinc-300 hover:border-amber-500/50"
              >
                {p}
              </button>
            ))}
          </div>
        )}
        {messages.map((m, i) => (
          // biome-ignore lint/suspicious/noArrayIndexKey: message list is append-only with timestamps
          <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-[85%] rounded-lg px-3 py-2 text-sm ${
                m.role === "user"
                  ? "bg-amber-500/20 text-zinc-100"
                  : "border border-zinc-800 bg-zinc-900/60 text-zinc-200"
              }`}
            >
              <span className="whitespace-pre-wrap">{m.content}</span>
              {m.role === "assistant" && (
                <button
                  type="button"
                  onClick={() => {
                    if (typeof window === "undefined" || !window.speechSynthesis) return;
                    window.speechSynthesis.cancel();
                    const u = new SpeechSynthesisUtterance(m.content.replace(/[*_`#]/g, ""));
                    window.speechSynthesis.speak(u);
                  }}
                  className="ml-2 inline-flex align-middle text-zinc-500 hover:text-amber-400"
                  title="Speak"
                >
                  <Volume2 className="h-3 w-3" />
                </button>
              )}
            </div>
          </div>
        ))}
        {thinking && <p className="text-sm text-zinc-500">Thinking...</p>}
        <div ref={bottomRef} />
      </div>

      {error && <p className="pb-2 text-xs text-red-400">{error}</p>}

      <div className="flex gap-2 border-t border-zinc-800 pt-3">
        <input
          data-testid="chat-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && void send()}
          placeholder={
            llmUp ? "Ask about the Chinese OSS ecosystem..." : "Start Ollama to enable chat"
          }
          className="flex-1 rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm text-zinc-100 placeholder-zinc-500"
        />
        <button
          type="button"
          data-testid="chat-send"
          onClick={() => void send()}
          disabled={!input.trim() || thinking}
          className="flex items-center gap-1.5 rounded-lg bg-amber-500 px-4 py-2 text-sm font-semibold text-zinc-950 hover:bg-amber-400 disabled:opacity-40"
        >
          <Send className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
