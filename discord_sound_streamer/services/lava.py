from typing import List

from lavaplayer import PlayList, Track

from discord_sound_streamer.bot import lavalink
from discord_sound_streamer.services import youtube as youtube_service


async def search_and_filter_tracks(query: str, *, count: int = 1) -> List[Track]:
    result = await lavalink.auto_search_tracks(query)
    if isinstance(result, PlayList):
        result = result.tracks

    if result:
        return await youtube_service.filter_age_restricted(result[:count])

    return []
