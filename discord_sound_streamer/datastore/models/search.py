from dataclasses import dataclass
from datetime import datetime
from typing import List

from hikari import Snowflake

# from lavaplay import Track
from lavalink import AudioTrack


@dataclass
class SearchWaitValue:
    tracks: List[AudioTrack]
    searched_at: datetime


# frozen and eq make the class hashable
@dataclass(frozen=True, eq=True)
class SearchWaitKey:
    guild_id: Snowflake
    user_id: Snowflake
