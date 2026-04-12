from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from community.intent import IntentClassifier
from community.lead_detector import LeadDetector, LeadSignal
from community.rag import RAGEngine, RAGResponse
from config import settings


@dataclass
class BotResponse:
    text: str
    intent: str
    escalate: bool
    lead_signal: LeadSignal | None


WELCOME_MESSAGE = """Welcome to the SoxAI community!

Here's how to get started:
- Quick Start: https://docs.soxai.io/quickstart
- Free $5 credit: https://console.soxai.io/register
- API Docs: https://docs.soxai.io/api-reference

Ask me anything about SoxAI!
If you're evaluating for your enterprise team, let me know and I'll connect you with our team."""


class CommunityResponder:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.intent_classifier = IntentClassifier(
            api_key=settings.soxai_api_key,
            base_url=settings.soxai_base_url,
        )
        self.lead_detector = LeadDetector()
        self.rag = RAGEngine(
            api_key=settings.soxai_api_key,
            base_url=settings.soxai_base_url,
        )

    async def respond(self, message: str, author_id: str) -> BotResponse:
        intent, confidence = self.intent_classifier.classify(message)
        lead_signal = self.lead_detector.detect(message)

        if intent == "beyond_scope":
            return BotResponse(
                text="That's outside my area of expertise. I'm best at helping with SoxAI and AI API questions!",
                intent=intent,
                escalate=False,
                lead_signal=lead_signal,
            )

        if intent == "newbie":
            return BotResponse(
                text=WELCOME_MESSAGE,
                intent=intent,
                escalate=False,
                lead_signal=lead_signal,
            )

        if intent == "chitchat":
            return BotResponse(
                text="Thanks for the message! If you have any technical questions about SoxAI, I'm here to help.",
                intent=intent,
                escalate=False,
                lead_signal=lead_signal,
            )

        if intent in ("technical", "enterprise"):
            chunks = await self.rag.search(message, self.db)
            if not chunks:
                return BotResponse(
                    text="I couldn't find relevant documentation for your question. Let me get a human colleague to help.",
                    intent=intent,
                    escalate=True,
                    lead_signal=lead_signal,
                )
            rag_response = self.rag.generate_answer(message, chunks)
            suffix = ""
            if lead_signal and lead_signal.detected:
                suffix = "\n\nIt sounds like you might benefit from our enterprise features. I'll flag this for our team to follow up!"
            return BotResponse(
                text=rag_response.answer + suffix,
                intent=intent,
                escalate=lead_signal.detected if lead_signal else False,
                lead_signal=lead_signal,
            )

        return BotResponse(
            text="Let me get a human colleague to help with this.",
            intent=intent,
            escalate=True,
            lead_signal=lead_signal,
        )
