# Wrappee: Gitee (gitee.com)

## What Gitee is

**Gitee** (码云) is the largest Chinese-language code hosting and DevOps
platform, operated by OSCHINA.NET. Over 12 million users host open-source
and internal projects there. It is the GitHub of the Chinese ecosystem -
and often the *first* place Chinese projects publish, long before (or
instead of) GitHub.

Notable projects hosted on Gitee:

- **OpenHarmony** (openharmony/openharmony) - Huawei's open-source
  operating system, one of the largest codebases on the platform
- **dromara** ecosystem - hutool (Java utility library, 20k+ stars),
  sa-token, RuoYi-Vue-Plus
- **macrozheng/mall** - the most-starred e-commerce learning project
- **RuoYi-Vue / YunaiV/ruoyi-vue-pro** - the dominant Java admin framework
  family in Chinese companies
- **Apache mirrors** (dubbo, seata, nacos, skywalking...) and Chinese
  enterprise OSS (xxl-job, mybatis-plus, APIJSON, amis)

## API quirks (verified 2026-08-18)

- **v5 API** (`https://gitee.com/api/v5`) - GitHub-style REST, JSON.
  Repo details, README, languages, commits, branches, contents and user
  search work **anonymously**.
- **Rate limits**: ~60 requests/hour anonymous; token raises the budget.
  The server caches 10 minutes to stay inside it.
- **Repo search** (`/search/repositories`) returns `[]` anonymously - it
  requires a personal access token. gitee-mcp reports this honestly.
- **Trending/explore pages** answer HTTP 405 to non-browser clients
  (anti-bot JS challenge). No public trending API exists. gitee-mcp
  computes its own radar from real repo data instead.
- **Timestamps** are +08:00 China Standard Time.
- **Gitee Search SPA** (`search.gitee.com`) is JS-rendered and redirects
  non-browser requests - not scrapeable.

## Community & links

- Homepage: https://gitee.com
- Signup (free): https://gitee.com/signup
- Personal access tokens: https://gitee.com/profile/personal_access_tokens/new
- API v5 docs: https://gitee.com/api/v5
- OSCHINA (parent community): https://www.oschina.net

## Disambiguation

"Gitee" is not to be confused with GitLab.com, GitCode, or any "Gitee"
brand outside code hosting. The platform is Chinese-language-first; most
project descriptions, issues and READMEs are written in Simplified Chinese
- exactly what gitee-mcp's translation layer is for.
