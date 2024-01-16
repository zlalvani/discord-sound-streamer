from typing import Optional

from pydantic import BaseSettings


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
    USE_INVIDIOUS_AGE_RESTRICTED: bool = True

    class Config:
        case_sensitive = True


CONFIG = Settings(_env_file=".env.local")
