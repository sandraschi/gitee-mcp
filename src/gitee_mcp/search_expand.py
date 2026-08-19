"""Cross-lingual query expansion for Gitee search (F3).

Chinese-OSS descriptions and tags are overwhelmingly Chinese, but users
search in English. expand_query() maps English search terms to their
common Chinese equivalents so "low-code" also finds 低代码 repos. This is
an explicit synonym map (curated, knowledge-sheet data) - a heuristic
applied BEFORE the Gitee call, never a fabricated result.
"""

from __future__ import annotations

# English search term -> Chinese synonym(s). Longest-first matching.
EN_TO_ZH: dict[str, str] = {
    "low-code": "低代码",
    "low code": "低代码",
    "microservices": "微服务",
    "microservice": "微服务",
    "distributed": "分布式",
    "admin panel": "后台管理",
    "admin": "管理后台",
    "management system": "管理系统",
    "permission": "权限",
    "rbac": "权限",
    "auth": "认证",
    "multi-tenant": "多租户",
    "high concurrency": "高并发",
    "high performance": "高性能",
    "big data": "大数据",
    "artificial intelligence": "人工智能",
    "real-time": "实时",
    "monitoring": "监控",
    "logging": "日志",
    "log": "日志",
    "config center": "配置中心",
    "message queue": "消息队列",
    "api doc": "接口文档",
    "visual": "可视化",
    "workflow": "工作流",
    "iot": "物联网",
    "blockchain": "区块链",
    "frontend": "前端",
    "backend": "后端",
    "framework": "框架",
    "component library": "组件库",
    "platform": "平台",
    "open source": "开源",
    "e-commerce": "电商",
    "ecommerce": "电商",
    "payment": "支付",
    "scaffold": "脚手架",
    "enterprise": "企业级",
    "generator": "生成器",
    "cms": "内容管理",
    "blog": "博客",
    "mall": "商城",
    "shop": "商城",
    "sso": "单点登录",
    "oauth": "认证授权",
    "websocket": "长连接",
    "chat": "聊天",
    "ai": "人工智能",
    "llm": "大模型",
    "rag": "知识库",
    "scheduling": "任务调度",
    "job": "任务",
    "notification": "通知",
    "wechat": "微信",
    "weixin": "微信",
    "export": "导出",
    "import": "导入",
    "excel": "表格",
    "report": "报表",
}

_ZHSORT = sorted(EN_TO_ZH.items(), key=lambda kv: -len(kv[0]))


def expand_query(query: str, max_candidates: int = 2) -> list[str]:
    """Return expanded query candidates (original untouched, best-effort).

    Matches whole phrases where possible; falls back to substring token
    mapping. Each candidate replaces the matched English term with its
    Chinese synonym, preserving the rest of the query.
    """
    q = (query or "").strip()
    if not q:
        return []
    low = q.lower()
    candidates: list[str] = []
    seen: set[str] = set()
    for en, zh in _ZHSORT:
        if en not in low:
            continue
        idx = low.find(en)
        cand = q[:idx] + zh + q[idx + len(en) :]
        if cand not in seen and cand != q:
            seen.add(cand)
            candidates.append(cand)
        if len(candidates) >= max_candidates:
            break
    return candidates


def expand_repos_query(query: str) -> str:
    """Expanded query for repo search: original + Chinese synonym appended
    so token-based Gitee search sees both. Falls back to the original."""
    q = (query or "").strip()
    candidates = expand_query(q, max_candidates=1)
    if not candidates:
        return q
    zh = candidates[0]
    if zh in q:
        return q
    return f"{q} {zh}".strip()
