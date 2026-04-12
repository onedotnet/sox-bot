"""Tests for ContentGenerator using mocked SoxAI API responses."""

import json

import pytest
import pytest_asyncio

from content.generator import ContentGenerator, GeneratedContent
from models.content import ContentLanguage, ContentType


MOCK_OUTLINE = {
    "title": "How to Unify AI APIs with SoxAI",
    "sections": [
        {"heading": "Introduction", "key_points": ["What is API unification", "Why it matters"]},
        {"heading": "Getting Started", "key_points": ["Installation", "Configuration"]},
    ],
}

MOCK_BODY = """## Introduction

Unifying AI APIs is a critical challenge for modern applications. SoxAI provides a single endpoint
at https://gateway.soxai.io/v1 that routes to 40+ providers.

## Getting Started

First, install the SoxAI SDK. Then configure your API key and base URL."""

MOCK_SEO = {
    "seo_title": "Unify AI APIs with SoxAI Gateway",
    "summary": "Learn how SoxAI unifies 40+ AI providers behind a single OpenAI-compatible endpoint.",
    "tags": ["AI gateway", "API unification", "SoxAI", "LLM routing", "enterprise AI"],
}


def _make_completion_response(content: str) -> dict:
    return {
        "id": "mock-id",
        "object": "chat.completion",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 100, "completion_tokens": 200, "total_tokens": 300},
    }


@pytest.mark.asyncio
async def test_generate_calls_three_models_in_sequence(httpx_mock):
    """Generator calls outline model, body model, SEO model in order."""
    # Response 1: outline (DeepSeek)
    httpx_mock.add_response(
        url="https://api.soxai.io/v1/chat/completions",
        json=_make_completion_response(json.dumps(MOCK_OUTLINE)),
    )
    # Response 2: body (Claude Sonnet)
    httpx_mock.add_response(
        url="https://api.soxai.io/v1/chat/completions",
        json=_make_completion_response(MOCK_BODY),
    )
    # Response 3: SEO (GPT-4o-mini)
    httpx_mock.add_response(
        url="https://api.soxai.io/v1/chat/completions",
        json=_make_completion_response(json.dumps(MOCK_SEO)),
    )

    import httpx as httpx_lib

    async with httpx_lib.AsyncClient(
        base_url="https://api.soxai.io/v1",
        headers={"Authorization": "Bearer test-key"},
    ) as client:
        generator = ContentGenerator(client=client)
        result = await generator.generate(
            content_type=ContentType.seo_article,
            seo_keyword="AI API gateway",
            language=ContentLanguage.en,
            target_platform="blog",
        )

    assert isinstance(result, GeneratedContent)
    assert result.title == MOCK_SEO["seo_title"]
    assert result.body == MOCK_BODY
    assert result.summary == MOCK_SEO["summary"]
    assert result.seo_tags == MOCK_SEO["tags"]
    assert result.outline_model == "gpt-4o-mini"
    assert result.body_model == "anthropic/claude-sonnet-4-5"
    assert result.seo_model == "openai/gpt-4o-mini"


@pytest.mark.asyncio
async def test_generate_handles_json_fenced_outline(httpx_mock):
    """Generator correctly strips markdown code fences from JSON responses."""
    fenced = f"```json\n{json.dumps(MOCK_OUTLINE)}\n```"

    httpx_mock.add_response(
        url="https://api.soxai.io/v1/chat/completions",
        json=_make_completion_response(fenced),
    )
    httpx_mock.add_response(
        url="https://api.soxai.io/v1/chat/completions",
        json=_make_completion_response(MOCK_BODY),
    )
    httpx_mock.add_response(
        url="https://api.soxai.io/v1/chat/completions",
        json=_make_completion_response(json.dumps(MOCK_SEO)),
    )

    import httpx as httpx_lib

    async with httpx_lib.AsyncClient(
        base_url="https://api.soxai.io/v1",
        headers={"Authorization": "Bearer test-key"},
    ) as client:
        generator = ContentGenerator(client=client)
        result = await generator.generate(
            content_type=ContentType.tutorial,
            seo_keyword="AI gateway tutorial",
            language=ContentLanguage.en,
            target_platform="blog",
        )

    assert result.title == MOCK_SEO["seo_title"]


@pytest.mark.asyncio
async def test_translate_calls_gpt4o(httpx_mock):
    """Translate method uses GPT-4o model."""
    translated_text = "如何使用 SoxAI 统一 AI API"

    httpx_mock.add_response(
        url="https://api.soxai.io/v1/chat/completions",
        json=_make_completion_response(translated_text),
    )

    import httpx as httpx_lib

    async with httpx_lib.AsyncClient(
        base_url="https://api.soxai.io/v1",
        headers={"Authorization": "Bearer test-key"},
    ) as client:
        generator = ContentGenerator(client=client)
        result = await generator.translate(
            content="How to unify AI APIs with SoxAI",
            target_language=ContentLanguage.zh,
        )

    assert result == translated_text


@pytest.mark.asyncio
async def test_generate_social_post_type(httpx_mock):
    """Generator works for social_post content type."""
    social_outline = {"title": "SoxAI Launch", "sections": []}
    social_body = "🚀 SoxAI now supports 40+ AI providers! Try it at gateway.soxai.io"
    social_seo = {
        "seo_title": "SoxAI Launch",
        "summary": "SoxAI supports 40+ AI providers.",
        "tags": ["SoxAI", "AI"],
    }

    httpx_mock.add_response(
        url="https://api.soxai.io/v1/chat/completions",
        json=_make_completion_response(json.dumps(social_outline)),
    )
    httpx_mock.add_response(
        url="https://api.soxai.io/v1/chat/completions",
        json=_make_completion_response(social_body),
    )
    httpx_mock.add_response(
        url="https://api.soxai.io/v1/chat/completions",
        json=_make_completion_response(json.dumps(social_seo)),
    )

    import httpx as httpx_lib

    async with httpx_lib.AsyncClient(
        base_url="https://api.soxai.io/v1",
        headers={"Authorization": "Bearer test-key"},
    ) as client:
        generator = ContentGenerator(client=client)
        result = await generator.generate(
            content_type=ContentType.social_post,
            seo_keyword="AI gateway launch",
            language=ContentLanguage.en,
            target_platform="twitter",
        )

    assert result.body == social_body
