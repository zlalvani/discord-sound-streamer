from dataclasses import dataclass
from datetime import datetime
from typing import List

from hikari import Snowflake, CommandInteraction

from lavalink import AudioTrack


@dataclass
class SearchWaitValue:
    search_message_id: Snowflake
    tracks: List[AudioTrack]
    searched_at: datetime
    interaction: CommandInteraction


# frozen and eq make the class hashable
@dataclass(frozen=True, eq=True)
class SearchWaitKey:
    guild_id: Snowflake
    user_id: Snowflake
