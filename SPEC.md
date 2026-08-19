# gitee-mcp v0.2.0 - Ecosystem Intelligence Feature Spec

**Date**: 2026-08-19
**Status**: Implemented (Tier 1 + Tier 2 + Tier 3-light) / Spec'd (Tier 3-heavy)
**Author**: assfix feature pass

This spec turns the gitee-mcp "what is humming now" tool into a "what is
**changing** in Chinese OSS" intelligence feed. It specs all sixteen feature
ideas from the brainstorm, grouped into three tiers by implementation
tractability. Every tier is honest about what it can and cannot verify
inside this repo.

---

## Guiding principles

1. **No fabricated data.** Every feature derives from real API calls or
   locally persisted observations (radar snapshots, webhook events,
   watchlist state). Where a computation is our own (momentum, digest
   narrative), the methodology is documented and the raw data is returned
   alongside so an agent can verify.
2. **Rate-budget aware.** The anonymous tier is ~60 req/hour. History and
   watchlist features reuse already-fetched radar data; GitHub mirror
   calls are cached; releases and stack fingerprints are cached.
3. **Local-first.** All LLM passes go through the local Ollama /
   OpenAI-compatible endpoint with honest glossary fallbacks - never a
   cloud call, never a fake result.
4. **Data lives under `data/`** (gitignored): `radar_history.jsonl`,
   `watchlist.json`, `corpus.db` (SQLite FTS5), `digest-latest.md`.
   All regenerable.

---

## Tier 1 - Core intelligence (implemented)

### F1. Radar momentum & anomaly detection
- **What**: persist a radar snapshot on every `humming` call (capped at
  30 snapshots, one per repo per snapshot). Each repo entry gains
  `momentum` (delta of `activity_score` vs previous snapshot, signed),
  `momentum_7d` (vs the snapshot ~7 days older), and `surge` (true when
  momentum exceeds a configurable threshold, default +3.0).
- **Surface**: momentum deltas are always attached to `humming` results;
  `gitee_explore(operation="momentum")` ranks by 7d delta. REST
  `GET /api/explore/momentum`.
- **Storage**: `data/radar_history.jsonl` - `{ts, repo: full_name,
  activity_score, stargazers_count, forks_count}` rows. Read at delta
  compute time; append on radar build.

### F2. Tech-stack fingerprint
- **What**: given repo README text + top-level contents names, detect the
  Chinese-OSS tech stack (RuoYi/RBAC admin frameworks, mybatis-plus,
  xxl-job, nacos, dubbo, seata, Spring Boot, Vue2/3, TDesign, Ant Design
  Vue, jeecg, hutool, etc.) via a keyword map with confidence scoring.
- **Surface**: `gitee_repo(operation="stack", owner, repo)`.
  REST `GET /api/repos/{owner}/{repo}/stack`.
- **Storage**: cached 10 min like other repo intel.

### F3. Cross-lingual search expansion
- **What**: expand a query through the glossary before hitting Gitee, so
  "low-code" finds 低代码 repos and "framework" matches 框架 tags.
  Expands English terms -> Chinese synonyms AND Chinese -> English
  (best-effort; Gitee search is token-based, we translate the query).
- **Surface**: `gitee_search(operation="repos"|"users", query=...)`
  transparently expands. REST `GET /api/search/{surface}?q=...` too.
- **Honesty**: expansion is a heuristic; the original query is always
  tried first, expanded as a second query when results are thin.

### F4. Culture notes mode
- **What**: beyond translation, an `explain` mode that answers "why does
  this matter in Chinese OSS" - RuoYi's dominance, Vue-vs-React in CN
  enterprise, the Java admin-framework monoculture, Go rising in ops.
  Uses the local LLM with a built-in knowledge sheet fallback so it works
  offline (honest: fallback is a static fact sheet, marked as such).
- **Surface**: `gitee_translate(operation="explain", text=... | repo=...)`.
  REST `POST /api/translate/explain`.

### F5. Persistent watchlist + change detection + auto-follow
- **What**: user-curated watchlist persisted to `data/watchlist.json`.
  `check` diffs stored commit hashes vs live and reports "what changed
  since last time". Optional `min_activity` threshold per entry: entries
  are flagged when `activity_score` crosses it (auto-follow signal).
- **Surface**: new `gitee_watchlist` portmanteau with ops
  `add / remove / list / check`.
  REST `GET /api/watchlist`, `POST /api/watchlist/{full_name}`,
  `DELETE /api/watchlist/{full_name}`, `POST /api/watchlist/check`.

### F6. Release-notes summarizer
- **What**: fetch `GET /repos/{owner}/{repo}/releases` (cached), pick the
  latest, summarize/translate its body to English via the local LLM with
  glossary fallback.
- **Surface**: `gitee_repo(operation="releases", owner, repo, limit)`.
  REST `GET /api/repos/{owner}/{repo}/releases`.

### F7. Embeddable radar feed
- **What**: RSS 2.0 endpoint generated from the radar - every "humming"
  run produces a feed item per repo. Lets users subscribe to "Chinese
  OSS now" in any feed reader.
- **Surface**: REST `GET /api/feed.xml`. Tool `gitee_ecosystem(op="feed")`
  returns the XML string.

### F8. Prompt templates + radar history param (quick wins)
- New `@mcp.prompt()` templates: `gitee_weekly_brief`,
  `gitee_adoption_assessment`, `gitee_compare_projects`.
- `humming` accepts `history` (0-30) enabling F1 deltas.

---

## Tier 2 - Ecosystem surface (implemented)

### F9. Ecosystem graph (org / fork families)
- **What**: build a graph of orgs, their seed/watchlist repos, and
  fork relationships (repo details `fork` + `parent.full_name` when
  present). Node = org or repo; edge = owns / forked_from.
- **Surface**: `gitee_ecosystem(operation="graph", scope="seeds"|"watchlist")`.
  REST `GET /api/ecosystem/graph`.
- **Honesty**: contributor-overlap edges need the events API (heavy,
  rate-limited) - spec'd as a later extension, not faked.

### F10. Cross-platform mirror intel
- **What**: for a repo, query GitHub's public API for the same
  `owner/repo` and compare stars/forks/velocity/pushed_at. Honest
  "not found on GitHub" when absent (many Chinese projects live only on
  Gitee).
- **Surface**: `gitee_ecosystem(operation="mirror", owner, repo)`.
  REST `GET /api/ecosystem/mirror/{owner}/{repo}`.
- **Storage**: GitHub responses cached 1 hour (unauthenticated GitHub is
  60 req/hr).

### F11. Richer webhook digestion
- **What**: `gitee_webhook(operation="digest", since_hours=24)` groups the
  stored event feed by repo and event type with one-line summaries,
  producing a daily "what happened on my repos" report. Local-only (no
  publish).
- **Surface**: `gitee_webhook` op `digest`. REST `GET /api/webhooks/digest`.

### F12. Star-history curves
- **What**: from persisted radar snapshots, return a repo's observed
  star/forks/activity series. Honest: reflects gitee-mcp's observations,
  not Gitee's full history (Gitee exposes no star-history API).
- **Surface**: `gitee_repo(operation="star_history", owner, repo)`.
  REST `GET /api/repos/{owner}/{repo}/star-history`. Webapp Trending
  cards get a sparkline when data exists.

---

## Tier 3 - Depth / integration

### F13. README corpus search (RAG-lite) - implemented as SQLite FTS5
- **What**: index every README fetched into a local SQLite FTS5 index
  (`data/corpus.db`) and answer "which Chinese project does X?" via
  BM25 keyword search. Honest label: keyword/BM25 retrieval, NOT
  embeddings - suitable for exact-fact lookup ("multi-tenant SaaS",
  "low-code platform"), not open-ended semantics.
- **Surface**: `gitee_corpus(operation="search", query, limit)` and
  `gitee_corpus(operation="ingest", owner, repo)` (reads + indexes the
  README). REST `GET /api/corpus/search?q=`.
- **Extension (spec'd, not implemented)**: real embeddings (LanceDB +
  local model) for open-ended semantic search - requires adding a local
  embedding runtime dependency and is out of scope for this pass.

### F14. Weekly "who's rising" digest - implemented as on-demand tool + recipe
- **What**: `gitee_ecosystem(operation="digest", days=7)` builds a
  narrative from radar history deltas (top movers, surges, drops, new
  arrivals) via the local LLM with a template-based fallback. Writes
  `data/digest-latest.md`. `just digest` recipe for a one-shot local run.
- **Extension (spec'd, not implemented)**: scheduled auto-publish to
  fleet sinks (aiwatcher publish_digest_to_hub / depot) - crosses repo
  boundaries and needs the fleet digest infrastructure running.

### F15. Voice command bus - spec'd only
- **What**: register gitee-mcp tools as a domain member of the fleet
  speech-mcp voice command bus (wake + "what's humming on Gitee" ->
  gitee_explore). Needs `mcp-central-docs/config/voice_command_bus.yaml`
  membership, speech-mcp running, and a live mic test - external
  infrastructure not verifiable from this repo. SPEC ONLY.

### F16. Weekly auto-publish scheduler - spec'd only
- **What**: a `just digest-weekly` scheduled task (like the fleet
  morning digest) that generates + publishes the narrative digest.
  Requires the fleet scheduler + hub publishing client. SPEC ONLY.

---

## Scope summary

| Feature | Status | Why |
|---|---|---|
| F1 momentum/anomaly | implemented | pure local computation |
| F2 stack fingerprint | implemented | README/contents scan + keyword map |
| F3 cross-lingual search | implemented | glossary query expansion |
| F4 culture notes | implemented | local LLM + fact-sheet fallback |
| F5 watchlist | implemented | local JSON persistence |
| F6 release summarizer | implemented | Gitee releases API + LLM |
| F7 RSS feed | implemented | radar -> RSS |
| F8 prompts + history param | implemented | trivial |
| F9 ecosystem graph | implemented | fork/org edges from repo details |
| F10 mirror compare | implemented | GitHub public API (cached) |
| F11 webhook digest | implemented | event feed grouping |
| F12 star-history curves | implemented | snapshot series + sparkline |
| F13 corpus search | implemented (FTS5-lite) | no embedding runtime this pass |
| F14 weekly digest | implemented on-demand | scheduler/publish deferred |
| F15 voice command | spec only | external speech-mcp infra |
| F16 weekly auto-publish | spec only | external scheduler + sinks |

## Honesty & anti-fabrication notes
- Momentum/deltas are computed from our own snapshots; the first run
  reports `momentum: null` (no baseline) rather than inventing 0.
- GitHub mirror returns "not found" for Gitee-only projects - never a
  fabricated comparison.
- Star-history reflects observed data and is labeled as such.
- Corpus search is explicitly keyword/BM25 (FTS5), never marketed as
  embeddings.
- Culture-note fallback is a static fact sheet with an explicit note,
  never passed off as fresh LLM analysis.
