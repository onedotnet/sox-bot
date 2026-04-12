import json
import pytest
from community.intent import IntentClassifier


class TestIntentClassifier:
    def test_technical_classification(self, httpx_mock):
        httpx_mock.add_response(
            url="https://api.soxai.io/v1/chat/completions",
            json={
                "id": "mock-intent-1",
                "object": "chat.completion",
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": json.dumps({"intent": "technical", "confidence": 0.92}),
                    },
                    "finish_reason": "stop",
                }],
                "usage": {"prompt_tokens": 50, "completion_tokens": 20, "total_tokens": 70},
            },
        )
        classifier = IntentClassifier(api_key="test-key", base_url="https://api.soxai.io/v1")
        intent, confidence = classifier.classify(
            "How do I configure rate limiting for a specific model in SoxAI?"
        )
        assert intent == "technical"
        assert 0.0 <= confidence <= 1.0
        assert confidence > 0.5

    def test_enterprise_classification(self, httpx_mock):
        httpx_mock.add_response(
            url="https://api.soxai.io/v1/chat/completions",
            json={
                "id": "mock-intent-2",
                "object": "chat.completion",
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": json.dumps({"intent": "enterprise", "confidence": 0.88}),
                    },
                    "finish_reason": "stop",
                }],
                "usage": {"prompt_tokens": 50, "completion_tokens": 20, "total_tokens": 70},
            },
        )
        classifier = IntentClassifier(api_key="test-key", base_url="https://api.soxai.io/v1")
        intent, confidence = classifier.classify(
            "We have 500 developers and need SOC 2 compliance. What enterprise plans do you offer?"
        )
        assert intent == "enterprise"
        assert 0.0 <= confidence <= 1.0
        assert confidence > 0.5
