import os
from typing import Optional

from dotenv import dotenv_values
from pydantic import BaseModel


class Config(BaseModel):
    BOT_TOKEN: str
    BOT_ID: int
    GUILD_ID: Optional[int]
    LAVALINK_HOST: str = "localhost"
    LAVALINK_PORT: int = 443
    LAVALINK_PASSWORD: str = "youshallnotpass"
    IMAGE_PATH: str = "./assets/image/"
    WAIT_FOR_LAVALINK: bool = False
    INACTIVE_TIMEOUT: int = 300


CONFIG = Config.parse_obj({**dotenv_values(".env"), **os.environ})
