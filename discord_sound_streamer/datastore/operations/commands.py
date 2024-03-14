import asyncio
from contextlib import asynccontextmanager
from typing import AsyncIterator, Dict, Optional

from hikari import Snowflake

from discord_sound_streamer.datastore.models.commands import LastCommandValue

_LAST_COMMANDS_LOCK: asyncio.Lock = asyncio.Lock()
_LAST_COMMANDS: Dict[Snowflake, LastCommandValue] = {}


@asynccontextmanager
async def get_last_command(key: Snowflake) -> AsyncIterator[Optional[LastCommandValue]]:
    try:
        await _LAST_COMMANDS_LOCK.acquire()
        yield _LAST_COMMANDS.get(key)
    finally:
        _LAST_COMMANDS_LOCK.release()


def set_last_command(key: Snowflake, value: LastCommandValue) -> None:
    _LAST_COMMANDS[key] = value


def remove_last_command(key: Snowflake) -> None:
    _LAST_COMMANDS.pop(key, None)


def get_last_commands() -> Dict[Snowflake, LastCommandValue]:
    return _LAST_COMMANDS.copy()
