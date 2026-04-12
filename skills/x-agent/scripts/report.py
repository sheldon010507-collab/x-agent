#!/usr/bin/env python3
"""获取每日运营报告"""
import argparse
import json
import sys

import requests

API_BASE = "http://localhost:8000"


def main():
    parser = argparse.ArgumentParser(description="Get daily operations report")
    parser.add_argument("--date", default=None, help="Date YYYY-MM-DD (default: today)")
    args = parser.parse_args()

    try:
        params = {}
        if args.date:
            params["date"] = args.date

        resp = requests.get(f"{API_BASE}/report", params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        print(f"\n📊 Daily Report — {data.get('date', 'N/A')}\n")
        print(f"  📝 Posts:    {data.get('posts_count', 0)}")
        print(f"  💬 Comments: {data.get('comments_count', 0)}")
        print(f"  ❤️  Likes:    {data.get('likes_count', 0)}")
        print(f"  🔄 Retweets: {data.get('rt_count', 0)}")
        print(f"  🏆 Top engagement: {data.get('top_engagement', 0)}")

        notes = data.get("notes")
        if notes:
            print(f"\n  📋 Notes: {notes}")
        print()

    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to x-agent API at {API_BASE}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
