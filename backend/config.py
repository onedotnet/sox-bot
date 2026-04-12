from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://soxbot:soxbot@localhost:5432/soxbot"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # SoxAI API
    soxai_api_key: str = ""
    soxai_base_url: str = "https://api.soxai.io/v1"

    # ScoutBot
    scout_interval_minutes: int = 30
    scout_relevance_threshold: int = 60
    scout_max_replies_per_platform_per_day: int = 5
    scout_cooldown_days: int = 30

    # Reddit
    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    reddit_username: str = ""
    reddit_password: str = ""

    # Twitter
    twitter_bearer_token: str = ""

    # Discord
    discord_token: str = ""

    model_config = {"env_prefix": "SOXBOT_"}


settings = Settings()
