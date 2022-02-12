import asyncio
from contextlib import asynccontextmanager
from typing import AsyncIterator, Dict, Optional
from discord_sound_streamer.logger import logger

from discord_sound_streamer.datastore.models.search import SearchWaitKey, SearchWaitValue, SearchWaitValue

# Used for mapping open search result requests to results, can leak if not managed carefully

# Using a global lock for now because guildmember-specific locks is too complex for current scale
_SEARCH_WAIT_STORE_LOCK: asyncio.Lock = asyncio.Lock()
_SEARCH_WAIT_STORE: Dict[SearchWaitKey, SearchWaitValue] = {}

class SearchValueNotFoundException(Exception):
    pass

@asynccontextmanager
async def get_search_wait_value(key: SearchWaitKey) -> AsyncIterator[Optional[SearchWaitValue]]:
    try:
        await _SEARCH_WAIT_STORE_LOCK.acquire()
        yield _SEARCH_WAIT_STORE.get(key)
    finally:
        _SEARCH_WAIT_STORE_LOCK.release()


def set_search_wait_value(key: SearchWaitKey, value: SearchWaitValue) -> None:
    _SEARCH_WAIT_STORE[key] = value


def remove_search_wait_value(key: SearchWaitKey) -> None:
    result = _SEARCH_WAIT_STORE.pop(key, None)
    if result is None:
        logger.warning(f'Tried to remove a search wait value that was not in the store. Key: {key}')

