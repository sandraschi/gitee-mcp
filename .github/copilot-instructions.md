# GitHub Copilot instructions - gitee-mcp

## Gitee MCP

Bridge to Gitee (gitee.com), China's largest Chinese-language code hosting
platform: live activity radar, repo intel, user/repo search and zh->en
translation via your local LLM.

**Before starting work:**
1. Check what is humming: gitee_explore(operation="humming", limit=10)
2. Check status/tier: show_gitee_status_card() or gitee_help()

**At end of work, save insights:**
- Offer a watchlist of interesting repos you found (radar + repo commits)
- Respect the anonymous budget (~60 req/hour) - cache-aware, small limits

Tools: gitee_explore, gitee_repo, gitee_search, gitee_translate,
gitee_webhook, gitee_help, show_gitee_humming_card, show_gitee_status_card.
