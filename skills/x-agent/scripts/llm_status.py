#!/usr/bin/env python3
"""多 LLM 供应商状态检查"""
import json
import sys

import requests

API_BASE = "http://localhost:8000"


def main():
    print("\n🤖 LLM Provider Status\n")

    try:
        resp = requests.get(f"{API_BASE}/status", timeout=10)
        resp.raise_for_status()
        status = resp.json()

        current = status.get("llm_provider", "unknown")
        print(f"  Current provider: {current}")
        print(f"  Service: {status.get('service', 'N/A')}")
        print(f"  Version: {status.get('version', 'N/A')}")
        print()

        # Known providers
        providers = [
            ("Anthropic", "claude-3-5-sonnet-20241022", "Recommended"),
            ("OpenAI", "gpt-4o", ""),
            ("Groq", "llama-3.3-70b-versatile", "Free tier"),
            ("Gemini", "gemini-2.0-flash-exp", ""),
            ("OpenRouter", "varies", "Aggregated"),
            ("NVIDIA NIM", "varies", ""),
            ("Ollama", "local", "Always available"),
        ]

        print("  Supported providers (priority order):")
        for i, (name, model, note) in enumerate(providers, 1):
            marker = "➡️ " if name.lower() == current.lower() else "   "
            note_str = f" ({note})" if note else ""
            print(f"  {marker}{i}. {name}: {model}{note_str}")

        print(f"\n  Routing: Based on LLM_PROVIDER env var")
        print(f"  Fallback: Auto-switch on provider failure")
        print()

    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to x-agent API at {API_BASE}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
