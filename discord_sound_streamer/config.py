from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENVIRONMENT: str
    BOT_TOKEN: str
    BOT_ID: int
    GUILD_ID: Optional[int]
    YOUTUBE_API_KEY: str
    HEALTH_CHECK_PORT: int = 1234
    INVIDIOUS_URL: str = "https://vid.puffyan.us"  # https://iv.ggtyler.dev
    LAVALINK_HOST: str = "localhost"
    LAVALINK_PORT: int = 40443
    LAVALINK_PASSWORD: str = "youshallnotpass"
    IMAGE_PATH: str = "./assets/image/"
    WAIT_FOR_LAVALINK: bool = False
    INACTIVE_TIMEOUT: int = 300
    YOUTUBE_FILTER_AGE_RESTRICTED: bool = False
    YOUTUBE_USE_INVIDIOUS_AGE_RESTRICTED_CHECK: bool = True

    model_config = SettingsConfigDict(
        env_file=".env.local", case_sensitive=True, extra="ignore"
    )


CONFIG = Settings()  # type: ignore
