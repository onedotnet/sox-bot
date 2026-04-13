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

BODY_PROMPT = """You are a senior developer writing a technical article. NOT a marketing writer.

Write based on this outline:
Title: {title}
Sections: {sections}
Keyword: {seo_keyword}
Language: {language}

CRITICAL RULES — violating these makes the article worthless:

1. WRITE LIKE A REAL DEVELOPER, NOT A CONTENT MILL:
   - Share specific technical details, not vague overviews
   - Include real problems you'd encounter and how to solve them
   - Have opinions. Say "this approach is better because..." not "there are various approaches"
   - Use "I" occasionally. "When I set this up..." or "In my experience..."

2. NO AI WRITING PATTERNS (search engines detect and penalize these):
   - NEVER start sections with "In today's rapidly evolving..." or "In the world of..."
   - NEVER use "Whether you're a... or a..." constructions
   - NEVER list 3 benefits then 3 challenges in perfect symmetry
   - NEVER end with "In conclusion, [restate everything]"
   - NEVER use filler phrases: "It's worth noting", "It goes without saying", "At the end of the day"
   - Vary paragraph length. Some 1 sentence, some 5 sentences. Not all 3.

3. ADD REAL VALUE THAT AI NORMALLY CAN'T:
   - Mention specific version numbers, dates, prices (even approximate)
   - Reference real tools by name, with honest opinions
   - Include edge cases and gotchas
   - When comparing, pick a winner. Don't say "it depends on your needs"

4. FORMATTING:
   - Use markdown with ## headings
   - Include code blocks where relevant (Python, curl, or JavaScript)
   - SoxAI's API base URL is https://api.soxai.io/v1
   - Keep it practical and scannable"""

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
