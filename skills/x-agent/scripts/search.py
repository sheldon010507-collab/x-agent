#!/usr/bin/env python3
"""搜索多平台热点趋势 — 调用 x-agent REST API"""
import argparse
import json
import sys

import requests

API_BASE = "http://localhost:8000"


def main():
    parser = argparse.ArgumentParser(description="Search multi-platform trends")
    parser.add_argument("keyword", help="Search keyword")
    parser.add_argument(
        "--sources",
        default="x,tiktok,reddit,hackernews",
        help="Data sources, comma-separated (x,tiktok,reddit,hackernews,youtube,web)",
    )
    parser.add_argument("--days", type=int, default=7, help="Lookback days (1-30)")
    parser.add_argument("--min-score", type=float, default=0, help="Minimum score (0-100)")
    parser.add_argument("--merge-previous", action="store_true", help="Merge with previous search layer")
    args = parser.parse_args()

    try:
        resp = requests.get(
            f"{API_BASE}/trends",
            params={
                "niche": args.keyword,
                "days": args.days,
                "sources": args.sources,
                "min_score": args.min_score,
            },
            timeout=120,
        )
        resp.raise_for_status()
        data = resp.json()

        print(f"\n🔍 Search: \"{args.keyword}\" | Sources: {args.sources} | Days: {args.days}")
        print(f"📊 Found {data.get('total', 0)} trends (min_score >= {args.min_score})\n")

        for i, trend in enumerate(data.get("trends", [])[:20], 1):
            title = trend.get("title") or trend.get("text", "")[:80]
            platform = trend.get("platform", "?")
            score = trend.get("score", 0)
            url = trend.get("url", "")
            print(f"  {i:2d}. [{platform:>12s}] (Score: {score:.0f}) {title}")
            if url:
                print(f"      {url}")

        if not data.get("trends"):
            print("  No trends found. Try different keywords or sources.")

    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to x-agent API at {API_BASE}")
        print("   Make sure x-agent-api is running: docker-compose up x-agent-api")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
