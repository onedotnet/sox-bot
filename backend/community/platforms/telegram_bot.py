"""Telegram bot for SoxAI community support.

Proactive behaviors:
- Keyword trigger: auto-responds when relevant topics mentioned in group
- Daily tips: posts AI/API tips on schedule
- Lead sharing: forwards ScoutBot discoveries to the group
"""

import logging
import random
import re

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

# Keywords that trigger the bot to join conversation
TRIGGER_KEYWORDS = [
    r'\bai\s*api\b', r'\bllm\s*(proxy|gateway)\b', r'\bopenrouter\b',
    r'\bmulti.?model\b', r'\bfailover\b', r'\bapi\s*key\s*manag',
    r'\brate\s*limit', r'\bai\s*cost\b', r'\btoken\s*budget\b',
    r'\bgpt.?4\b.*\bclaude\b|\bclaude\b.*\bgpt.?4\b',
]
TRIGGER_PATTERN = re.compile('|'.join(TRIGGER_KEYWORDS), re.IGNORECASE)
KEYWORD_RESPONSE_CHANCE = 0.4

DAILY_TIPS = [
    "💡 tip: if you're using multiple AI providers, put a gateway in front. one API key, one billing dashboard, automatic failover.",
    "💡 did you know? GPT-4o-mini is 10x cheaper than GPT-4o, and for classification tasks the quality difference is negligible.",
    "💡 most teams spend 60% of their AI API budget on a model they could replace with a cheaper one for that task. audit your model-to-task mapping.",
    "💡 always set per-developer spending limits on AI API keys. one runaway loop = $500 gone before anyone notices.",
    "💡 if your AI API provider goes down, your app goes down. multi-provider failover is table stakes for production.",
    "💡 the fastest way to cut AI costs isn't negotiating — it's using the right model for each task. classification → mini, reasoning → full.",
    "💡 AI model pricing changes constantly. automate your price comparison.",
]

# Store group chat IDs for proactive posting
_group_chat_ids: set[int] = set()


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME_MESSAGE, disable_web_page_preview=True)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Ask me anything about SoxAI!\n\n"
        "Commands:\n"
        "/start — Welcome + getting started\n"
        "/help — This message\n"
        "/tip — Get a random AI API tip\n\n"
        "In groups: I'll join relevant conversations automatically."
    )


async def tip_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(random.choice(DAILY_TIPS))


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text
    user = update.message.from_user
    chat = update.message.chat

    # Track group chats for proactive posting
    if chat.type in ("group", "supergroup"):
        _group_chat_ids.add(chat.id)

    is_group = chat.type in ("group", "supergroup")
    is_mention = False
    is_reply_to_bot = False
    is_keyword = bool(TRIGGER_PATTERN.search(text))

    if is_group:
        bot_username = context.bot.username
        is_mention = f"@{bot_username}" in text
        is_reply_to_bot = (
            update.message.reply_to_message
            and update.message.reply_to_message.from_user
            and update.message.reply_to_message.from_user.id == context.bot.id
        )

        # In groups: respond to mentions, replies, or keyword triggers (probabilistic)
        if not is_mention and not is_reply_to_bot:
            if not (is_keyword and random.random() < KEYWORD_RESPONSE_CHANCE):
                return

        # Strip @mention
        if is_mention:
            text = text.replace(f"@{bot_username}", "").strip()

    if not text:
        return

    async with async_session() as db:
        responder = CommunityResponder(db)
        result = await responder.respond(text, str(user.id))

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


async def daily_tip_job(context: ContextTypes.DEFAULT_TYPE):
    """Send daily tip to all known group chats."""
    tip = random.choice(DAILY_TIPS)
    for chat_id in _group_chat_ids:
        try:
            await context.bot.send_message(chat_id=chat_id, text=tip)
        except Exception as e:
            logger.warning(f"Failed to send tip to {chat_id}: {e}")


async def share_leads_job(context: ContextTypes.DEFAULT_TYPE):
    """Share high-value ScoutBot leads in group chats."""
    from sqlalchemy import select, and_
    from models.lead import Lead, LeadPriority, LeadStatus

    async with async_session() as db:
        result = await db.execute(
            select(Lead).where(
                and_(
                    Lead.priority == LeadPriority.high,
                    Lead.status == LeadStatus.pending_review,
                )
            ).order_by(Lead.detected_at.desc()).limit(1)
        )
        lead = result.scalar_one_or_none()

    if not lead or not _group_chat_ids:
        return

    text = lead.original_text[:300]
    if len(lead.original_text) > 300:
        text += "..."

    msg = (
        f"🔍 *Interesting discussion on {lead.source}*\n\n"
        f"{text}\n\n"
        f"[View thread]({lead.source_url})"
    )

    for chat_id in _group_chat_ids:
        try:
            await context.bot.send_message(
                chat_id=chat_id, text=msg,
                parse_mode="Markdown",
                disable_web_page_preview=True,
            )
        except Exception as e:
            logger.warning(f"Failed to share lead to {chat_id}: {e}")


def run_telegram_bot():
    from config import settings
    token = settings.telegram_token
    if not token:
        print("SOXBOT_TELEGRAM_TOKEN not set, skipping Telegram bot")
        return

    app = Application.builder().token(token).build()

    # Command handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("tip", tip_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Scheduled jobs
    job_queue = app.job_queue
    job_queue.run_repeating(daily_tip_job, interval=86400, first=3600)  # first tip after 1h
    job_queue.run_repeating(share_leads_job, interval=21600, first=7200)  # every 6h, first after 2h

    print("Telegram bot starting (with proactive features)...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    run_telegram_bot()
