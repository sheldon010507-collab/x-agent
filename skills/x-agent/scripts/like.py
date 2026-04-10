#!/usr/bin/env python3
"""点赞指定推文"""
import argparse
import sys

import requests

API_BASE = "http://localhost:8000"


def main():
    parser = argparse.ArgumentParser(description="Like a tweet")
    parser.add_argument("--url", required=True, help="Tweet URL")
    args = parser.parse_args()

    try:
        resp = requests.post(
            f"{API_BASE}/like",
            json={"url": args.url},
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()

        if data.get("success"):
            print(f"✅ Liked successfully!")
        else:
            print(f"❌ Like failed: {data.get('reason', 'Unknown error')}")

    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to x-agent API at {API_BASE}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
