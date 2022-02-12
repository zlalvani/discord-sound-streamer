import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncIterator, Dict, Optional

from discord_sound_streamer.logger import logger
from hikari import Snowflake

_LAST_COMMAND_TIMES_LOCK: asyncio.Lock = asyncio.Lock()
_LAST_COMMAND_TIMES: Dict[Snowflake, datetime] = {}


@asynccontextmanager
async def get_last_command_time(key: Snowflake) -> AsyncIterator[Optional[datetime]]:
    try:
        await _LAST_COMMAND_TIMES_LOCK.acquire()
        yield _LAST_COMMAND_TIMES.get(key)
    finally:
        _LAST_COMMAND_TIMES_LOCK.release()


def set_last_command_time(key: Snowflake, value: datetime) -> None:
    _LAST_COMMAND_TIMES[key] = value


def remove_last_command_time(key: Snowflake) -> None:
    _LAST_COMMAND_TIMES.pop(key, None)

def get_last_command_times() -> Dict[Snowflake, datetime]:
    return _LAST_COMMAND_TIMES.copy()