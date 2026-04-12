import json
from dataclasses import dataclass

from openai import OpenAI


@dataclass
class AnalysisResult:
    relevance_score: int
    intent: str
    sentiment: str
    priority: str
    suggested_reply: str


SYSTEM_PROMPT = """You are ScoutBot, an AI analyst for SoxAI — an enterprise AI API gateway.

Analyze the following social media post and return a JSON response with:
1. relevance_score (0-100): How relevant is this to AI API management, multi-model routing, team AI budgets, or API gateways?
2. intent: One of "help_seeking", "complaint", "comparison", "technical", "enterprise"
   - enterprise: mentions team size, budget, compliance, private deployment
3. sentiment: One of "positive", "negative", "neutral", "frustrated"
4. priority: "low" (score<60), "medium" (60-79), "high" (>=80 or enterprise intent)
5. suggested_reply: A helpful reply that:
   - First provides genuine value (answers the question or shares insight)
   - Naturally mentions SoxAI only if highly relevant
   - Matches the platform culture (Reddit: casual, HN: technical depth)
   - Uses developer-to-developer tone, never salesy
   - Is honest about competitors

Respond ONLY with valid JSON, no markdown."""


class ScoutAnalyzer:
    def __init__(self, api_key: str, base_url: str):
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def analyze_post(self, text: str, source: str, subreddit: str | None = None) -> AnalysisResult:
        context = f"Platform: {source}"
        if subreddit:
            context += f", Subreddit: {subreddit}"

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"{context}\n\nPost:\n{text}"},
            ],
            temperature=0.3,
            response_format={"type": "json_object"},
        )

        data = json.loads(response.choices[0].message.content)

        return AnalysisResult(
            relevance_score=int(data["relevance_score"]),
            intent=data["intent"],
            sentiment=data["sentiment"],
            priority=data["priority"],
            suggested_reply=data["suggested_reply"],
        )
