from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from hikari import Snowflake, CommandInteraction

from lavalink import AudioTrack


@dataclass
class SearchWaitValue:
    search_message_id: Snowflake
    query: str
    tracks: Sequence[AudioTrack]
    searched_at: datetime
    interaction: CommandInteraction


# frozen and eq make the class hashable
@dataclass(frozen=True, eq=True)
class SearchWaitKey:
    guild_id: Snowflake
    user_id: Snowflake
