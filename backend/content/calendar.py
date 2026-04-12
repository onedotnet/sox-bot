from datetime import datetime, timedelta, timezone

WEEKLY_SCHEDULE = [
    {"weekday": 0, "content_type": "seo_article", "language": "en", "platform": "blog"},
    {"weekday": 1, "content_type": "industry_brief", "language": "en", "platform": "twitter"},
    {"weekday": 2, "content_type": "seo_article", "language": "zh", "platform": "blog"},
    {"weekday": 3, "content_type": "social_post", "language": "en", "platform": "twitter"},
    {"weekday": 4, "content_type": "industry_brief", "language": "en", "platform": "linkedin"},
]


class ContentCalendar:
    def generate_weekly_plan(self, start_date: datetime, keywords: list[str]) -> list[dict]:
        plan = []
        kw_index = 0
        for slot in WEEKLY_SCHEDULE:
            target_date = start_date + timedelta(days=slot["weekday"])
            keyword = keywords[kw_index % len(keywords)] if keywords else "AI API gateway"
            kw_index += 1
            plan.append({
                "scheduled_at": target_date.replace(hour=9, minute=0, tzinfo=timezone.utc),
                "content_type": slot["content_type"],
                "language": slot["language"],
                "target_platform": slot["platform"],
                "seo_keyword": keyword,
            })
        return plan

    def get_next_monday(self, from_date: datetime | None = None) -> datetime:
        d = from_date or datetime.now(timezone.utc)
        days_ahead = 7 - d.weekday()
        if days_ahead == 7:
            days_ahead = 0
        return (d + timedelta(days=days_ahead)).replace(hour=0, minute=0, second=0, microsecond=0)
