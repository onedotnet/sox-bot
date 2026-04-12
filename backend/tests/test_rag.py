import pytest
from community.knowledge.indexer import KnowledgeIndexer, Chunk


SAMPLE_MARKDOWN = """
# SoxAI Documentation

This is some intro text that is not under a ## heading.

## Getting Started

To get started with SoxAI, first install the SDK. Then configure your API key.
You can find your API key in the dashboard under Settings > API Keys.
Make sure to keep your key secure and never commit it to version control.

## Authentication

SoxAI uses Bearer token authentication. Include your API key in the Authorization header
for every request. Tokens can be scoped to specific models or rate limits.
Example: Authorization: Bearer sox_your_key_here

## Short Section

Too short.

## Model Routing

SoxAI supports routing requests to 40+ AI providers through a unified OpenAI-compatible API.
Configure routing rules in the dashboard or via the Admin API. Supports fallback chains,
priority routing, and session stickiness for consistent conversations.
"""


class TestChunkMarkdown:
    def test_splits_by_heading(self):
        indexer = KnowledgeIndexer(api_key="test-key")
        chunks = indexer.chunk_markdown(SAMPLE_MARKDOWN, "docs/getting_started.md")
        headings = [c.heading for c in chunks]
        assert "Getting Started" in headings
        assert "Authentication" in headings
        assert "Model Routing" in headings

    def test_skips_tiny_chunks(self):
        indexer = KnowledgeIndexer(api_key="test-key")
        chunks = indexer.chunk_markdown(SAMPLE_MARKDOWN, "docs/getting_started.md")
        # "Short Section" has content < 50 chars, should be skipped
        headings = [c.heading for c in chunks]
        assert "Short Section" not in headings

    def test_has_required_fields(self):
        indexer = KnowledgeIndexer(api_key="test-key")
        chunks = indexer.chunk_markdown(SAMPLE_MARKDOWN, "docs/test.md")
        assert len(chunks) > 0
        for chunk in chunks:
            assert isinstance(chunk, Chunk)
            assert chunk.source_file == "docs/test.md"
            assert isinstance(chunk.heading, str)
            assert isinstance(chunk.content, str)
            assert len(chunk.content) >= 50
            assert isinstance(chunk.chunk_index, int)
            assert chunk.chunk_index >= 0
