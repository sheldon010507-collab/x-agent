#!/usr/bin/env python3
"""配置验证 — 检查所有环境变量和服务状态"""
import json
import sys

import requests

API_BASE = "http://localhost:8000"


def main():
    print("\n🔧 X-Agent Configuration Validator\n")

    # Check API connectivity
    try:
        resp = requests.get(f"{API_BASE}/health", timeout=5)
        resp.raise_for_status()
        print("  ✅ x-agent API: Connected")
    except Exception:
        print("  ❌ x-agent API: Not reachable")
        print(f"     Expected at: {API_BASE}")
        print("     Run: docker-compose up x-agent-api")
        sys.exit(1)

    # Check system status
    try:
        resp = requests.get(f"{API_BASE}/status", timeout=10)
        resp.raise_for_status()
        status = resp.json()

        provider = status.get("llm_provider", "unknown")
        niche = status.get("niche", "unknown")
        print(f"  ✅ LLM Provider: {provider}")
        print(f"  ✅ Current Niche: {niche}")

    except Exception as e:
        print(f"  ⚠️  Status check failed: {e}")

    # Check trends endpoint (basic connectivity)
    try:
        resp = requests.get(
            f"{API_BASE}/trends",
            params={"niche": "test", "sources": "hackernews", "days": 1},
            timeout=30,
        )
        if resp.status_code == 200:
            print("  ✅ Trends API: Working")
        else:
            print(f"  ⚠️  Trends API: Status {resp.status_code}")
    except Exception as e:
        print(f"  ⚠️  Trends API: {e}")

    # Check DMs endpoint
    try:
        resp = requests.get(f"{API_BASE}/dms", timeout=10)
        if resp.status_code == 200:
            print("  ✅ DM Monitor: Configured")
        elif resp.status_code == 400:
            print("  ⚠️  DM Monitor: X credentials not configured")
        else:
            print(f"  ⚠️  DM Monitor: Status {resp.status_code}")
    except Exception:
        print("  ⚠️  DM Monitor: Not available")

    print("\n📋 Summary:")
    print("  - Ensure X_USERNAME and X_PASSWORD are set for DM monitoring and posting")
    print("  - Ensure at least one LLM API key is configured")
    print("  - Optional: SUPABASE_URL/KEY for cloud database")
    print("  - Optional: REDDIT_CLIENT_ID/SECRET for Reddit search")
    print()


if __name__ == "__main__":
    main()
