"""
migrations.py - 数据库版本管理与升级

将 x-agent 数据库从 Phase 1 升级到 Phase 2，添加以下新表：
  - posts_analytics    : 推文互动数据追踪
  - niche_performance  : Niche 语气效果对标
  - ab_test_results    : A/B 测试结果
  - learning_feedback  : 学习优化反馈记录
"""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# ==================== SQL 建表语句 ====================

CREATE_POSTS_ANALYTICS_TABLE = """
CREATE TABLE IF NOT EXISTS posts_analytics (
    id TEXT PRIMARY KEY,
    post_id TEXT NOT NULL,
    platform TEXT NOT NULL,
    content TEXT,
    niche TEXT,
    type TEXT,
    publish_time TIMESTAMP,

    -- 互动数据（每小时更新）
    likes_count INTEGER DEFAULT 0,
    retweets_count INTEGER DEFAULT 0,
    replies_count INTEGER DEFAULT 0,
    views_count INTEGER DEFAULT 0,

    -- 计算字段
    engagement_rate REAL DEFAULT 0.0,
    last_sync TIMESTAMP,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (post_id) REFERENCES content_queue(id)
);
"""

CREATE_NICHE_PERFORMANCE_TABLE = """
CREATE TABLE IF NOT EXISTS niche_performance (
    id TEXT PRIMARY KEY,
    niche TEXT NOT NULL,
    type TEXT NOT NULL,

    -- 统计数据（基于过去7/30天计算）
    total_posts INTEGER DEFAULT 0,
    avg_engagement_rate REAL DEFAULT 0.0,
    avg_likes REAL DEFAULT 0.0,
    avg_retweets REAL DEFAULT 0.0,
    avg_replies REAL DEFAULT 0.0,

    -- 排名
    engagement_rank INTEGER,

    -- 时间窗口
    period_days INTEGER DEFAULT 7,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_AB_TEST_RESULTS_TABLE = """
CREATE TABLE IF NOT EXISTS ab_test_results (
    id TEXT PRIMARY KEY,
    test_name TEXT NOT NULL,
    variant_a_content TEXT NOT NULL,
    variant_b_content TEXT NOT NULL,
    variant_a_niche TEXT NOT NULL,
    variant_b_niche TEXT NOT NULL,

    variant_a_id TEXT,
    variant_b_id TEXT,

    variant_a_engagement REAL DEFAULT 0.0,
    variant_b_engagement REAL DEFAULT 0.0,
    winner TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    concluded_at TIMESTAMP
);
"""

CREATE_LEARNING_FEEDBACK_TABLE = """
CREATE TABLE IF NOT EXISTS learning_feedback (
    id TEXT PRIMARY KEY,
    feedback_type TEXT NOT NULL,

    post_id TEXT,
    niche TEXT NOT NULL,
    type TEXT,
    engagement_rate REAL DEFAULT 0.0,

    -- 建议调整
    suggested_niche TEXT,
    suggested_type TEXT,
    adjustment_reason TEXT,

    applied BOOLEAN DEFAULT FALSE,
    applied_at TIMESTAMP,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

# ==================== 索引 ====================

CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_posts_analytics_niche_type ON posts_analytics(niche, type);",
    "CREATE INDEX IF NOT EXISTS idx_posts_analytics_publish_time ON posts_analytics(publish_time);",
    "CREATE INDEX IF NOT EXISTS idx_posts_analytics_platform ON posts_analytics(platform);",
    "CREATE INDEX IF NOT EXISTS idx_niche_performance_engagement_rate ON niche_performance(avg_engagement_rate DESC);",
    "CREATE INDEX IF NOT EXISTS idx_niche_performance_niche_type ON niche_performance(niche, type);",
    "CREATE INDEX IF NOT EXISTS idx_ab_test_results_test_name ON ab_test_results(test_name);",
    "CREATE INDEX IF NOT EXISTS idx_learning_feedback_feedback_type ON learning_feedback(feedback_type);",
    "CREATE INDEX IF NOT EXISTS idx_learning_feedback_niche ON learning_feedback(niche);",
]


class DatabaseMigration:
    """数据库迁移管理器"""

    def __init__(self, db):
        self.db = db

    async def migrate_to_phase2(self) -> bool:
        """
        执行 Phase 2 迁移

        1. 创建新表
        2. 创建索引
        3. 验证表结构
        4. 记录迁移时间

        Returns:
            bool: 迁移是否成功
        """
        try:
            logger.info("🚀 开始 Phase 2 数据库迁移...")

            # 1. 创建新表
            logger.info("📊 创建新表...")
            await self.db.execute(CREATE_POSTS_ANALYTICS_TABLE)
            await self.db.execute(CREATE_NICHE_PERFORMANCE_TABLE)
            await self.db.execute(CREATE_AB_TEST_RESULTS_TABLE)
            await self.db.execute(CREATE_LEARNING_FEEDBACK_TABLE)
            logger.info("✅ 4个新表创建完成")

            # 2. 创建索引
            logger.info("📑 创建索引...")
            for index_sql in CREATE_INDEXES:
                await self.db.execute(index_sql)
            logger.info(f"✅ {len(CREATE_INDEXES)} 个索引创建完成")

            # 3. 验证表结构
            logger.info("🔍 验证表结构...")
            tables = ["posts_analytics", "niche_performance", "ab_test_results", "learning_feedback"]
            for table in tables:
                exists = await self._table_exists(table)
                if exists:
                    logger.info(f"  ✓ 表 {table} 验证成功")
                else:
                    raise Exception(f"表 {table} 创建失败")

            # 4. 记录迁移时间
            migration_record = {
                'version': '2.0',
                'name': 'Phase 2: Web Dashboard + Feedback Loop',
                'timestamp': datetime.now().isoformat(),
                'tables_created': 4,
                'indexes_created': len(CREATE_INDEXES),
            }

            await self.db.execute("""
                INSERT OR REPLACE INTO migrations (version, name, applied_at)
                VALUES (?, ?, ?)
            """, ('2.0', 'Phase 2: Web Dashboard + Feedback Loop', datetime.now()))

            logger.info("✅ Phase 2 数据库迁移完成！")
            logger.info(f"  📊 新表: {', '.join(tables)}")
            logger.info(f"  📑 索引: {len(CREATE_INDEXES)} 个")
            return True

        except Exception as e:
            logger.error(f"❌ 迁移失败: {e}")
            return False

    async def _table_exists(self, table_name: str) -> bool:
        """检查表是否存在"""
        result = await self.db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        )
        return bool(result)

    async def rollback(self) -> bool:
        """回滚 Phase 2（删除新表）"""
        try:
            logger.warning("⚠️  执行 Phase 2 回滚...")

            tables = [
                "posts_analytics",
                "niche_performance",
                "ab_test_results",
                "learning_feedback",
            ]

            for table in tables:
                await self.db.execute(f"DROP TABLE IF EXISTS {table};")
                logger.info(f"  ✓ 表 {table} 已删除")

            logger.info("✅ Phase 2 回滚完成")
            return True

        except Exception as e:
            logger.error(f"❌ 回滚失败: {e}")
            return False


# ==================== 启动时自动迁移 ====================

async def auto_migrate_on_startup(db):
    """
    在应用启动时自动检查并执行迁移

    使用方式：
    @app.on_event("startup")
    async def startup():
        await auto_migrate_on_startup(app.state.db)
    """
    try:
        # 检查迁移历史
        migrations = await db.execute(
            "SELECT version FROM migrations WHERE version = '2.0'"
        )

        if migrations:
            logger.info("✅ Phase 2 数据库已迁移，跳过")
            return

        # 执行迁移
        migration = DatabaseMigration(db)
        success = await migration.migrate_to_phase2()

        if not success:
            logger.error("❌ 自动迁移失败，某些功能可能不可用")

    except Exception as e:
        logger.error(f"⚠️  迁移检查出错: {e}")
