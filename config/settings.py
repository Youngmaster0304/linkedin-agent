from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import os


class Settings(BaseSettings):
    # LinkedIn Credentials
    linkedin_email: str = Field(..., env="LINKEDIN_EMAIL")
    linkedin_password: str = Field(..., env="LINKEDIN_PASSWORD")
    linkedin_2fa_secret: Optional[str] = Field(None, env="LINKEDIN_2FA_SECRET")

    # LLM API Keys (priority: HF/FLUX > Groq > OpenRouter > Cerebras)
    hf_token: Optional[str] = Field(None, env="HF_TOKEN")
    groq_api_key: Optional[str] = Field(None, env="GROQ_API_KEY")
    openrouter_api_key: Optional[str] = Field(None, env="OPENROUTER_API_KEY")
    cerebras_api_key: Optional[str] = Field(None, env="CEREBRAS_API_KEY")

    # Database
    database_url: str = Field(
        default="sqlite+aiosqlite:///./data/linkedin_agent.db",
        env="DATABASE_URL"
    )

    # Scheduling
    post_time_utc: str = Field(default="10:00", env="POST_TIME_UTC")
    timezone: str = Field(default="Asia/Kolkata", env="TIMEZONE")
    posts_per_week: int = Field(default=3, env="POSTS_PER_WEEK")

    # Content Generation
    max_post_length: int = Field(default=280, env="MAX_POST_LENGTH")
    min_post_length: int = Field(default=150, env="MIN_POST_LENGTH")
    research_depth: str = Field(default="deep", env="RESEARCH_DEPTH")

    # Playwright
    headless: bool = Field(default=True, env="HEADLESS")
    browser_timeout: int = Field(default=60000, env="BROWSER_TIMEOUT")

    # Analytics
    track_engagement: bool = Field(default=True, env="TRACK_ENGAGEMENT")
    engagement_check_hours: int = Field(default=24, env="ENGAGEMENT_CHECK_HOURS")

    # Storage
    data_dir: str = Field(default="./data", env="DATA_DIR")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()


def ensure_data_dir():
    os.makedirs(settings.data_dir, exist_ok=True)
