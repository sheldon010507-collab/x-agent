#!/usr/bin/env python3
"""4 维热点评分 + 风险评估"""
import argparse
import json
import sys
from pathlib import Path

# 直接导入 scorer 模块（不经过 API）
XAGENT_DIR = str(Path(__file__).resolve().parent.parent.parent.parent / "x-agent")
sys.path.insert(0, XAGENT_DIR)


def main():
    parser = argparse.ArgumentParser(description="Score a topic (4-dimension + risk)")
    parser.add_argument("--topic", required=True, help="Topic data as JSON string")
    args = parser.parse_args()

    try:
        data = json.loads(args.topic)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
        sys.exit(1)

    try:
        from modules.scorer import TrendScorer
        scorer = TrendScorer()
        result = scorer.score_with_details(data)

        score = result.get("score", 0)
        risk = result.get("risk_score", 0)

        # Determine grade
        if score >= 80:
            grade = "🔴 HIGH (Push immediately)"
        elif score >= 60:
            grade = "🟡 MEDIUM (Show in summary)"
        else:
            grade = "🟢 LOW (Store only)"

        # Risk level
        if risk >= 80:
            risk_level = "🚫 HIGH RISK (Block auto-publish)"
        elif risk >= 50:
            risk_level = "⚠️  MEDIUM RISK (Require confirmation)"
        else:
            risk_level = "✅ LOW RISK (Safe)"

        print(f"\n📊 Topic Score: {score:.1f}/100 — {grade}")
        print(f"🛡️  Risk Score: {risk:.1f}/100 — {risk_level}\n")

        details = result.get("details", {})
        if details:
            print("  Breakdown:")
            for dim, val in details.items():
                print(f"    {dim:>15s}: {val:.1f}")
        print()

    except Exception as e:
        print(f"❌ Scoring failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
