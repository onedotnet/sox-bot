import pytest
from community.lead_detector import LeadDetector, LeadSignal


class TestLeadDetector:
    def setup_method(self):
        self.detector = LeadDetector()

    def test_team_size(self):
        signal = self.detector.detect("We have 50 developers and need a unified AI API gateway.")
        assert signal.detected is True
        assert signal.signal_type == "team_size"
        assert signal.confidence > 0.5

    def test_budget_high_confidence(self):
        signal = self.detector.detect("What is the pricing for 10M tokens per month? Our budget is $5000.")
        assert signal.detected is True
        assert signal.signal_type == "budget"
        assert signal.confidence >= 0.85

    def test_compliance_chinese(self):
        signal = self.detector.detect("我们需要符合GDPR合规要求，请问SoxAI有数据合规认证吗？")
        assert signal.detected is True
        assert signal.signal_type == "compliance"
        assert signal.confidence > 0.5

    def test_procurement(self):
        signal = self.detector.detect(
            "Our procurement team needs a vendor evaluation before we can sign a contract."
        )
        assert signal.detected is True
        assert signal.signal_type == "procurement"
        assert signal.confidence > 0.5

    def test_no_signal_for_normal_question(self):
        signal = self.detector.detect("How do I make an API call with Python?")
        assert signal.detected is False
        assert signal.signal_type == "none"
        assert signal.confidence == 0.0

    def test_migration(self):
        signal = self.detector.detect(
            "We are currently using OpenAI direct and want to migrate to SoxAI for better routing."
        )
        assert signal.detected is True
        assert signal.signal_type == "migration"
        assert signal.confidence > 0.5
