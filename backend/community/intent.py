import json

import httpx

INTENT_SYSTEM = """You are an intent classifier for community messages about AI API gateway products.
Classify messages into exactly one of these intents:
- technical: technical questions about APIs, integrations, configurations, debugging
- newbie: basic questions from beginners who are just getting started
- chitchat: casual conversation, greetings, off-topic discussion
- enterprise: questions about enterprise features, pricing, compliance, SLA, large-scale deployment
- beyond_scope: questions unrelated to AI APIs or the product

Respond with ONLY a JSON object in this exact format:
{"intent": "<intent>", "confidence": <float between 0.0 and 1.0>}"""

VALID_INTENTS = {"technical", "newbie", "chitchat", "enterprise", "beyond_scope"}


class IntentClassifier:
    def __init__(self, api_key: str, base_url: str = "https://api.soxai.io/v1"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    def classify(self, message: str) -> tuple[str, float]:
        """Classify a message and return (intent, confidence)."""
        with httpx.Client() as client:
            response = client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": INTENT_SYSTEM},
                        {"role": "user", "content": message},
                    ],
                    "temperature": 0.1,
                },
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()

        raw = data["choices"][0]["message"]["content"].strip()
        parsed = json.loads(raw)
        intent = parsed.get("intent", "beyond_scope")
        confidence = float(parsed.get("confidence", 0.5))

        if intent not in VALID_INTENTS:
            intent = "beyond_scope"

        return intent, confidence
