import os
from typing import Optional

from dotenv import dotenv_values
from pydantic import BaseModel, validator


class Config(BaseModel):
    BOT_TOKEN: str
    BOT_ID: int
    GUILD_ID: Optional[int]
    YOUTUBE_API_KEY: str
    INVIDIOUS_URL: str = "https://vid.puffyan.us"
    LAVALINK_HOST: str = "localhost"
    LAVALINK_PORT: int = 443
    LAVALINK_PASSWORD: str = "youshallnotpass"
    IMAGE_PATH: str = "./assets/image/"
    WAIT_FOR_LAVALINK: bool = False
    INACTIVE_TIMEOUT: int = 300
    USE_INVIDIOUS_AGE_RESTRICTED: bool = True


CONFIG = Config.parse_obj({**dotenv_values(".env"), **os.environ})
