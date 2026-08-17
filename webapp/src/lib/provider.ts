/** Local LLM provider probing (Ollama / LM Studio / custom) per SOTA webapp standard. */

export interface Provider {
  name: string;
  base: string;
  port: number | null;
  status: "probing" | "detected" | "not_found";
}

export interface DiscoverResult {
  providers: Provider[];
  selected_provider: string;
  default_model: string;
}

export async function discoverProviders(): Promise<DiscoverResult> {
  try {
    const r = await fetch("http://127.0.0.1:11161/api/llm/discover");
    if (!r.ok) return { providers: [], selected_provider: "", default_model: "" };
    return (await r.json()) as DiscoverResult;
  } catch {
    return { providers: [], selected_provider: "", default_model: "" };
  }
}
