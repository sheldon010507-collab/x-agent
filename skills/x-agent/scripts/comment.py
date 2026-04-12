#!/usr/bin/env python3
"""评论指定推文"""
import argparse
import json
import sys

import requests

API_BASE = "http://localhost:8000"


def main():
    parser = argparse.ArgumentParser(description="Comment on a tweet")
    parser.add_argument("--url", required=True, help="Tweet URL")
    parser.add_argument("--content", required=True, help="Comment content")
    parser.add_argument("--style", default="conversational", help="Comment style")
    args = parser.parse_args()

    try:
        resp = requests.post(
            f"{API_BASE}/comment",
            json={
                "url": args.url,
                "content": args.content,
                "style": args.style,
            },
            timeout=120,
        )
        resp.raise_for_status()
        data = resp.json()

        if data.get("success"):
            print(f"✅ Comment posted successfully!")
        else:
            print(f"❌ Comment failed: {data.get('reason', 'Unknown error')}")

    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to x-agent API at {API_BASE}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
