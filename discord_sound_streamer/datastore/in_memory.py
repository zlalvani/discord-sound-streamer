import asyncio
from typing import Dict, List
from dataclasses import dataclass

from hikari import Snowflake
from lavaplayer import Track


# frozen and eq make the class hashable
@dataclass(frozen=True, eq=True)
class SearchWaitItem:
    guild_id: Snowflake
    user_id: Snowflake


# Used for mapping open search result requests to results, can leak if not managed carefully
SEARCH_WAIT_STORE_LOCK: asyncio.Lock = asyncio.Lock()
SEARCH_WAIT_STORE: Dict[SearchWaitItem, List[Track]] = {}
