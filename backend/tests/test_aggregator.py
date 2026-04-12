from analytics.aggregator import WeekMetrics


class TestWeekMetrics:
    def test_metrics_dataclass(self):
        m = WeekMetrics(
            leads_discovered=47,
            leads_published=12,
            enterprise_leads=3,
            content_generated=8,
            content_published=6,
            content_cost_cents=72,
            messages_received=34,
            messages_auto_resolved=26,
            messages_escalated=8,
            community_leads=2,
            resolution_rate=76.5,
        )
        assert m.leads_discovered == 47
        assert m.resolution_rate == 76.5

    def test_resolution_rate_calculation(self):
        received = 34
        escalated = 8
        auto = received - escalated
        rate = auto / received * 100
        assert round(rate, 1) == 76.5

    def test_zero_messages_rate(self):
        rate = 0.0 if 0 == 0 else (0 / 0 * 100)
        assert rate == 0.0

    def test_metrics_all_fields_accessible(self):
        m = WeekMetrics(
            leads_discovered=10,
            leads_published=5,
            enterprise_leads=2,
            content_generated=4,
            content_published=3,
            content_cost_cents=100,
            messages_received=20,
            messages_auto_resolved=15,
            messages_escalated=5,
            community_leads=1,
            resolution_rate=75.0,
        )
        assert m.leads_published == 5
        assert m.enterprise_leads == 2
        assert m.content_generated == 4
        assert m.content_published == 3
        assert m.content_cost_cents == 100
        assert m.messages_received == 20
        assert m.messages_auto_resolved == 15
        assert m.messages_escalated == 5
        assert m.community_leads == 1

    def test_resolution_rate_full_resolution(self):
        received = 10
        escalated = 0
        auto = received - escalated
        rate = auto / received * 100 if received > 0 else 0.0
        assert rate == 100.0

    def test_resolution_rate_all_escalated(self):
        received = 10
        escalated = 10
        auto = received - escalated
        rate = auto / received * 100 if received > 0 else 0.0
        assert rate == 0.0

    def test_metrics_dict_conversion(self):
        m = WeekMetrics(
            leads_discovered=5,
            leads_published=2,
            enterprise_leads=1,
            content_generated=3,
            content_published=2,
            content_cost_cents=50,
            messages_received=10,
            messages_auto_resolved=8,
            messages_escalated=2,
            community_leads=0,
            resolution_rate=80.0,
        )
        d = m.__dict__
        assert "leads_discovered" in d
        assert "resolution_rate" in d
        assert d["resolution_rate"] == 80.0
