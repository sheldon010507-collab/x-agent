"""
test_api.py - X-Agent FastAPI 端点测试

使用 TestClient（同步）+ 完全 Mock 所有外部依赖，离线运行。
"""

import sys
from datetime import date
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent))


# ============ Fixtures ============


def make_app_state(app):
    """为 FastAPI app.state 注入 Mock 组件"""
    config = MagicMock()
    config.llm.provider = "anthropic"
    config.supabase_url = "https://test.supabase.co"
    config.supabase_key = "test-key"

    db = MagicMock()
    db.get_current_niche.return_value = "ai_tools"
    db.confirm_content.return_value = None
    db.get_daily_log.return_value = {
        "date": date.today().isoformat(),
        "posts_count": 5,
        "comments_count": 12,
        "likes_count": 30,
        "rt_count": 8,
        "top_engagement": 150,
        "notes": "测试日报",
    }
    db.create_content.return_value = {"id": "test-content-id-001"}

    llm_router = MagicMock()
    generator = MagicMock()
    generator.niche = "ai_tools"
    generator.generate_type_a = AsyncMock(
        return_value={
            "tweets": [
                {"angle": "Hot take", "content": "AI is amazing!", "hashtags": ["#AI"]},
            ],
            "media_suggestion": "ai, robot",
        }
    )
    generator.generate_type_b = AsyncMock(
        return_value={"script": "Video script content here.", "duration": "60s"}
    )

    researcher = MagicMock()
    researcher.research_async = AsyncMock(
        return_value={
            "hackernews": {
                "posts": [
                    {
                        "topic": "AI Trends 2026",
                        "score": 85.0,
                        "source": "hackernews",
                        "summary": "AI is growing fast",
                    }
                ]
            }
        }
    )

    scorer = MagicMock()
    scorer.score_with_details.return_value = {"score": 85.0}

    deduplicator = MagicMock()
    deduplicator.deduplicate.side_effect = lambda x: x

    app.state.config = config
    app.state.db = db
    app.state.llm_router = llm_router
    app.state.generator = generator
    app.state.researcher = researcher
    app.state.scorer = scorer
    app.state.deduplicator = deduplicator
    app.state.niche = "ai_tools"
    return app


@pytest.fixture
def client():
    """返回已初始化的 TestClient（绕过 lifespan）"""
    import api as api_module

    # 注入 Mock 状态，跳过真实 lifespan 初始化
    make_app_state(api_module.app)

    with TestClient(api_module.app, raise_server_exceptions=True) as c:
        yield c


# ============ 测试用例 ============


class TestHealth:
    def test_health_returns_ok(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "timestamp" in data


class TestTrends:
    def test_trends_returns_list(self, client):
        resp = client.get("/trends?niche=ai_tools&days=7")
        assert resp.status_code == 200
        data = resp.json()
        assert data["niche"] == "ai_tools"
        assert data["days"] == 7
        assert isinstance(data["trends"], list)
        assert data["total"] == len(data["trends"])

    def test_trends_default_params(self, client):
        resp = client.get("/trends")
        assert resp.status_code == 200

    def test_trends_days_out_of_range(self, client):
        resp = client.get("/trends?days=0")
        assert resp.status_code == 422

    def test_trends_days_max(self, client):
        resp = client.get("/trends?days=31")
        assert resp.status_code == 422


class TestCreate:
    def test_create_type_a(self, client):
        resp = client.post(
            "/create",
            json={"niche": "ai_tools", "type": "A", "topic": "GPT-5 released"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["type"] == "A"
        assert data["status"] == "draft"
        assert "result" in data

    def test_create_type_b(self, client):
        resp = client.post(
            "/create",
            json={"niche": "ai_tools", "type": "B", "topic": "AI video tools"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["type"] == "B"

    def test_create_invalid_type(self, client):
        resp = client.post(
            "/create",
            json={"niche": "ai_tools", "type": "Z", "topic": "test"},
        )
        assert resp.status_code == 422

    def test_create_missing_topic(self, client):
        resp = client.post("/create", json={"niche": "ai_tools", "type": "A"})
        assert resp.status_code == 422

    def test_create_returns_content_id(self, client):
        resp = client.post(
            "/create",
            json={"niche": "ai_tools", "type": "A", "topic": "AI test"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["content_id"] == "test-content-id-001"


class TestApprove:
    def test_approve_returns_confirmed(self, client):
        resp = client.post("/approve/test-content-id-001")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "confirmed"
        assert data["content_id"] == "test-content-id-001"

    def test_approve_includes_message(self, client):
        resp = client.post("/approve/abc-123")
        assert resp.status_code == 200
        data = resp.json()
        assert "abc-123" in data["message"]


class TestReport:
    def test_report_today(self, client):
        resp = client.get("/report")
        assert resp.status_code == 200
        data = resp.json()
        assert "date" in data
        assert "posts_count" in data
        assert data["posts_count"] == 5

    def test_report_specific_date(self, client):
        resp = client.get("/report?date=2026-03-31")
        assert resp.status_code == 200
        data = resp.json()
        assert data["date"] == "2026-03-31"

    def test_report_invalid_date(self, client):
        resp = client.get("/report?date=not-a-date")
        assert resp.status_code == 422

    def test_report_no_data_returns_empty(self, client):
        import api as api_module

        api_module.app.state.db.get_daily_log.return_value = None
        resp = client.get("/report?date=2020-01-01")
        assert resp.status_code == 200
        data = resp.json()
        assert data["posts_count"] == 0
        assert data["notes"] == "暂无数据"
        # 恢复 mock
        api_module.app.state.db.get_daily_log.return_value = {
            "date": date.today().isoformat(),
            "posts_count": 5,
            "comments_count": 12,
            "likes_count": 30,
            "rt_count": 8,
            "top_engagement": 150,
            "notes": "测试日报",
        }


class TestStatus:
    def test_status_returns_service_info(self, client):
        resp = client.get("/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["service"] == "x-agent-api"
        assert data["version"] == "1.0.0"
        assert data["llm_provider"] == "anthropic"
        assert "timestamp" in data
