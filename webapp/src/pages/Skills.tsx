import { BookOpen } from "lucide-react";
import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";

interface Skill {
  name: string;
  uri: string;
  description: string;
}

export default function Skills() {
  const [skills, setSkills] = useState<Skill[]>([]);
  const [selected, setSelected] = useState("");
  const [content, setContent] = useState("");

  useEffect(() => {
    void fetch("http://127.0.0.1:11161/api/skills")
      .then((r) => r.json())
      .then((b) => {
        setSkills(b.skills ?? []);
        if (b.skills?.[0]) setSelected(b.skills[0].name);
      })
      .catch(() => setSkills([]));
  }, []);

  useEffect(() => {
    if (!selected) return;
    void fetch(`http://127.0.0.1:11161/api/skills/${selected}`)
      .then((r) => r.text())
      .then(setContent)
      .catch(() => setContent(""));
  }, [selected]);

  return (
    <div
      data-testid="skills-page"
      className="mx-auto grid max-w-5xl gap-4 md:grid-cols-[240px_1fr]"
    >
      <div>
        <h2 className="flex items-center gap-2 text-lg font-bold">
          <BookOpen className="h-5 w-5 text-amber-500" /> Skills
        </h2>
        <div className="mt-3 space-y-1.5">
          {skills.map((s) => (
            <button
              type="button"
              key={s.name}
              data-testid={`skill-${s.name}`}
              onClick={() => setSelected(s.name)}
              className={`block w-full rounded-lg border px-3 py-2 text-left text-sm ${
                selected === s.name
                  ? "border-amber-500/60 bg-amber-500/10 text-amber-400"
                  : "border-zinc-800 bg-zinc-900/50 text-zinc-300 hover:border-zinc-700"
              }`}
            >
              {s.name}
              <span className="block text-[11px] text-zinc-500">{s.description}</span>
            </button>
          ))}
        </div>
      </div>
      <div className="prose-dark min-h-[60vh] rounded-lg border border-zinc-800 bg-zinc-900/50 p-5">
        <ReactMarkdown>{content}</ReactMarkdown>
      </div>
    </div>
  );
}
