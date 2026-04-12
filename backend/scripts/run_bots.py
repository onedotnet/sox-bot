#!/usr/bin/env python3
"""Start all community bots (Discord + Telegram).

Usage:
    python scripts/run_bots.py              # Start all configured bots
    python scripts/run_bots.py discord      # Start Discord only
    python scripts/run_bots.py telegram     # Start Telegram only
"""
import asyncio
import multiprocessing
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings


def start_discord():
    from community.platforms.discord_bot import run_discord_bot
    run_discord_bot()


def start_telegram():
    from community.platforms.telegram_bot import run_telegram_bot
    run_telegram_bot()


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "all"

    processes = []

    if target in ("all", "discord") and settings.discord_token:
        p = multiprocessing.Process(target=start_discord, name="discord-bot")
        processes.append(("Discord", p))
    elif target == "discord":
        print("SOXBOT_DISCORD_TOKEN not set. Skipping Discord.")

    if target in ("all", "telegram") and settings.telegram_token:
        p = multiprocessing.Process(target=start_telegram, name="telegram-bot")
        processes.append(("Telegram", p))
    elif target == "telegram":
        print("SOXBOT_TELEGRAM_TOKEN not set. Skipping Telegram.")

    if not processes:
        print("No bots configured. Set SOXBOT_DISCORD_TOKEN and/or SOXBOT_TELEGRAM_TOKEN in .env")
        print("\nDiscord setup: https://discord.com/developers/applications")
        print("Telegram setup: Message @BotFather on Telegram → /newbot")
        sys.exit(1)

    for name, p in processes:
        print(f"Starting {name} bot...")
        p.start()

    print(f"\n{len(processes)} bot(s) running. Press Ctrl+C to stop.\n")

    try:
        for _, p in processes:
            p.join()
    except KeyboardInterrupt:
        print("\nStopping bots...")
        for _, p in processes:
            p.terminate()


if __name__ == "__main__":
    main()
