"""Scheduled multi-platform report agent."""

import asyncio
import logging
import os
from datetime import datetime
from typing import Dict

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
    """Collects platform data, builds a compact report, and stores/pushes it."""

    def __init__(self):
        self.db = Database()
        self.researcher = Researcher()
        self.scorer = TrendScorer()
        self.running = False
        self.report_frequency = os.getenv("REPORT_FREQUENCY", "daily")
        self.report_hour = int(os.getenv("REPORT_HOUR", "21"))
        self.report_day = int(os.getenv("REPORT_DAY_OF_WEEK", "0"))

    async def should_generate_report(self) -> bool:
        now = datetime.now()
        if self.report_frequency == "daily":
            return now.hour == self.report_hour
        if self.report_frequency == "weekly":
            return now.weekday() == self.report_day and now.hour == self.report_hour
        return False

    async def collect_platform_data(self) -> Dict:
        logger.info("Collecting multi-platform data...")
        try:
            result = await self.researcher.research_async(
                niche=os.getenv("REPORT_NICHE", "general"),
                days=1,
                sources="reddit,hackernews,google_trends",
                timeout_secs=25.0,
            )
        except Exception as exc:
            logger.error("Data collection failed: %s", exc)
            return {}

        platforms = {}
        for platform, data in result.get("platform_data", {}).items():
            posts = data.get("posts", []) if isinstance(data, dict) else []
            platforms[platform] = {"count": len(posts), "top_posts": posts[:3]}
        return platforms

    async def analyze_trends(self, platform_data: Dict) -> Dict:
        analysis = {"platforms": {}, "recommendations": []}
        for platform, data in platform_data.items():
            posts = data.get("top_posts", [])
            scores = [self.scorer.calculate_score(post) for post in posts] if posts else []
            analysis["platforms"][platform] = {
                "post_count": data.get("count", 0),
                "avg_score": sum(scores) / len(scores) if scores else 0,
                "top_score": max(scores) if scores else 0,
            }
        analysis["recommendations"] = [
            "Prioritize the highest-scoring cross-platform topics.",
            "Review low-volume platforms before increasing automation.",
            "Keep human approval before publishing generated posts.",
        ]
        return analysis

    async def generate_report(self) -> str:
        platform_data = await self.collect_platform_data()
        if not platform_data:
            return "Report generation failed: no platform data collected."

        analysis = await self.analyze_trends(platform_data)
        now = datetime.now()
        lines = [
            "# X-Agent Multi-Platform Report",
            "",
            f"Generated: {now.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Platform Summary",
        ]
        for platform, data in analysis["platforms"].items():
            lines.extend(
                [
                    f"- {platform}: {data['post_count']} posts, "
                    f"avg score {data['avg_score']:.1f}, top score {data['top_score']:.1f}"
                ]
            )
        lines.extend(["", "## Recommendations"])
        lines.extend(f"- {item}" for item in analysis["recommendations"])
        return "\n".join(lines)

    async def push_report(self, report: str):
        self.db.save_report(
            content=report,
            report_type="multi_platform",
            timestamp=datetime.now(),
        )
        await self._push_telegram(report)
        logger.info("Report stored and push hook completed")

    async def _push_telegram(self, report: str):
        logger.info("Telegram push hook: %s", report[:120])

    async def run(self):
        logger.info("Report Agent starting...")
        self.running = True
        try:
            while self.running:
                if await self.should_generate_report():
                    report = await self.generate_report()
                    await self.push_report(report)
                await asyncio.sleep(60)
        except KeyboardInterrupt:
            logger.info("Report Agent interrupted")
        finally:
            await self.shutdown()

    async def shutdown(self):
        self.running = False
        logger.info("Report Agent stopped")


async def main():
    agent = ReportAgent()
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
