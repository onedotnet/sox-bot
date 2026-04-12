import json

from openai import OpenAI

from analytics.aggregator import WeekMetrics
from config import settings

REPORT_PROMPT = """You are AnalyticsBot for sox.bot, generating a weekly operations report.

Given these metrics for the week, generate:
1. A markdown summary (3-5 paragraphs) highlighting key achievements, concerns, and trends
2. 3-5 specific action items for next week

Metrics:
{metrics}

Previous week metrics (for comparison):
{prev_metrics}

Output JSON with:
- "summary": markdown string
- "action_items": array of strings (each a specific, actionable recommendation)

Be specific and data-driven. Reference actual numbers. Prioritize actionable insights."""


class ReportGenerator:
    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        self.client = OpenAI(
            api_key=api_key or settings.soxai_api_key,
            base_url=base_url or settings.soxai_base_url,
        )

    def generate(
        self,
        current: WeekMetrics,
        previous: WeekMetrics | None = None,
    ) -> tuple[str, list[str]]:
        prev_str = (
            json.dumps(previous.__dict__)
            if previous is not None
            else "No previous data (first week)"
        )

        resp = self.client.chat.completions.create(
            model="claude-sonnet-4-20250514",
            messages=[
                {
                    "role": "system",
                    "content": "You are a data-driven marketing analyst. Output valid JSON only.",
                },
                {
                    "role": "user",
                    "content": REPORT_PROMPT.format(
                        metrics=json.dumps(current.__dict__),
                        prev_metrics=prev_str,
                    ),
                },
            ],
            temperature=0.5,
            response_format={"type": "json_object"},
        )

        data = json.loads(resp.choices[0].message.content)
        return data.get("summary", ""), data.get("action_items", [])
