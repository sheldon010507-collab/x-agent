"""
api.py - X-Agent FastAPI HTTP 服务

将 X-Agent 所有功能暴露为 REST API，供 OpenClaw Bot 调用。

启动方式：
    python -m uvicorn api:app --host 0.0.0.0 --port 8000

端点：
    GET  /health          健康检查
    GET  /trends          获取热点（采集+评分+去重）
    POST /create          生成内容草稿
    POST /approve/{id}    确认内容发布
    GET  /report          每日日报
    GET  /status          系统状态

Fixed: Supabase httpx compatibility (v2.5.0, httpx<0.25.0)
"""

import logging
import os
import sys
from contextlib import asynccontextmanager
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent))

from fastapi import Body, Depends, FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

logger = logging.getLogger(__name__)


def require_api_key(x_agent_api_key: Optional[str] = Header(default=None)) -> None:
    expected = os.getenv("XAGENT_API_KEY")
    if not expected:
        raise HTTPException(status_code=503, detail="XAGENT_API_KEY is not configured")
    if x_agent_api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid X-Agent API key")


# ============ Pydantic 模型 ============


class HealthResponse(BaseModel):
    status: str
    timestamp: str


class TrendItem(BaseModel):
    topic: str
    score: float
    source: str
    summary: Optional[str] = None
    url: Optional[str] = None


class TrendsResponse(BaseModel):
    niche: str
    days: int
    trends: List[Dict[str, Any]]
    total: int


class CreateRequest(BaseModel):
    niche: str = "general"
    type: str = "A"  # A=推文, B=视频脚本
    topic: str
    summary: str = ""
    source: str = ""
    score: float = 50.0


class CreateResponse(BaseModel):
    content_id: Optional[str] = None
    type: str
    result: Dict[str, Any]
    status: str = "draft"


class ApproveResponse(BaseModel):
    content_id: str
    status: str
    message: str


class ReportResponse(BaseModel):
    date: str
    posts_count: int
    comments_count: int
    likes_count: int
    rt_count: int
    top_engagement: int
    notes: Optional[str] = None


class CommentRequest(BaseModel):
    url: str
    content: str
    style: str = "conversational"


class LikeRequest(BaseModel):
    url: str


class RetweetRequest(BaseModel):
    url: str
    comment: Optional[str] = None


class PostRequest(BaseModel):
    content: str
    variant: bool = True


class AnalyzeRequest(BaseModel):
    keyword: str
    sources: str = "x,tiktok,reddit"


class DMsResponse(BaseModel):
    dms: List[Dict[str, Any]]
    total: int


class ActionResponse(BaseModel):
    success: bool
    reason: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class AnalyzeResponse(BaseModel):
    report: str


class StatusResponse(BaseModel):
    service: str
    version: str
    llm_provider: str
    niche: str
    timestamp: str


# ============ 应用初始化 ============


@asynccontextmanager
async def lifespan(app: FastAPI):
    """初始化所有组件"""
    from config import Config
    from modules.deduplicator import ContentDeduplicator
    from modules.generator import ContentGenerator
    from modules.llm_router import LLMRouter
    from modules.research import Researcher
    from modules.scorer import TrendScorer

    logger.info("🚀 X-Agent API 启动中...")

    try:
        config = Config()
        app.state.config = config

        # Try to init DB, but don't fail if it fails
        app.state.db = None
        try:
            from modules.database import init_database

            app.state.db = init_database(config.supabase_url, config.supabase_key)
            logger.info("✅ Database initialized")
        except Exception as db_err:
            logger.warning(f"⚠️  Database init failed (running without DB): {db_err}")

        app.state.llm_router = LLMRouter(config)
        logger.info(f"✅ LLM Router initialized (Provider: {config.llm.provider})")

        niche = "general"
        if app.state.db:
            try:
                niche = await run_in_threadpool(app.state.db.get_current_niche) or "general"
            except Exception:
                pass
        app.state.niche = niche

        app.state.generator = ContentGenerator(app.state.llm_router, niche)
        app.state.researcher = Researcher(config)
        app.state.scorer = TrendScorer(app.state.db) if app.state.db else None
        app.state.deduplicator = ContentDeduplicator()

        logger.info("🎉 X-Agent API 初始化完成")
    except Exception as e:
        logger.error(f"❌ 初始化失败: {e}")
        raise

    yield

    logger.info("👋 X-Agent API 关闭")


app = FastAPI(
    title="X-Agent API",
    description="X-Agent 功能 REST API，供 OpenClaw Bot 调用",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============ 端点 ============


@app.get("/health", response_model=HealthResponse)
async def health():
    """健康检查"""
    return HealthResponse(status="ok", timestamp=datetime.now().isoformat())


@app.get("/trends", response_model=TrendsResponse)
async def get_trends(
    niche: str = Query(default="general", description="研究领域"),
    days: int = Query(default=7, ge=1, le=30, description="回溯天数"),
    sources: str = Query(default="hackernews,reddit", description="数据源，逗号分隔"),
    min_score: float = Query(default=50.0, ge=0, le=100, description="最低热点分数"),
):
    """获取热点趋势（采集 + 评分 + 去重）"""
    researcher = app.state.researcher
    scorer = app.state.scorer
    deduplicator = app.state.deduplicator

    try:
        raw = await researcher.research_async(niche=niche, days=days, sources=sources)
    except Exception as e:
        logger.error(f"研究失败: {e}")
        raise HTTPException(status_code=500, detail=f"数据采集失败: {e}")

    # 合并所有平台数据
    all_items = []
    for platform, data in raw.items():
        if isinstance(data, dict) and "posts" in data:
            for post in data["posts"]:
                post["platform"] = platform
                all_items.append(post)

    # 评分 + 过滤
    scored = []
    for item in all_items:
        try:
            score_info = scorer.score_with_details(item)
            item["score"] = score_info.get("score", 50.0)
        except Exception:
            item["score"] = 50.0
        if item["score"] >= min_score:
            scored.append(item)

    # 去重
    try:
        unique = deduplicator.deduplicate(scored)
    except Exception:
        unique = scored

    # 按分数降序
    unique.sort(key=lambda x: x.get("score", 0), reverse=True)

    return TrendsResponse(niche=niche, days=days, trends=unique, total=len(unique))


@app.post("/create", response_model=CreateResponse)
async def create_content(req: CreateRequest):
    """生成内容草稿并保存到数据库"""
    generator = app.state.generator
    db = app.state.db

    # 更新生成器的 niche
    if req.niche != generator.niche:
        from modules.generator import ContentGenerator

        generator = ContentGenerator(app.state.llm_router, req.niche)

    content_type = req.type.upper()
    if content_type not in ("A", "B"):
        raise HTTPException(status_code=422, detail="type 必须为 A（推文）或 B（视频脚本）")

    try:
        if content_type == "A":
            result = await generator.generate_type_a(
                topic=req.topic, summary=req.summary, source=req.source, score=req.score
            )
        else:
            result = await generator.generate_type_b(topic=req.topic, summary=req.summary)
    except Exception as e:
        logger.error(f"内容生成失败: {e}")
        raise HTTPException(status_code=500, detail=f"内容生成失败: {e}")

    # 将第一条内容存入数据库
    content_id = None
    content_text = ""
    try:
        if content_type == "A" and "tweets" in result and result["tweets"]:
            content_text = result["tweets"][0].get("content", "")
        elif content_type == "B":
            content_text = result.get("script", result.get("content", ""))

        if content_text:
            record = await run_in_threadpool(
                db.create_content,
                trend_id="api-generated",
                type=content_type,
                content=content_text,
            )
            if record:
                content_id = record.get("id")
    except Exception as e:
        logger.warning(f"保存到数据库失败（内容已生成）: {e}")

    return CreateResponse(content_id=content_id, type=content_type, result=result, status="draft")


@app.post("/approve/{content_id}", response_model=ApproveResponse)
async def approve_content(content_id: str, _: None = Depends(require_api_key)):
    """确认内容发布（draft → confirmed）"""
    db = app.state.db
    try:
        await run_in_threadpool(db.confirm_content, content_id)
    except Exception as e:
        logger.error(f"确认内容失败: {e}")
        raise HTTPException(status_code=500, detail=f"确认失败: {e}")

    return ApproveResponse(
        content_id=content_id,
        status="confirmed",
        message=f"内容 {content_id} 已确认，等待发布",
    )


@app.post("/approve", response_model=ApproveResponse)
async def approve_content_query(
    content_id: Optional[str] = Query(default=None),
    payload: Optional[Dict[str, str]] = Body(default=None),
    _: None = Depends(require_api_key),
):
    """Compatibility endpoint for the original OpenClaw plan."""
    resolved_id = content_id or (payload or {}).get("content_id")
    if not resolved_id:
        raise HTTPException(status_code=422, detail="content_id is required")
    return await approve_content(resolved_id, None)


@app.get("/report", response_model=ReportResponse)
async def get_report(
    report_date: Optional[str] = Query(
        default=None, description="日期 YYYY-MM-DD，默认今天", alias="date"
    ),
):
    """获取每日日报"""
    db = app.state.db

    try:
        if report_date:
            target_date = date.fromisoformat(report_date)
        else:
            target_date = date.today()
    except ValueError:
        raise HTTPException(status_code=422, detail="日期格式错误，请使用 YYYY-MM-DD")

    try:
        log = await run_in_threadpool(db.get_daily_log, target_date)
    except Exception as e:
        logger.error(f"获取日报失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取日报失败: {e}")

    if not log:
        # 返回空日报
        return ReportResponse(
            date=target_date.isoformat(),
            posts_count=0,
            comments_count=0,
            likes_count=0,
            rt_count=0,
            top_engagement=0,
            notes="暂无数据",
        )

    return ReportResponse(
        date=target_date.isoformat(),
        posts_count=log.get("posts_count", 0),
        comments_count=log.get("comments_count", 0),
        likes_count=log.get("likes_count", 0),
        rt_count=log.get("rt_count", 0),
        top_engagement=log.get("top_engagement", 0),
        notes=log.get("notes"),
    )


@app.get("/daily_report", response_model=ReportResponse)
async def get_daily_report(
    report_date: Optional[str] = Query(default=None, description="Date YYYY-MM-DD", alias="date"),
):
    """Compatibility endpoint for the original OpenClaw plan."""
    return await get_report(report_date=report_date)


@app.get("/status", response_model=StatusResponse)
async def get_status():
    """系统状态"""
    config = app.state.config
    db = app.state.db

    niche = "general"
    try:
        niche = await run_in_threadpool(db.get_current_niche) or "general"
    except Exception:
        pass

    return StatusResponse(
        service="x-agent-api",
        version="1.0.0",
        llm_provider=config.llm.provider,
        niche=niche,
        timestamp=datetime.now().isoformat(),
    )


# ============ 新增端点：DM / Post / Comment / Like / Retweet / Analyze ============


@app.get("/dms", response_model=DMsResponse)
async def get_dms(_: None = Depends(require_api_key)):
    """获取 X 私信列表（指纹浏览器）"""
    try:
        from modules.x_dm_monitor import XDMMonitor
    except ImportError:
        raise HTTPException(status_code=501, detail="x_dm_monitor 模块未安装")

    config = app.state.config
    if not getattr(config, "x_username", None) or not getattr(config, "x_password", None):
        raise HTTPException(status_code=400, detail="需要配置 X_USERNAME 和 X_PASSWORD")

    try:
        monitor = XDMMonitor(config)
        dms = await monitor.fetch_dms()
        return DMsResponse(dms=dms, total=len(dms))
    except Exception as e:
        logger.error(f"获取私信失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取私信失败: {e}")


@app.post("/post", response_model=ActionResponse)
async def post_tweet(req: PostRequest, _: None = Depends(require_api_key)):
    """发布推文到 X（Playwright 浏览器自动化）"""
    try:
        from modules.openclaw_bridge import OpenClawBridge
    except ImportError:
        raise HTTPException(status_code=501, detail="openclaw_bridge 模块未安装")

    try:
        bridge = OpenClawBridge()
        bridge.auto_post_enabled = True
        await bridge.initialize()
        result = await bridge.post_content(content=req.content, apply_variant=req.variant)
        return ActionResponse(
            success=result.get("success", False),
            reason=result.get("reason"),
            details=result,
        )
    except Exception as e:
        logger.error(f"发帖失败: {e}")
        raise HTTPException(status_code=500, detail=f"发帖失败: {e}")


@app.post("/comment", response_model=ActionResponse)
async def comment_tweet(req: CommentRequest, _: None = Depends(require_api_key)):
    """评论指定推文"""
    try:
        from modules.openclaw_bridge import OpenClawBridge
    except ImportError:
        raise HTTPException(status_code=501, detail="openclaw_bridge 模块未安装")

    try:
        bridge = OpenClawBridge()
        bridge.auto_comment_enabled = True
        await bridge.initialize()
        if not bridge.x_automation:
            raise HTTPException(status_code=500, detail="X 自动化未初始化")
        result = await bridge.x_automation.comment(req.url, req.content)
        return ActionResponse(
            success=result.get("success", False),
            reason=result.get("reason"),
            details=result,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"评论失败: {e}")
        raise HTTPException(status_code=500, detail=f"评论失败: {e}")


@app.post("/like", response_model=ActionResponse)
async def like_tweet(req: LikeRequest, _: None = Depends(require_api_key)):
    """点赞指定推文"""
    try:
        from modules.openclaw_bridge import OpenClawBridge
    except ImportError:
        raise HTTPException(status_code=501, detail="openclaw_bridge 模块未安装")

    try:
        bridge = OpenClawBridge()
        bridge.auto_like_enabled = True
        await bridge.initialize()
        result = await bridge.like_post(req.url)
        return ActionResponse(
            success=result.get("success", False),
            reason=result.get("reason"),
            details=result,
        )
    except Exception as e:
        logger.error(f"点赞失败: {e}")
        raise HTTPException(status_code=500, detail=f"点赞失败: {e}")


@app.post("/retweet", response_model=ActionResponse)
async def retweet_tweet(req: RetweetRequest, _: None = Depends(require_api_key)):
    """转发指定推文"""
    try:
        from modules.openclaw_bridge import OpenClawBridge
    except ImportError:
        raise HTTPException(status_code=501, detail="openclaw_bridge 模块未安装")

    try:
        bridge = OpenClawBridge()
        bridge.auto_rt_enabled = True
        await bridge.initialize()
        result = await bridge.retweet_post(req.url, req.comment)
        return ActionResponse(
            success=result.get("success", False),
            reason=result.get("reason"),
            details=result,
        )
    except Exception as e:
        logger.error(f"转发失败: {e}")
        raise HTTPException(status_code=500, detail=f"转发失败: {e}")


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_trends(req: AnalyzeRequest):
    """AI 趋势分析 — 搜索 + LLM 生成 Markdown 报告"""
    researcher = app.state.researcher
    generator = app.state.generator

    try:
        raw = await researcher.research_async(niche=req.keyword, sources=req.sources)
    except Exception as e:
        logger.error(f"搜索失败: {e}")
        raise HTTPException(status_code=500, detail=f"数据采集失败: {e}")

    # 汇总各平台数据
    summary_parts = []
    for platform, data in raw.items():
        if isinstance(data, dict) and "posts" in data:
            for post in data["posts"][:5]:
                title = post.get("title") or post.get("text", "")[:80]
                summary_parts.append(f"[{platform}] {title}")

    summary_text = "\n".join(summary_parts) if summary_parts else "暂无搜索数据"

    try:
        report = await generator.llm_router.chat(
            messages=[
                {
                    "role": "system",
                    "content": "你是专业的社交媒体运营分析师，擅长多平台趋势分析。请输出结构清晰的 Markdown 报告。",
                },
                {
                    "role": "user",
                    "content": f"""请根据以下多平台搜索数据，为关键词「{req.keyword}」生成一份趋势分析报告（Markdown 格式）。

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
        return AnalyzeResponse(report=report)
    except Exception as e:
        logger.error(f"分析报告生成失败: {e}")
        raise HTTPException(status_code=500, detail=f"分析报告生成失败: {e}")


# ============ 启动入口 ============

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=False)
