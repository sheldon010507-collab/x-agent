#!/usr/bin/env python3
"""AI 趋势分析报告 — 搜索 + LLM 分析"""
import argparse
import json
import sys

import requests

API_BASE = "http://localhost:8000"


def main():
    parser = argparse.ArgumentParser(description="AI trend analysis report")
    parser.add_argument("keyword", help="Analysis keyword")
    parser.add_argument("--sources", default="x,tiktok,reddit", help="Data sources, comma-separated")
    args = parser.parse_args()

    try:
        print(f"\n🔬 Analyzing \"{args.keyword}\" (sources: {args.sources})...")
        print("   This may take a moment...\n")

        resp = requests.post(
            f"{API_BASE}/analyze",
            json={
                "keyword": args.keyword,
                "sources": args.sources,
            },
            timeout=180,
        )
        resp.raise_for_status()
        data = resp.json()

        report = data.get("report", "No report generated.")
        print(report)

    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to x-agent API at {API_BASE}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
