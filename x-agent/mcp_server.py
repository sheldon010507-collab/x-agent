"""
mcp_server.py - X-Agent MCP Server

将 X-Agent 所有能力暴露为 MCP (Model Context Protocol) 工具，
供 Claude Desktop/Code 或 OpenClaw MCP 客户端调用。

启动方式：
    stdio:  python mcp_server.py
    sse:    python mcp_server.py sse

工具列表：
    search_trends       多平台热点搜索
    generate_tweet      生成推文草稿 (3 条)
    generate_video      生成视频脚本
    generate_comment    生成智能评论
    score_topic         4 维热点评分 + 风险评估
    post_tweet          发布推文到 X
    comment_tweet       评论指定推文
    like_tweet          点赞推文
    retweet_tweet       转发推文
    get_dms             获取 X 私信列表
    analyze_trends      AI 趋势分析报告
    get_daily_report    每日运营报告
    get_status          系统状态
"""

import json
import logging
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Optional

# 确保 x-agent 模块可导入
sys.path.insert(0, str(Path(__file__).parent))

from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)

mcp = FastMCP(
    "x-agent",
    instructions=(
        "X (Twitter) 全自动运营助手 — 多平台热点搜索、AI 内容生成、"
        "自动发布、DM 监控、日报统计。支持 7 种 Niche 语气风格。"
    ),
    host="0.0.0.0",
    port=8001,
)


# ─── 懒加载单例 ────────────────────────────────────────────────────────

_config = None
_llm_router = None
_researcher = None
_generator = None
_scorer = None
_deduplicator = None


def _get_config():
    global _config
    if _config is None:
        from config import Config
        _config = Config()
    return _config


def _get_llm_router():
    global _llm_router
    if _llm_router is None:
        from modules.llm_router import LLMRouter
        _llm_router = LLMRouter(_get_config())
    return _llm_router


def _get_researcher():
    global _researcher
    if _researcher is None:
        from modules.research import Researcher
        _researcher = Researcher(_get_config())
    return _researcher


def _get_generator(niche: str = "general"):
    global _generator
    if _generator is None or _generator.niche != niche:
        from modules.generator import ContentGenerator
        _generator = ContentGenerator(_get_llm_router(), niche)
    return _generator


def _get_scorer():
    global _scorer
    if _scorer is None:
        from modules.scorer import TrendScorer
        _scorer = TrendScorer()
    return _scorer


def _get_deduplicator():
    global _deduplicator
    if _deduplicator is None:
        from modules.deduplicator import ContentDeduplicator
        _deduplicator = ContentDeduplicator()
    return _deduplicator


# ─── MCP 工具定义 ──────────────────────────────────────────────────────


@mcp.tool()
async def search_trends(
    keyword: str,
    sources: str = "x,tiktok,reddit,hackernews",
    days: int = 7,
    min_score: float = 0,
) -> str:
    """搜索多平台热点趋势。

    数据源支持: x, tiktok, reddit, hackernews, youtube, web
    返回各平台热点列表（标题/作者/互动量/URL），自动去重和评分。

    Args:
        keyword: 搜索关键词
        sources: 数据源列表，逗号分隔
        days: 回溯天数 (1-30)
        min_score: 最低热点分数 (0-100)
    """
    researcher = _get_researcher()
    scorer = _get_scorer()
    deduplicator = _get_deduplicator()

    try:
        raw = await researcher.research_async(niche=keyword, days=days, sources=sources)
    except Exception as e:
        return json.dumps({"error": f"搜索失败: {e}"}, ensure_ascii=False)

    all_items = []
    for platform, data in raw.items():
        if isinstance(data, dict) and "posts" in data:
            for post in data["posts"]:
                post["platform"] = platform
                all_items.append(post)

    scored = []
    for item in all_items:
        try:
            score_info = scorer.score_with_details(item)
            item["score"] = score_info.get("score", 50.0)
        except Exception:
            item["score"] = 50.0
        if item["score"] >= min_score:
            scored.append(item)

    try:
        unique = deduplicator.deduplicate(scored)
    except Exception:
        unique = scored

    unique.sort(key=lambda x: x.get("score", 0), reverse=True)

    return json.dumps(
        {"keyword": keyword, "total": len(unique), "trends": unique[:20]},
        ensure_ascii=False,
        default=str,
    )


@mcp.tool()
async def generate_tweet(
    topic: str,
    niche: str = "general",
    summary: str = "",
) -> str:
    """生成 3 条不同风格的推文草稿。

    风格: Hot Take (犀利观点) / Data (数据引用) / Interactive Poll (互动提问)
    支持 Niche 语气注入: general, ai_tools, crypto, beauty, fitness, humor, adult

    Args:
        topic: 话题关键词
        niche: 内容领域 (影响语气风格)
        summary: 可选的背景信息
    """
    generator = _get_generator(niche)
    try:
        result = await generator.generate_type_a(topic=topic, summary=summary)
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"生成失败: {e}"}, ensure_ascii=False)


@mcp.tool()
async def generate_video(
    topic: str,
    niche: str = "general",
    summary: str = "",
) -> str:
    """生成 30 秒视频脚本（含分镜描述、台词、CTA）。

    Args:
        topic: 话题关键词
        niche: 内容领域
        summary: 可选的背景信息
    """
    generator = _get_generator(niche)
    try:
        result = await generator.generate_type_b(topic=topic, summary=summary)
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"生成失败: {e}"}, ensure_ascii=False)


@mcp.tool()
async def generate_comment(
    post_content: str,
    niche: str = "general",
    author: str = "",
) -> str:
    """生成智能评论（3 条备选），适合回复目标推文。

    评论风格: conversational / analytical / supportive / curious
    自动注入 Niche 语气。

    Args:
        post_content: 目标推文内容
        niche: 内容领域
        author: 原作者（可选）
    """
    generator = _get_generator(niche)
    try:
        result = await generator.generate_comment(post_content=post_content, author=author)
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"生成失败: {e}"}, ensure_ascii=False)


@mcp.tool()
async def score_topic(topic_data: str) -> str:
    """4 维热点评分 + 风险评估。

    评分维度 (总分 0-100):
    - relevance (40%): 话题相关性
    - velocity (30%): 24h 增长速度
    - authority (15%): 来源权威性
    - convergence (15%): 跨平台汇聚度

    风险: risk >= 80 禁止自动发布, 50-80 需人工确认

    Args:
        topic_data: 话题数据 JSON 字符串
    """
    scorer = _get_scorer()
    try:
        data = json.loads(topic_data)
        result = scorer.score_with_details(data)
        return json.dumps(result, ensure_ascii=False, default=str)
    except Exception as e:
        return json.dumps({"error": f"评分失败: {e}"}, ensure_ascii=False)


@mcp.tool()
async def post_tweet(content: str, variant: bool = True) -> str:
    """发布推文到 X（Playwright 浏览器自动化）。

    防封机制: 随机延迟 10-40s, 自动添加 emoji/phrase 变体。
    每日上限 10 条。

    Args:
        content: 推文内容 (280 字符以内)
        variant: 是否应用内容变体（防重复检测）
    """
    try:
        from modules.openclaw_bridge import OpenClawBridge
        bridge = OpenClawBridge()
        bridge.auto_post_enabled = True
        await bridge.initialize()
        result = await bridge.post_content(content=content, apply_variant=variant)
        return json.dumps(result, ensure_ascii=False, default=str)
    except Exception as e:
        return json.dumps({"error": f"发帖失败: {e}"}, ensure_ascii=False)


@mcp.tool()
async def comment_tweet(url: str, content: str) -> str:
    """评论指定推文。

    每日上限 15 条，自动随机延迟。

    Args:
        url: 推文 URL
        content: 评论内容
    """
    try:
        from modules.openclaw_bridge import OpenClawBridge
        bridge = OpenClawBridge()
        bridge.auto_comment_enabled = True
        await bridge.initialize()
        if not bridge.x_automation:
            return json.dumps({"error": "X 自动化未初始化"})
        result = await bridge.x_automation.comment(url, content)
        return json.dumps(result, ensure_ascii=False, default=str)
    except Exception as e:
        return json.dumps({"error": f"评论失败: {e}"}, ensure_ascii=False)


@mcp.tool()
async def like_tweet(url: str) -> str:
    """点赞指定推文。

    每日上限 30 个，延迟 5-15s。

    Args:
        url: 推文 URL
    """
    try:
        from modules.openclaw_bridge import OpenClawBridge
        bridge = OpenClawBridge()
        bridge.auto_like_enabled = True
        await bridge.initialize()
        result = await bridge.like_post(url)
        return json.dumps(result, ensure_ascii=False, default=str)
    except Exception as e:
        return json.dumps({"error": f"点赞失败: {e}"}, ensure_ascii=False)


@mcp.tool()
async def retweet_tweet(url: str, comment: str = "") -> str:
    """转发指定推文（可选引用评论）。

    每日上限 10 条。

    Args:
        url: 推文 URL
        comment: 引用评论（可选）
    """
    try:
        from modules.openclaw_bridge import OpenClawBridge
        bridge = OpenClawBridge()
        bridge.auto_rt_enabled = True
        await bridge.initialize()
        result = await bridge.retweet_post(url, comment or None)
        return json.dumps(result, ensure_ascii=False, default=str)
    except Exception as e:
        return json.dumps({"error": f"转发失败: {e}"}, ensure_ascii=False)


@mcp.tool()
async def get_dms(max_count: int = 20) -> str:
    """获取 X 私信列表（指纹浏览器）。

    使用指纹浏览器伪装，Session Cookie 持久化（20h TTL）。
    返回: 发件人/消息预览/是否未读/时间戳/会话链接

    Args:
        max_count: 最多返回条数
    """
    config = _get_config()
    if not getattr(config, "x_username", None) or not getattr(config, "x_password", None):
        return json.dumps({"error": "需要配置 X_USERNAME 和 X_PASSWORD"})

    try:
        from modules.x_dm_monitor import XDMMonitor
        monitor = XDMMonitor(config)
        dms = await monitor.fetch_dms()
        return json.dumps(
            {"dms": dms[:max_count], "total": len(dms)},
            ensure_ascii=False,
            default=str,
        )
    except Exception as e:
        return json.dumps({"error": f"获取私信失败: {e}"}, ensure_ascii=False)


@mcp.tool()
async def analyze_trends(
    keyword: str,
    sources: str = "x,tiktok,reddit",
) -> str:
    """AI 趋势分析 — 搜索多平台数据 + LLM 生成 Markdown 分析报告。

    报告包含: 趋势概览 / 热度排行 / 平台汇聚性 / 风险预警 / 运营建议

    Args:
        keyword: 分析关键词
        sources: 数据源列表，逗号分隔
    """
    researcher = _get_researcher()
    llm = _get_llm_router()

    try:
        raw = await researcher.research_async(niche=keyword, sources=sources)
    except Exception as e:
        return json.dumps({"error": f"搜索失败: {e}"}, ensure_ascii=False)

    summary_parts = []
    for platform, data in raw.items():
        if isinstance(data, dict) and "posts" in data:
            for post in data["posts"][:5]:
                title = post.get("title") or post.get("text", "")[:80]
                summary_parts.append(f"[{platform}] {title}")

    summary_text = "\n".join(summary_parts) if summary_parts else "暂无搜索数据"

    try:
        report = await llm.chat(
            messages=[
                {
                    "role": "system",
                    "content": "你是专业的社交媒体运营分析师，擅长多平台趋势分析。请输出结构清晰的 Markdown 报告。",
                },
                {
                    "role": "user",
                    "content": f"""请根据以下多平台搜索数据，为关键词「{keyword}」生成一份趋势分析报告（Markdown 格式）。

搜索数据：
{summary_text}

报告要求：
1. 趋势概览（总结当前热度）
2. 热度排行（Top 5 话题）
3. 平台汇聚性（哪些平台同时关注）
4. 风险预警（如有敏感内容）
5. 运营建议（发帖时机、话题切入角度）""",
                },
            ],
        )
        return report
    except Exception as e:
        return json.dumps({"error": f"分析报告生成失败: {e}"}, ensure_ascii=False)


@mcp.tool()
async def get_daily_report(report_date: str = "") -> str:
    """获取每日运营统计报告。

    数据: 发帖数/评论数/点赞数/转发数/最高互动量
    来源: SQLite 本地数据库 或 Supabase 云端

    Args:
        report_date: 日期 YYYY-MM-DD（默认今天）
    """
    config = _get_config()

    try:
        from modules.database import init_database
        db = init_database(config.supabase_url, config.supabase_key)
    except Exception as e:
        return json.dumps({"error": f"数据库连接失败: {e}"}, ensure_ascii=False)

    try:
        target_date = date.fromisoformat(report_date) if report_date else date.today()
    except ValueError:
        return json.dumps({"error": "日期格式错误，请使用 YYYY-MM-DD"})

    try:
        log = db.get_daily_log(target_date)
    except Exception as e:
        return json.dumps({"error": f"获取日报失败: {e}"}, ensure_ascii=False)

    if not log:
        return json.dumps({
            "date": target_date.isoformat(),
            "posts_count": 0,
            "comments_count": 0,
            "likes_count": 0,
            "rt_count": 0,
            "top_engagement": 0,
            "notes": "暂无数据",
        })

    return json.dumps({
        "date": target_date.isoformat(),
        "posts_count": log.get("posts_count", 0),
        "comments_count": log.get("comments_count", 0),
        "likes_count": log.get("likes_count", 0),
        "rt_count": log.get("rt_count", 0),
        "top_engagement": log.get("top_engagement", 0),
        "notes": log.get("notes"),
    }, ensure_ascii=False)


@mcp.tool()
async def get_status() -> str:
    """获取 X-Agent 系统状态 — LLM 供应商/Niche/可用供应商列表"""
    config = _get_config()
    return json.dumps({
        "service": "x-agent-mcp",
        "version": "1.0.0",
        "llm_provider": config.llm.provider,
        "llm_model": config.llm.model,
        "available_providers": config.llm.get_available_providers(),
        "x_configured": bool(getattr(config, "x_username", None)),
        "supabase_configured": bool(config.supabase_url),
        "timestamp": datetime.now().isoformat(),
    }, ensure_ascii=False)


# ─── 启动入口 ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    transport = sys.argv[1] if len(sys.argv) > 1 else "stdio"
    if transport == "sse":
        mcp.run(transport="sse")
    else:
        mcp.run()
