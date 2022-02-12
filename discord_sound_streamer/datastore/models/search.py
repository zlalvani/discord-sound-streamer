from dataclasses import dataclass
from typing import List

from hikari import Snowflake
from lavaplayer import Track

@dataclass
class SearchWaitValue:
    tracks: List[Track]

# frozen and eq make the class hashable
@dataclass(frozen=True, eq=True)
class SearchWaitKey:
    guild_id: Snowflake
    user_id: Snowflake
