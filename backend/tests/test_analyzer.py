import pytest
from scout.analyzer import ScoutAnalyzer, AnalysisResult


class TestAnalyzePost:
    def test_returns_analysis_result(self, mock_soxai):
        mock_soxai()
        analyzer = ScoutAnalyzer(api_key="test-key", base_url="https://api.soxai.io/v1")
        result = analyzer.analyze_post(
            text="We have 30 developers and need a unified AI API gateway",
            source="reddit",
            subreddit="r/devops",
        )
        assert isinstance(result, AnalysisResult)
        assert 0 <= result.relevance_score <= 100
        assert result.intent in ("help_seeking", "complaint", "comparison", "technical", "enterprise")
        assert result.sentiment in ("positive", "negative", "neutral", "frustrated")
        assert len(result.suggested_reply) > 0

    def test_low_relevance_for_unrelated(self, mock_soxai):
        mock_soxai(relevance=15, intent="technical", sentiment="neutral")
        analyzer = ScoutAnalyzer(api_key="test-key", base_url="https://api.soxai.io/v1")
        result = analyzer.analyze_post(
            text="Best recipe for chocolate chip cookies",
            source="reddit",
            subreddit="r/cooking",
        )
        assert result.relevance_score < 30
