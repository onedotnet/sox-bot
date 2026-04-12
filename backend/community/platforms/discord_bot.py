"""Discord bot for SoxAI community.

Proactive behaviors:
- Keyword trigger: auto-responds when relevant topics mentioned in group
- Daily tips: posts AI/API tips on schedule
- Lead sharing: forwards high-value ScoutBot discoveries to the group
"""

import random
import re
import discord
from discord.ext import commands, tasks

from database import async_session
from community.responder import CommunityResponder, WELCOME_MESSAGE
from models.knowledge import CommunityMessage


# Keywords that trigger the bot to join a conversation (without @mention)
TRIGGER_KEYWORDS = [
    r'\bai\s*api\b', r'\bllm\s*(proxy|gateway)\b', r'\bopenrouter\b',
    r'\bmulti.?model\b', r'\bfailover\b', r'\bapi\s*key\s*manag',
    r'\brate\s*limit', r'\bai\s*cost\b', r'\btoken\s*budget\b',
    r'\bgpt.?4\b.*\bclaude\b|\bclaude\b.*\bgpt.?4\b',  # mentions both providers
]
TRIGGER_PATTERN = re.compile('|'.join(TRIGGER_KEYWORDS), re.IGNORECASE)

# Don't respond to every keyword match — random chance to seem natural
KEYWORD_RESPONSE_CHANCE = 0.4  # 40% chance to respond to keyword triggers

DAILY_TIPS = [
    "tip of the day: if you're using multiple AI providers, put a gateway in front. one API key, one billing dashboard, automatic failover. saves hours of integration work.",
    "did you know? the price difference between GPT-4o and GPT-4o-mini is 10x, but for most classification tasks the quality difference is negligible. route smartly, save money.",
    "fun fact: most teams using AI APIs spend 60% of their budget on a model they could replace with a cheaper one for that specific task. audit your model-to-task mapping.",
    "quick tip: always set per-developer spending limits on AI API keys. one runaway loop can burn through $500 before anyone notices.",
    "pro tip: if your AI API provider goes down, your app goes down. multi-provider failover isn't a nice-to-have, it's table stakes for production.",
    "today's insight: the fastest way to cut AI API costs isn't negotiating with providers — it's using the right model for each task. classification → mini model, reasoning → full model.",
    "reminder: AI model pricing changes constantly. what was cheapest last month might not be cheapest now. automate your price comparison.",
]


class SoxBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)
        self._general_channel_id: int | None = None

    async def on_ready(self):
        print(f"SoxBot connected as {self.user}")
        print(f"Servers: {[g.name for g in self.guilds]}")

        # Find #general or first text channel for proactive posts
        for guild in self.guilds:
            for channel in guild.text_channels:
                if channel.name in ("general", "chat", "discussion"):
                    self._general_channel_id = channel.id
                    break
            if not self._general_channel_id and guild.text_channels:
                self._general_channel_id = guild.text_channels[0].id

        # Start scheduled tasks
        if not self.daily_tip.is_running():
            self.daily_tip.start()
        if not self.share_leads.is_running():
            self.share_leads.start()

    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        is_dm = isinstance(message.channel, discord.DMChannel)
        is_mention = self.user.mentioned_in(message)
        is_keyword = bool(TRIGGER_PATTERN.search(message.content))

        # Always respond to DMs and mentions
        if is_dm or is_mention:
            await self._respond(message, is_mention=is_mention)
            return

        # Keyword trigger — respond probabilistically to seem natural
        if is_keyword and random.random() < KEYWORD_RESPONSE_CHANCE:
            await self._respond(message, is_mention=False)

    async def _respond(self, message: discord.Message, is_mention: bool):
        async with async_session() as db:
            responder = CommunityResponder(db)
            clean_text = message.content
            if is_mention:
                clean_text = clean_text.replace(f"<@{self.user.id}>", "").strip()

            result = await responder.respond(clean_text, str(message.author.id))

            # Log
            msg_record = CommunityMessage(
                platform="discord",
                channel_id=str(message.channel.id),
                author_id=str(message.author.id),
                author_name=str(message.author),
                message_text=clean_text,
                intent=result.intent,
                response_text=result.text,
                escalated=result.escalate,
                is_lead=result.lead_signal.detected if result.lead_signal else False,
            )
            db.add(msg_record)
            await db.commit()

        await message.reply(result.text)

    @tasks.loop(hours=24)
    async def daily_tip(self):
        """Post a daily tip to the general channel."""
        if not self._general_channel_id:
            return
        channel = self.get_channel(self._general_channel_id)
        if channel:
            tip = random.choice(DAILY_TIPS)
            await channel.send(f"💡 **{tip}**")

    @daily_tip.before_loop
    async def before_daily_tip(self):
        await self.wait_until_ready()

    @tasks.loop(hours=6)
    async def share_leads(self):
        """Share high-value ScoutBot discoveries in the group."""
        if not self._general_channel_id:
            return
        channel = self.get_channel(self._general_channel_id)
        if not channel:
            return

        from sqlalchemy import select, and_
        from models.lead import Lead, LeadPriority, LeadStatus

        async with async_session() as db:
            # Find recent high-priority leads that haven't been shared
            result = await db.execute(
                select(Lead).where(
                    and_(
                        Lead.priority == LeadPriority.high,
                        Lead.status == LeadStatus.pending_review,
                    )
                ).order_by(Lead.detected_at.desc()).limit(1)
            )
            lead = result.scalar_one_or_none()

        if lead:
            text = lead.original_text[:300]
            if len(lead.original_text) > 300:
                text += "..."
            await channel.send(
                f"🔍 **Interesting discussion spotted on {lead.source}**\n\n"
                f"> {text}\n\n"
                f"[View thread]({lead.source_url})"
            )


def run_discord_bot():
    from config import settings
    token = settings.discord_token
    if not token:
        print("SOXBOT_DISCORD_TOKEN not set, skipping Discord bot")
        return
    bot = SoxBot()
    bot.run(token)
