"""Multi-model content generator using the SoxAI API."""

import json
from dataclasses import dataclass, field

import httpx

from config import settings
from content.templates import (
    BODY_PROMPT,
    CONTENT_TYPE_CONFIG,
    OUTLINE_PROMPT,
    SEO_PROMPT,
    TRANSLATE_PROMPT,
)
from models.content import ContentLanguage, ContentType


@dataclass
class GeneratedContent:
    title: str
    body: str
    summary: str
    seo_tags: list[str]
    outline_model: str
    body_model: str
    cost_estimate_cents: int = 0
    seo_model: str = "openai/gpt-4o-mini"
    translate_model: str | None = None
    translated_body: str | None = None


class ContentGenerator:
    """Generates content using a 3-step multi-model pipeline via SoxAI API."""

    TRANSLATE_MODEL = "openai/gpt-4o"

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client
        self._owns_client = client is None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=settings.soxai_base_url,
                headers={"Authorization": f"Bearer {settings.soxai_api_key}"},
                timeout=300.0,
            )
        return self._client

    async def _chat(self, model: str, prompt: str) -> str:
        client = await self._get_client()
        response = await client.post(
            "/chat/completions",
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]

    async def generate(
        self,
        content_type: ContentType,
        seo_keyword: str,
        language: ContentLanguage,
        target_platform: str,
    ) -> GeneratedContent:
        config = CONTENT_TYPE_CONFIG[content_type]
        outline_model = config["outline_model"]
        body_model = config["body_model"]
        seo_model = config["seo_model"]

        # Step 1: Generate outline with DeepSeek
        outline_prompt = OUTLINE_PROMPT.format(
            content_type=content_type.value,
            seo_keyword=seo_keyword,
            target_platform=target_platform,
            language=language.value,
        )
        outline_raw = await self._chat(outline_model, outline_prompt)
        outline = self._parse_json(outline_raw)
        title = outline.get("title", seo_keyword)
        sections = outline.get("sections", [])

        # Step 2: Generate body with Claude Sonnet
        body_prompt = BODY_PROMPT.format(
            content_type=content_type.value,
            title=title,
            sections=json.dumps(sections, ensure_ascii=False),
            seo_keyword=seo_keyword,
            target_platform=target_platform,
            language=language.value,
        )
        body = await self._chat(body_model, body_prompt)

        # Step 3: SEO optimization with GPT-4o-mini
        seo_prompt = SEO_PROMPT.format(
            title=title,
            body_excerpt=body[:500],
        )
        seo_raw = await self._chat(seo_model, seo_prompt)
        seo_data = self._parse_json(seo_raw)
        summary = seo_data.get("summary", "")
        seo_title = seo_data.get("seo_title", title)
        seo_tags = seo_data.get("tags", [])

        return GeneratedContent(
            title=seo_title,
            body=body,
            summary=summary,
            seo_tags=seo_tags,
            outline_model=outline_model,
            body_model=body_model,
            seo_model=seo_model,
            cost_estimate_cents=0,
        )

    async def translate(
        self,
        content: str,
        target_language: ContentLanguage,
    ) -> str:
        prompt = TRANSLATE_PROMPT.format(
            target_language=target_language.value,
            content=content,
        )
        translated = await self._chat(self.TRANSLATE_MODEL, prompt)
        return translated

    async def close(self) -> None:
        if self._owns_client and self._client is not None:
            await self._client.aclose()
            self._client = None

    @staticmethod
    def _parse_json(text: str) -> dict:
        """Extract and parse JSON from a model response, stripping markdown fences."""
        text = text.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            # Drop first and last fence lines
            inner = lines[1:-1] if lines[-1].startswith("```") else lines[1:]
            text = "\n".join(inner).strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {}
