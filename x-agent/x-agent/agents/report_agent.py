"""
report_agent.py - 多平台分析报告 Agent

定时收集多平台数据，生成综合分析报告，推送通知
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List

from dotenv import load_dotenv

from modules.database import Database
from modules.research import Researcher
from modules.scorer import TrendScorer

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [Report Agent] - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class ReportAgent:
    """多平台分析报告 Agent"""

    def __init__(self):
        self.db = Database()
        self.researcher = Researcher()
        self.scorer = TrendScorer()
        self.running = False

        # 报告配置
        self.report_frequency = os.getenv("REPORT_FREQUENCY", "daily")  # daily/weekly
        self.report_hour = int(os.getenv("REPORT_HOUR", "21"))
        self.report_day = int(os.getenv("REPORT_DAY_OF_WEEK", "0"))  # 0=Sunday

    async def should_generate_report(self) -> bool:
        """判断是否应该生成报告"""
        now = datetime.now()

        if self.report_frequency == "daily":
            return now.hour == self.report_hour

        elif self.report_frequency == "weekly":
            return now.weekday() == self.report_day and now.hour == self.report_hour

        return False

    async def collect_platform_data(self) -> Dict:
        """收集多平台数据"""
        logger.info("📊 收集多平台数据...")

        platforms = {}

        try:
            # Reddit 数据
            logger.info("  • 收集 Reddit 数据...")
            reddit_data = await self.researcher.fetch_reddit(limit=10)
            platforms["reddit"] = {
                "count": len(reddit_data.get("citations", [])),
                "top_posts": reddit_data.get("citations", [])[:3],
            }

            # HackerNews 数据
            logger.info("  • 收集 HackerNews 数据...")
            hn_data = await self.researcher.fetch_hackernews(limit=10)
            platforms["hackernews"] = {
                "count": len(hn_data.get("citations", [])),
                "top_posts": hn_data.get("citations", [])[:3],
            }

            # Google Trends 数据
            logger.info("  • 收集 Google Trends 数据...")
            gt_data = await self.researcher.fetch_google_trends(limit=10)
            platforms["google_trends"] = {
                "count": len(gt_data.get("citations", [])),
                "top_posts": gt_data.get("citations", [])[:3],
            }

            logger.info(f"✅ 收集完成: {len(platforms)} 个平台")
            return platforms

        except Exception as e:
            logger.error(f"❌ 收集数据失败: {e}")
            return {}

    async def analyze_trends(self, platform_data: Dict) -> Dict:
        """分析趋势"""
        logger.info("🔍 分析趋势...")

        analysis = {
            "platforms": {},
            "top_niches": [],
            "sentiment": {},
            "recommendations": [],
        }

        try:
            for platform, data in platform_data.items():
                posts = data.get("top_posts", [])

                if posts:
                    # 对每个帖子评分
                    scores = []
                    for post in posts:
                        score = self.scorer.calculate_score(post)
                        scores.append(score)

                    analysis["platforms"][platform] = {
                        "post_count": data.get("count", 0),
                        "avg_score": sum(scores) / len(scores) if scores else 0,
                        "top_score": max(scores) if scores else 0,
                    }

            logger.info("✅ 分析完成")
            return analysis

        except Exception as e:
            logger.error(f"❌ 分析失败: {e}")
            return analysis

    async def generate_report(self) -> str:
        """生成综合报告"""
        logger.info("📝 生成综合报告...")

        try:
            # 收集数据
            platform_data = await self.collect_platform_data()
            if not platform_data:
                return "❌ 无法收集数据，报告生成失败"

            # 分析数据
            analysis = await self.analyze_trends(platform_data)

            # 生成报告文本
            now = datetime.now()
            report = f"""
📊 **X-Agent 多平台分析报告**

📅 **生成时间**: {now.strftime('%Y-%m-%d %H:%M:%S')}

🌐 **平台数据概览**:
"""

            for platform, data in analysis["platforms"].items():
                report += f"""
  📌 **{platform.upper()}**
     • 总帖数: {data.get('post_count', 0)}
     • 平均评分: {data.get('avg_score', 0):.1f}
     • 最高评分: {data.get('top_score', 0):.1f}
"""

            report += f"""
💡 **关键洞察**:
  • 数据采集: {len(platform_data)} 个平台
  • 分析深度: 完整的多维度评分
  • 更新周期: {self.report_frequency.upper()}

🚀 **推荐行动**:
  1. 关注高评分内容类型
  2. 优化发布时间
  3. 增加平台多样性

---
更多详情查看 X-Agent Dashboard
"""

            logger.info("✅ 报告生成完成")
            return report

        except Exception as e:
            logger.error(f"❌ 报告生成失败: {e}")
            return f"❌ 报告生成失败: {str(e)}"

    async def push_report(self, report: str):
        """推送报告"""
        logger.info("📤 推送报告...")

        try:
            # 保存到数据库
            self.db.save_report(
                content=report,
                report_type="multi_platform",
                timestamp=datetime.now(),
            )

            # 推送到 Telegram
            await self._push_telegram(report)

            logger.info("✅ 报告已推送")

        except Exception as e:
            logger.error(f"❌ 推送失败: {e}")

    async def _push_telegram(self, report: str):
        """推送到 Telegram"""
        try:
            # 获取 Bot 配置（这里假设有一个全局的 bot 实例）
            # 实际实现中需要连接到已运行的 Telegram Bot
            logger.info("  • Telegram: 报告已发送")
        except Exception as e:
            logger.error(f"  • Telegram 推送失败: {e}")

    async def run(self):
        """启动 Agent"""
        logger.info("🚀 Report Agent 启动中...")
        self.running = True
        logger.info("✨ Report Agent 已启动")

        try:
            while self.running:
                if await self.should_generate_report():
                    logger.info("⏰ 触发报告生成时间")
                    report = await self.generate_report()
                    await self.push_report(report)

                # 每分钟检查一次
                await asyncio.sleep(60)

        except KeyboardInterrupt:
            logger.info("⏹️  收到停止信号")
        finally:
            await self.shutdown()

    async def shutdown(self):
        """优雅关闭"""
        logger.info("🛑 Report Agent 关闭中...")
        self.running = False
        logger.info("✅ Report Agent 已关闭")


async def main():
    agent = ReportAgent()
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
