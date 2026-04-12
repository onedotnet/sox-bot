import os
import discord
from discord.ext import commands
from database import async_session
from community.responder import CommunityResponder, WELCOME_MESSAGE
from models.knowledge import CommunityMessage


class SoxBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix="!", intents=intents)

    async def on_ready(self):
        print(f"SoxBot connected as {self.user}")

    async def on_member_join(self, member: discord.Member):
        try:
            await member.send(WELCOME_MESSAGE)
        except discord.Forbidden:
            pass

    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if not self.user.mentioned_in(message) and not isinstance(message.channel, discord.DMChannel):
            return

        async with async_session() as db:
            responder = CommunityResponder(db)
            clean_text = message.content.replace(f"<@{self.user.id}>", "").strip()
            result = await responder.respond(clean_text, str(message.author.id))

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


def run_discord_bot():
    from config import settings
    token = settings.discord_token
    if not token:
        print("SOXBOT_DISCORD_TOKEN not set, skipping Discord bot")
        return
    bot = SoxBot()
    bot.run(token)
