#!/usr/bin/env python3
"""发布推文到 X — Playwright 浏览器自动化"""
import argparse
import json
import sys

import requests

API_BASE = "http://localhost:8000"


def main():
    parser = argparse.ArgumentParser(description="Post tweet to X")
    parser.add_argument("--content", required=True, help="Tweet content (max 280 chars)")
    parser.add_argument("--no-variant", action="store_true", help="Disable content variant (anti-duplicate)")
    args = parser.parse_args()

    try:
        resp = requests.post(
            f"{API_BASE}/post",
            json={
                "content": args.content,
                "variant": not args.no_variant,
            },
            timeout=120,
        )
        resp.raise_for_status()
        data = resp.json()

        if data.get("success"):
            print(f"✅ Tweet posted successfully!")
            details = data.get("details", {})
            if details.get("url"):
                print(f"   URL: {details['url']}")
        else:
            print(f"❌ Post failed: {data.get('reason', 'Unknown error')}")

    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to x-agent API at {API_BASE}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
