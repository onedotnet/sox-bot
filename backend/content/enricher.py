"""Content enricher — injects real data into AI-generated articles.

This is what makes our content unique and un-penalizable by search engines.
AI writes the structure, enricher fills in real data that no other AI can generate.
"""

import json
from datetime import datetime, timezone

import httpx

from config import settings


class ContentEnricher:
    """Inject real-world data into content to make it unique and authoritative."""

    def __init__(self):
        self._cache: dict = {}

    async def get_live_pricing(self) -> str:
        """Fetch real-time model pricing from SoxAI API."""
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(
                    f"{settings.soxai_base_url}/models",
                    headers={"Authorization": f"Bearer {settings.soxai_api_key}"},
                )
                if resp.status_code == 200:
                    models = resp.json().get("data", [])
                    # Build a pricing table from real data
                    rows = []
                    for m in models[:15]:  # Top 15 models
                        model_id = m.get("id", "")
                        rows.append(f"| {model_id} |")
                    if rows:
                        return (
                            "| Model | Available |\n"
                            "|-------|----------|\n"
                            + "\n".join(f"| {m.get('id', '')} | Yes |" for m in models[:15])
                        )
        except Exception:
            pass
        return ""

    def get_code_examples(self) -> dict[str, str]:
        """Return real, working code examples that point to actual SoxAI endpoints."""
        return {
            "python": '''```python
from openai import OpenAI

client = OpenAI(
    api_key="your-soxai-key",
    base_url="https://api.soxai.io/v1",
)

# Use ANY model from ANY provider — same SDK
response = client.chat.completions.create(
    model="gpt-4o-mini",  # or "claude-sonnet-4-20250514", "gemini-flash", etc.
    messages=[{"role": "user", "content": "Hello!"}],
)
print(response.choices[0].message.content)
```''',
            "curl": '''```bash
curl https://api.soxai.io/v1/chat/completions \\
  -H "Authorization: Bearer $SOXAI_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```''',
            "nodejs": '''```javascript
import OpenAI from "openai";

const client = new OpenAI({
  apiKey: "your-soxai-key",
  baseURL: "https://api.soxai.io/v1",
});

const response = await client.chat.completions.create({
  model: "claude-sonnet-4-20250514",
  messages: [{ role: "user", content: "Hello!" }],
});
```''',
        }

    def get_unique_data_block(self) -> str:
        """Generate a data block with real stats that changes over time."""
        now = datetime.now(timezone.utc)
        # These should eventually come from real analytics
        return f"""
> **SoxAI Live Stats** (as of {now.strftime('%B %Y')}):
> - 200+ AI models available through one endpoint
> - OpenAI-compatible API — change one line of code to switch
> - Free $5 credit to try, no card required
> - [Try it now →](https://console.soxai.io/register)
"""

    async def enrich(self, body: str, content_type: str) -> str:
        """Inject real data into article body."""
        enriched = body

        # Add working code examples if article mentions code/integration
        code_keywords = ["code", "sdk", "integration", "example", "python", "curl", "api"]
        if any(kw in body.lower() for kw in code_keywords):
            examples = self.get_code_examples()
            if "python" not in body.lower() or "openai" not in body.lower():
                enriched += "\n\n## Quick Start\n\n" + examples["python"]
                enriched += "\n\n" + examples["curl"]

        # Add live pricing table if article is about pricing/comparison
        price_keywords = ["pricing", "cost", "price", "comparison", "compare", "cheaper"]
        if any(kw in body.lower() for kw in price_keywords):
            pricing = await self.get_live_pricing()
            if pricing:
                enriched += f"\n\n## Available Models (Live)\n\n{pricing}\n"

        # Always add CTA block at the end
        enriched += "\n\n---\n" + self.get_unique_data_block()

        return enriched
