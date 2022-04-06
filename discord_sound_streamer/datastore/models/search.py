from dataclasses import dataclass
from datetime import datetime
from typing import List

from hikari import Snowflake
from lavaplayer import Track


@dataclass
class SearchWaitValue:
    tracks: List[Track]
    searched_at: datetime


# frozen and eq make the class hashable
@dataclass(frozen=True, eq=True)
class SearchWaitKey:
    guild_id: Snowflake
    user_id: Snowflake
