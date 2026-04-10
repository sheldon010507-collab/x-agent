#!/usr/bin/env python3
"""AI 内容生成 — 推文 / 视频脚本 / 智能评论"""
import argparse
import json
import sys

import requests

API_BASE = "http://localhost:8000"


def main():
    parser = argparse.ArgumentParser(description="Generate AI content")
    parser.add_argument("topic", help="Topic or tweet content (for comments)")
    parser.add_argument(
        "--type",
        choices=["tweet", "video", "comment"],
        default="tweet",
        help="Content type: tweet (Type A), video (Type B), comment (Type C)",
    )
    parser.add_argument("--niche", default="general", help="Niche: general/ai_tools/crypto/beauty/fitness/humor/adult")
    parser.add_argument("--summary", default="", help="Optional background info")
    parser.add_argument("--style", default="conversational", help="Comment style (for type=comment)")
    args = parser.parse_args()

    try:
        if args.type == "tweet":
            resp = requests.post(
                f"{API_BASE}/create",
                json={
                    "topic": args.topic,
                    "niche": args.niche,
                    "type": "A",
                    "summary": args.summary,
                },
                timeout=60,
            )
            resp.raise_for_status()
            data = resp.json()

            print(f"\n✍️  Tweet drafts for \"{args.topic}\" (niche: {args.niche})\n")
            result = data.get("result", {})
            for i, tweet in enumerate(result.get("tweets", []), 1):
                angle = tweet.get("angle", "")
                content = tweet.get("content", "")
                tags = " ".join(tweet.get("hashtags", []))
                print(f"  {i}. [{angle}]")
                print(f"     {content}")
                if tags:
                    print(f"     {tags}")
                print()

        elif args.type == "video":
            resp = requests.post(
                f"{API_BASE}/create",
                json={
                    "topic": args.topic,
                    "niche": args.niche,
                    "type": "B",
                    "summary": args.summary,
                },
                timeout=60,
            )
            resp.raise_for_status()
            data = resp.json()

            print(f"\n🎬 Video script for \"{args.topic}\" (niche: {args.niche})\n")
            result = data.get("result", {})
            script = result.get("script", {})
            print(f"  Title: {result.get('title', 'N/A')}")
            print(f"  Angle: {result.get('angle', 'N/A')}")
            print()
            for section in ["hook", "body", "cta"]:
                s = script.get(section, {})
                print(f"  [{s.get('time', '')}] {section.upper()}")
                print(f"    {s.get('content', 'N/A')}")
            print(f"\n  Caption: {result.get('caption', '')}")
            print(f"  Hashtags: {' '.join(result.get('hashtags', []))}")
            print(f"  Best posting time: {result.get('best_posting_time', 'N/A')}")

        elif args.type == "comment":
            # Comment generation uses /create with type A but different prompt
            # For now, call the API and format
            resp = requests.post(
                f"{API_BASE}/create",
                json={
                    "topic": args.topic,
                    "niche": args.niche,
                    "type": "A",
                    "summary": f"Generate comments for this tweet: {args.topic}",
                },
                timeout=60,
            )
            resp.raise_for_status()
            data = resp.json()

            print(f"\n💬 Comment options (niche: {args.niche}, style: {args.style})\n")
            result = data.get("result", {})
            for i, tweet in enumerate(result.get("tweets", []), 1):
                content = tweet.get("content", "")
                print(f"  {i}. {content}")
            print()

    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to x-agent API at {API_BASE}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
