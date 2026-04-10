#!/usr/bin/env python3
"""转发指定推文"""
import argparse
import sys

import requests

API_BASE = "http://localhost:8000"


def main():
    parser = argparse.ArgumentParser(description="Retweet a tweet")
    parser.add_argument("--url", required=True, help="Tweet URL")
    parser.add_argument("--comment", default=None, help="Quote comment (optional)")
    args = parser.parse_args()

    try:
        resp = requests.post(
            f"{API_BASE}/retweet",
            json={
                "url": args.url,
                "comment": args.comment,
            },
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()

        if data.get("success"):
            print(f"✅ Retweeted successfully!")
        else:
            print(f"❌ Retweet failed: {data.get('reason', 'Unknown error')}")

    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to x-agent API at {API_BASE}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
