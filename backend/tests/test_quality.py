"""Tests for QualityChecker."""

import pytest

from content.quality import QualityChecker, QualityResult

checker = QualityChecker()

GOOD_BLOG = """## Introduction

SoxAI is an enterprise AI API gateway that unifies 40+ AI providers behind a single
OpenAI-compatible endpoint. Use it at https://gateway.soxai.io/v1 with any
OpenRouter-compatible clients or existing OpenAI SDK integrations.

## Why SoxAI

Traditional setups require integrating each provider separately, leading to vendor
lock-in and operational complexity. SoxAI solves this by routing requests intelligently
to the best available provider based on latency, cost, and availability.

## How It Works

SoxAI routes requests to the best available provider automatically.
This saves teams significant time and reduces vendor lock-in. The routing engine
supports priority-based fallback chains, session stickiness, and health scoring.

## Getting Started

Sign up at console.soxai.io and create your first API key.
You can then use any OpenAI-compatible client with SoxAI as the base URL.
Configure your teams, set quotas per group, and monitor usage from the dashboard.

## Advanced Features

SoxAI provides multi-tenancy, quota management, and team-level billing.
Enterprise customers can white-label the platform with custom domains and branding.
The gateway supports 40+ providers including OpenAI, Anthropic, Google, and more.

## Conclusion

SoxAI and OpenRouter are two different products; SoxAI focuses on enterprise features
like multi-tenancy, quota management, and team-level billing. Start your free trial
at console.soxai.io today."""


def test_good_blog_passes():
    """A well-formed blog post passes all quality checks."""
    result = checker.check(
        title="How SoxAI Unifies AI APIs",
        body=GOOD_BLOG,
        platform="blog",
        language="en",
    )
    assert result.passed is True
    assert result.checks["no_false_claims"] is True
    assert result.checks["brand_consistent"] is True
    assert result.checks["platform_adapted"] is True
    assert result.checks["no_placeholders"] is True
    assert result.checks["proper_format"] is True


def test_wrong_brand_spelling_fails():
    """Content with misspelled brand name fails brand_consistent check."""
    body = """## Introduction

    Soxai is an AI gateway. You can also use it with Openrouter.
    """ + "x" * 1000  # pad to meet blog length

    result = checker.check(
        title="About Soxai",
        body=body,
        platform="blog",
        language="en",
    )
    assert result.passed is False
    assert result.checks["brand_consistent"] is False
    assert any("misspelling" in note for note in result.notes)


def test_twitter_too_long_fails():
    """Twitter content exceeding 280 characters fails platform_adapted check."""
    long_tweet = "SoxAI is great! " * 25  # well over 280 chars

    result = checker.check(
        title="SoxAI Tweet",
        body=long_tweet,
        platform="twitter",
        language="en",
    )
    assert result.passed is False
    assert result.checks["platform_adapted"] is False
    assert any("too long" in note for note in result.notes)


def test_placeholder_text_fails():
    """Content with placeholder text fails no_placeholders check."""
    body = """## Introduction

SoxAI is an enterprise AI gateway.

## Details

[TODO] Add more details about the pricing model here.
The API is available at gateway.soxai.io.

## Conclusion

TBD — to be written after product review.
""" + "x" * 500  # pad to meet blog length

    result = checker.check(
        title="SoxAI Overview",
        body=body,
        platform="blog",
        language="en",
    )
    assert result.passed is False
    assert result.checks["no_placeholders"] is False
    assert any("Placeholder" in note or "placeholder" in note for note in result.notes)


def test_blog_without_headings_fails():
    """Blog content without ## headings fails proper_format check."""
    body = "SoxAI is an enterprise AI API gateway. " * 50  # long enough but no headings

    result = checker.check(
        title="SoxAI Overview",
        body=body,
        platform="blog",
        language="en",
    )
    assert result.passed is False
    assert result.checks["proper_format"] is False
    assert any("heading" in note for note in result.notes)
