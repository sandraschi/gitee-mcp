# Configuration

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GITEE_TOKEN` | *(empty)* | Gitee personal access token. Anonymous tier works without it; token tier unlocks repo search, top-starred lists and stargazers. Free: `gitee.com/profile/personal_access_tokens/new` |
| `GITEE_API_BASE` | `https://gitee.com/api/v5` | Gitee v5 API base URL |
| `GITEE_WEBHOOK_SECRET` | *(empty)* | Secret checked against the `X-Gitee-Token` header on `POST /api/webhooks/gitee`. Empty = no check |
| `GITEE_LLM_BASE_URL` | `http://127.0.0.1:11434/v1` | OpenAI-compatible LLM base for translation + chat (Ollama default) |
| `GITEE_LLM_MODEL` | `qwen2.5:7b` | Model used for translation and chat completion |
| `GITEE_CACHE_TTL` | `600` | Response cache TTL in seconds (protects the anonymous rate budget) |
| `GITEE_SEED_REPOS` | *(curated list)* | Comma-separated `owner/repo` seeds for the humming radar |
| `GITEE_BACKEND_PORT` | `11161` | Backend REST/MCP port (fleet registry) |
| `GITEE_FRONTEND_PORT` | `11162` | Webapp dev port (fleet registry) |

## Default seed repos

```
openharmony/openharmony, RuoYi-Vue/RuoYi-Vue, dromara/hutool,
dromara/sa-token, dromara/RuoYi-Vue-Plus, apache/dubbo, seata/seata,
JPressProjects/jpress, lyswhut/lx-music-desktop, SnailClimb/JavaGuide,
macrozheng/mall, xuxueli/xxl-job, YunaiV/ruoyi-vue-pro, alibaba/nacos,
spring-projects/spring-boot, mybatis/mybatis-3, apache/skywalking,
apache/shardingsphere, apache/rocketmq, doocs/advanced-java,
halo-dev/halo, baomidou/mybatis-plus, Tencent/APIJSON,
pandao/editor.md, baidu/amis
```

## Setting Variables

### Claude Desktop (Option C)

In `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "gitee-mcp": {
      "command": "uv",
      "args": ["--directory", "C:\\path\\to\\gitee-mcp", "run", "python", "-m", "gitee_mcp.server"],
      "env": {
        "GITEE_TOKEN": "your-token",
        "GITEE_LLM_MODEL": "qwen2.5:7b"
      }
    }
  }
}
```

### Webapp / start.bat (Option D)

Copy `.env.example` to `.env` in the repo root and edit. One file, one
source of truth - the server loads it at startup.

## Webhooks

To receive push/star/fork events:

1. In Gitee: repo -> Management -> Web Hooks -> Add Web Hook
2. URL: `http://127.0.0.1:11161/api/webhooks/gitee`
3. Set a secret and mirror it as `GITEE_WEBHOOK_SECRET`
4. Pick events (Push, Tag Push, Star, Fork, Pull Request)

Events are appended to `data/webhook_events.jsonl` and visible via
`gitee_webhook(operation="list")` and the webapp Inbox page.
