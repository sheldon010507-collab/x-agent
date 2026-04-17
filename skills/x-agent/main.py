#!/usr/bin/env python3
"""
X-Agent CLI - OpenClaw Skill Entry Point

Research / Generation:
  x-agent trends   --niche ai_tools --days 3
  x-agent create   --type a --topic "Bitcoin ETF" --niche crypto
  x-agent score    --input trends.json
  x-agent report

Browser sessions (login required for full data + actions):
  x-agent login    --platform x          # one-time, opens headed browser
  x-agent sessions                        # list login status
  x-agent logout   --platform x

Social actions (uses saved session, headless):
  x-agent post     --platform x --content "Hello"
  x-agent comment  --platform x --url <tweet_url> --content "Nice!"
  x-agent like     --platform x --url <tweet_url>
  x-agent retweet  --platform x --url <tweet_url> [--quote "..."]
  x-agent follow   --platform tiktok --url <profile_url>
  x-agent subscribe --platform youtube --url <channel_url>

Status:
  x-agent status                          # config + storage
  x-agent limits                          # daily action quotas
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path


def get_config():
    from core.config import Config
    return Config()


def _print(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=2, default=str))


# ==================== Research / Generation ====================

def cmd_trends(args):
    config = get_config()
    if args.niche:
        config.set_niche(args.niche)

    from core.research import Researcher

    researcher = Researcher(config, headless=not args.headed)
    result = asyncio.run(
        researcher.research_async(
            niche=config.niche,
            days=args.days,
            sources=args.sources,
            limit_per_source=args.limit,
            query=args.query,
            refines=args.refine or [],
            rank_by=args.rank_by,
        )
    )

    from core.storage import Storage
    Storage(config.data_dir).save_trends(result)

    # 默认输出精简摘要；--full 输出完整 JSON
    if args.full:
        _print(result)
    else:
        _print({
            "niche": result.get("niche"),
            "query": result.get("query"),
            "refines": result.get("refines"),
            "platforms": result.get("platforms", []),
            "total_posts": result.get("total_posts", 0),
            "total_engagement": result.get("total_engagement"),
            "avg_velocity_per_hour": result.get("avg_velocity_per_hour"),
            "engagement_score": result.get("engagement_score"),
            "velocity_24h": result.get("velocity_24h"),
            "risk_score": result.get("risk_score"),
            "summary": result.get("summary"),
            "filter_traces": result.get("filter_traces", []),
            "top_posts": [
                {
                    "platform": p.get("platform"),
                    "title": p.get("title", "")[:120],
                    "url": p.get("url", ""),
                    "engagement": p.get("engagement_score"),
                    "velocity": p.get("velocity_per_hour"),
                    "age_hours": p.get("age_hours"),
                }
                for p in result.get("top_posts", [])[:10]
            ],
        })


def cmd_search(args):
    """在已缓存的研究结果中级联搜索（不重新抓取）"""
    config = get_config()
    from core.research import Researcher

    researcher = Researcher(config)
    queries = ([args.query] if args.query else []) + (args.refine or [])
    if not queries:
        _print({"error": "Provide --query and/or --refine"})
        sys.exit(1)

    result = researcher.search_cached(queries, niche=args.niche, limit=args.limit)

    if args.full:
        _print(result)
    else:
        _print({
            "queries": result.get("queries"),
            "niche_filter": result.get("niche_filter"),
            "total_cached_trends": result.get("total_cached_trends"),
            "filter_trace": result.get("filter_trace"),
            "matched_count": len(result.get("matched_posts", [])),
            "matched_posts": [
                {
                    "platform": p.get("platform"),
                    "title": p.get("title", "")[:120],
                    "url": p.get("url", ""),
                    "engagement": p.get("engagement_score"),
                    "velocity": p.get("velocity_per_hour"),
                }
                for p in result.get("matched_posts", [])[:20]
            ],
        })


def cmd_create(args):
    config = get_config()
    niche = args.niche or config.niche

    from core.llm_router import LLMRouter
    from core.generator import ContentGenerator

    llm = LLMRouter(config)
    generator = ContentGenerator(llm, niche=niche)
    result = asyncio.run(generator.generate(topic=args.topic, content_type=args.type.lower(), niche=niche))

    from core.storage import Storage
    Storage(config.data_dir).save_content(result)
    _print(result)


def cmd_score(args):
    from core.scorer import TrendScorer
    scorer = TrendScorer()

    if args.input:
        path = Path(args.input)
        if not path.exists():
            _print({"error": f"File not found: {args.input}"})
            sys.exit(1)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = json.load(sys.stdin)

    if isinstance(data, list):
        results = [scorer.score_with_details(item) for item in data]
    else:
        results = scorer.score_with_details(data)
    _print(results)


def cmd_report(args):
    config = get_config()
    from core.storage import Storage
    storage = Storage(config.data_dir)
    trends = storage.get_trends(limit=50)
    contents = storage.get_content(limit=50)

    report = {
        "date": args.date or __import__("datetime").date.today().isoformat(),
        "trends_collected": len(trends),
        "content_generated": len(contents),
        "top_niches": _count(trends, "niche"),
        "content_by_type": _count(contents, "type"),
        "recent_trends": [
            {"niche": t.get("niche"), "summary": t.get("summary", "")[:100]}
            for t in trends[-5:]
        ],
    }
    storage.save_report(report)
    _print(report)


def cmd_status(args):
    config = get_config()
    from core.storage import Storage
    from core.browser.session import SessionManager
    _print({
        "config": config.get_status(),
        "storage": Storage(config.data_dir).get_stats(),
        "sessions": SessionManager().list_sessions(),
    })


# ==================== Sessions ====================

def cmd_login(args):
    """打开 headed 浏览器让用户手动登录指定平台"""
    config = get_config()

    from core.browser import BrowserManager
    from core.browser.session import PLATFORM_LOGIN_URLS, SUPPORTED_PLATFORMS

    if args.platform not in SUPPORTED_PLATFORMS:
        _print({"error": f"Unknown platform: {args.platform}", "supported": SUPPORTED_PLATFORMS})
        sys.exit(1)

    mgr = BrowserManager(headless=False)
    login_url = PLATFORM_LOGIN_URLS.get(args.platform)

    print(f"[login] Opening browser for {args.platform}...", file=sys.stderr)
    print(f"[login] Please log in manually. Press ENTER in terminal when done.", file=sys.stderr)

    async def run_login():
        async with mgr.login_session(args.platform) as page:
            await page.goto(login_url)
            print(f"[login] Browser opened: {login_url}", file=sys.stderr)
            # 等用户在终端按 enter
            await asyncio.get_event_loop().run_in_executor(None, input, "")
            print(f"[login] Saving session...", file=sys.stderr)

    asyncio.run(run_login())
    _print({"success": True, "platform": args.platform, "session_saved": True})


def cmd_sessions(args):
    from core.browser.session import SessionManager
    _print(SessionManager().list_sessions())


def cmd_logout(args):
    from core.browser.session import SessionManager
    deleted = SessionManager().delete_session(args.platform)
    _print({"platform": args.platform, "deleted": deleted})


# ==================== Social Actions ====================

def _run_action(platform: str, action_name: str, headed: bool, action_fn):
    """通用动作执行包装"""
    config = get_config()
    from core.browser import BrowserManager, SafetyGuard
    from core.actors import get_actor

    browser = BrowserManager(headless=not headed)
    safety = SafetyGuard(data_dir=config.data_dir)

    async def run():
        try:
            await browser.start()
            actor = get_actor(platform, browser, safety)
            return await action_fn(actor)
        finally:
            await browser.stop()

    result = asyncio.run(run())
    _print(result)
    if not result.get("success"):
        sys.exit(1)


def cmd_post(args):
    _run_action(args.platform, "post", args.headed,
                lambda actor: actor.post(args.content))


def cmd_comment(args):
    _run_action(args.platform, "comment", args.headed,
                lambda actor: actor.comment(args.url, args.content))


def cmd_like(args):
    _run_action(args.platform, "like", args.headed,
                lambda actor: actor.like(args.url))


def cmd_retweet(args):
    _run_action("x", "retweet", args.headed,
                lambda actor: actor.retweet(args.url, with_quote=args.quote))


def cmd_follow(args):
    _run_action(args.platform, "follow", args.headed,
                lambda actor: actor.follow(args.url))


def cmd_subscribe(args):
    _run_action("youtube", "subscribe", args.headed,
                lambda actor: actor.subscribe(args.url))


def cmd_limits(args):
    config = get_config()
    from core.browser import SafetyGuard
    _print(SafetyGuard(data_dir=config.data_dir).get_status())


# ==================== Helpers ====================

def _count(items, key):
    counts = {}
    for it in items:
        v = it.get(key, "unknown")
        counts[v] = counts.get(v, 0) + 1
    return counts


# ==================== Main ====================

def main():
    parser = argparse.ArgumentParser(
        prog="x-agent",
        description="X-Agent: Browser-based trend research, AI content gen & social actions",
    )
    sub = parser.add_subparsers(dest="command")

    # --- Research / Generation ---
    p = sub.add_parser("trends", help="Fetch trends via browser scraping (multi-layer search supported)")
    p.add_argument("--niche", default=None, help="Predefined niche (ai_tools, crypto, ...)")
    p.add_argument("--query", "-q", default=None, help="Custom search keyword (overrides niche default query)")
    p.add_argument("--refine", "-r", action="append", help="Cascade filter (repeat to narrow further: -r uk -r fitness -r gym)")
    p.add_argument("--days", type=int, default=7)
    p.add_argument("--sources", default="x,reddit,hackernews,google_trends,youtube,tiktok")
    p.add_argument("--limit", type=int, default=20, help="Max items per platform")
    p.add_argument("--rank-by", default="engagement", choices=["engagement", "velocity", "recent"], help="How to rank top posts")
    p.add_argument("--headed", action="store_true", help="Show browser (debug)")
    p.add_argument("--full", action="store_true", help="Output full JSON (default: summary)")
    p.set_defaults(func=cmd_trends)

    p = sub.add_parser("search", help="Search within cached trends (no re-scraping)")
    p.add_argument("--query", "-q", default=None, help="Initial query")
    p.add_argument("--refine", "-r", action="append", help="Cascade filter (repeat to narrow)")
    p.add_argument("--niche", default=None, help="Restrict to one niche")
    p.add_argument("--limit", type=int, default=50)
    p.add_argument("--full", action="store_true")
    p.set_defaults(func=cmd_search)

    p = sub.add_parser("create", help="Generate content (a/b/c)")
    p.add_argument("--type", default="a", choices=["a", "b", "c"])
    p.add_argument("--topic", required=True)
    p.add_argument("--niche", default=None)
    p.set_defaults(func=cmd_create)

    p = sub.add_parser("score", help="Score trend data")
    p.add_argument("--input", default=None)
    p.set_defaults(func=cmd_score)

    p = sub.add_parser("report", help="Generate daily report")
    p.add_argument("--date", default=None)
    p.set_defaults(func=cmd_report)

    p = sub.add_parser("status", help="Show config/storage/sessions status")
    p.set_defaults(func=cmd_status)

    # --- Sessions ---
    p = sub.add_parser("login", help="Open browser to log in (one-time, headed)")
    p.add_argument("--platform", required=True)
    p.set_defaults(func=cmd_login)

    p = sub.add_parser("sessions", help="List login sessions for all platforms")
    p.set_defaults(func=cmd_sessions)

    p = sub.add_parser("logout", help="Delete saved session for a platform")
    p.add_argument("--platform", required=True)
    p.set_defaults(func=cmd_logout)

    # --- Social Actions ---
    p = sub.add_parser("post", help="Post content to a platform")
    p.add_argument("--platform", required=True)
    p.add_argument("--content", required=True)
    p.add_argument("--headed", action="store_true")
    p.set_defaults(func=cmd_post)

    p = sub.add_parser("comment", help="Comment on a URL")
    p.add_argument("--platform", required=True)
    p.add_argument("--url", required=True)
    p.add_argument("--content", required=True)
    p.add_argument("--headed", action="store_true")
    p.set_defaults(func=cmd_comment)

    p = sub.add_parser("like", help="Like a URL")
    p.add_argument("--platform", required=True)
    p.add_argument("--url", required=True)
    p.add_argument("--headed", action="store_true")
    p.set_defaults(func=cmd_like)

    p = sub.add_parser("retweet", help="Retweet (X only, optionally with quote)")
    p.add_argument("--url", required=True)
    p.add_argument("--quote", default=None, help="Optional quote text")
    p.add_argument("--headed", action="store_true")
    p.set_defaults(func=cmd_retweet)

    p = sub.add_parser("follow", help="Follow a profile (TikTok)")
    p.add_argument("--platform", default="tiktok")
    p.add_argument("--url", required=True)
    p.add_argument("--headed", action="store_true")
    p.set_defaults(func=cmd_follow)

    p = sub.add_parser("subscribe", help="Subscribe to a channel (YouTube)")
    p.add_argument("--url", required=True)
    p.add_argument("--headed", action="store_true")
    p.set_defaults(func=cmd_subscribe)

    p = sub.add_parser("limits", help="Show daily action quotas")
    p.set_defaults(func=cmd_limits)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)
    args.func(args)


if __name__ == "__main__":
    main()
