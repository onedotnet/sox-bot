"""Telegram bot for SoxAI community support.

Reuses the same CommunityResponder as Discord — RAG answers, intent
classification, enterprise lead detection.

Setup:
  1. Message @BotFather on Telegram → /newbot → get token
  2. Set SOXBOT_TELEGRAM_TOKEN in .env
  3. Run: python -m community.platforms.telegram_bot
"""

import asyncio
import logging
import os

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from database import async_session
from community.responder import CommunityResponder, WELCOME_MESSAGE
from models.knowledge import CommunityMessage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command — send welcome message."""
    await update.message.reply_text(
        WELCOME_MESSAGE,
        disable_web_page_preview=True,
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    await update.message.reply_text(
        "Ask me anything about SoxAI!\n\n"
        "Commands:\n"
        "/start — Welcome message + getting started links\n"
        "/help — This help message\n\n"
        "Just type your question and I'll answer based on SoxAI documentation."
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages — route through CommunityResponder."""
    if not update.message or not update.message.text:
        return

    text = update.message.text
    user = update.message.from_user
    chat = update.message.chat

    # In groups, only respond to mentions or replies to the bot
    if chat.type in ("group", "supergroup"):
        bot_username = context.bot.username
        if not (
            f"@{bot_username}" in text
            or (update.message.reply_to_message
                and update.message.reply_to_message.from_user
                and update.message.reply_to_message.from_user.id == context.bot.id)
        ):
            return
        # Strip the @mention
        text = text.replace(f"@{bot_username}", "").strip()

    if not text:
        return

    async with async_session() as db:
        responder = CommunityResponder(db)
        result = await responder.respond(text, str(user.id))

        # Log message
        msg_record = CommunityMessage(
            platform="telegram",
            channel_id=str(chat.id),
            author_id=str(user.id),
            author_name=user.full_name or user.username or "unknown",
            message_text=text,
            intent=result.intent,
            response_text=result.text,
            escalated=result.escalate,
            is_lead=result.lead_signal.detected if result.lead_signal else False,
        )
        db.add(msg_record)
        await db.commit()

    await update.message.reply_text(result.text, disable_web_page_preview=True)


def run_telegram_bot():
    """Start the Telegram bot."""
    from config import settings
    token = settings.telegram_token
    if not token:
        print("SOXBOT_TELEGRAM_TOKEN not set, skipping Telegram bot")
        return

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Telegram bot starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    run_telegram_bot()
