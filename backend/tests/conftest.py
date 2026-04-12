import json
import pytest


@pytest.fixture
def mock_soxai(httpx_mock):
    """Mock SoxAI API for CI testing"""
    def _mock(relevance=85, intent="enterprise", sentiment="frustrated"):
        httpx_mock.add_response(
            url="https://api.soxai.io/v1/chat/completions",
            json={
                "id": "mock-1",
                "object": "chat.completion",
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": json.dumps({
                            "relevance_score": relevance,
                            "intent": intent,
                            "sentiment": sentiment,
                            "priority": "high" if relevance >= 80 else ("medium" if relevance >= 60 else "low"),
                            "suggested_reply": "Great question! For multi-provider routing, you might want to look at using an API gateway that unifies different providers behind a single endpoint."
                        })
                    },
                    "finish_reason": "stop",
                }],
                "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
            },
        )
    return _mock
