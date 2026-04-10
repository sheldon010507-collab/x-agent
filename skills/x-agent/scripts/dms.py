#!/usr/bin/env python3
"""查看/监控 X 私信 — 指纹浏览器"""
import argparse
import json
import sys
import time

import requests

API_BASE = "http://localhost:8000"


def fetch_dms():
    """Fetch DMs from API"""
    resp = requests.get(f"{API_BASE}/dms", timeout=120)
    resp.raise_for_status()
    return resp.json()


def main():
    parser = argparse.ArgumentParser(description="View/monitor X DMs")
    parser.add_argument("--monitor", action="store_true", help="Enable background monitoring")
    parser.add_argument("--interval", type=int, default=300, help="Monitor interval in seconds (default: 300)")
    args = parser.parse_args()

    if args.monitor:
        print(f"👁️  DM monitoring started (interval: {args.interval}s)")
        print("   Press Ctrl+C to stop\n")
        seen_ids = set()

        try:
            while True:
                try:
                    data = fetch_dms()
                    dms = data.get("dms", [])

                    new_dms = []
                    for dm in dms:
                        conv_id = dm.get("conv_id", dm.get("sender", ""))
                        if conv_id and conv_id not in seen_ids:
                            if seen_ids:  # Skip first round (everything is "new")
                                new_dms.append(dm)
                            seen_ids.add(conv_id)

                    if new_dms:
                        print(f"\n🔔 {len(new_dms)} new message(s) at {time.strftime('%H:%M:%S')}:")
                        for dm in new_dms:
                            sender = dm.get("sender", "Unknown")
                            preview = dm.get("preview", "")[:60]
                            print(f"   📩 {sender}: {preview}")

                except Exception as e:
                    print(f"⚠️  Check failed: {e}")

                time.sleep(args.interval)

        except KeyboardInterrupt:
            print("\n\n👋 Monitoring stopped.")
    else:
        # One-time fetch
        try:
            data = fetch_dms()
            dms = data.get("dms", [])
            total = data.get("total", 0)

            print(f"\n📨 X Direct Messages ({total} conversations)\n")

            if not dms:
                print("  No messages found.")
                return

            for i, dm in enumerate(dms, 1):
                sender = dm.get("sender", "Unknown")
                preview = dm.get("preview", "")[:80]
                is_unread = dm.get("is_unread", False)
                timestamp = dm.get("timestamp", "")
                unread_icon = "🔴" if is_unread else "⚪"

                print(f"  {unread_icon} {i:2d}. {sender}")
                print(f"       {preview}")
                if timestamp:
                    print(f"       {timestamp}")
                print()

        except requests.exceptions.ConnectionError:
            print(f"❌ Cannot connect to x-agent API at {API_BASE}")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Error: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
