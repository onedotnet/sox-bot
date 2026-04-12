"""Prompt templates and content type configuration for the content generator."""

from models.content import ContentType

OUTLINE_PROMPT = """You are a content strategist for SoxAI, an enterprise AI API gateway.

Create a detailed outline for a {content_type} about: {seo_keyword}
Target platform: {target_platform}
Language: {language}

Respond with valid JSON only:
{{
  "title": "The article title",
  "sections": [
    {{"heading": "Section heading", "key_points": ["point 1", "point 2"]}}
  ]
}}"""

BODY_PROMPT = """You are a technical writer for SoxAI, an enterprise AI API gateway that unifies 40+ AI providers.

Write a complete {content_type} based on this outline:
Title: {title}
Sections: {sections}

Keyword to target: {seo_keyword}
Platform: {target_platform}
Language: {language}

Write in {language}. Use markdown formatting with ## headings for sections.
Be accurate: SoxAI's API base URL is https://gateway.soxai.io/v1"""

SEO_PROMPT = """You are an SEO specialist. Review this article and provide optimization metadata.

Title: {title}
Body excerpt (first 500 chars): {body_excerpt}

Respond with valid JSON only:
{{
  "seo_title": "Optimized title (60 chars max)",
  "summary": "Meta description (150-160 chars)",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]
}}"""

TRANSLATE_PROMPT = """Translate the following content to {target_language}.
Preserve all markdown formatting and code blocks exactly.
Keep technical terms like SoxAI, OpenRouter, GPT-4o in their original form.

Content to translate:
{content}"""

CONTENT_TYPE_CONFIG: dict[ContentType, dict] = {
    ContentType.seo_article: {
        "min_words": 1000,
        "outline_model": "gpt-4o-mini",
        "body_model": "gpt-4o",
        "seo_model": "gpt-4o-mini",
        "description": "Long-form SEO article",
    },
    ContentType.industry_brief: {
        "min_words": 600,
        "outline_model": "gpt-4o-mini",
        "body_model": "gpt-4o",
        "seo_model": "gpt-4o-mini",
        "description": "Industry analysis brief",
    },
    ContentType.tutorial: {
        "min_words": 800,
        "outline_model": "gpt-4o-mini",
        "body_model": "gpt-4o",
        "seo_model": "gpt-4o-mini",
        "description": "Step-by-step tutorial",
    },
    ContentType.comparison: {
        "min_words": 700,
        "outline_model": "gpt-4o-mini",
        "body_model": "gpt-4o",
        "seo_model": "gpt-4o-mini",
        "description": "Product/feature comparison",
    },
    ContentType.changelog: {
        "min_words": 200,
        "outline_model": "gpt-4o-mini",
        "body_model": "gpt-4o",
        "seo_model": "gpt-4o-mini",
        "description": "Release changelog",
    },
    ContentType.social_post: {
        "min_words": 50,
        "outline_model": "gpt-4o-mini",
        "body_model": "gpt-4o",
        "seo_model": "gpt-4o-mini",
        "description": "Social media post",
    },
}
