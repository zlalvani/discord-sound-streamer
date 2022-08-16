from typing import List, Optional

from lavaplayer import PlayList, Track

from discord_sound_streamer.bot import lavalink
from discord_sound_streamer.services import youtube as youtube_service


async def search_and_filter_tracks(query: str, *, count: int = 1) -> List[Track]:
    """Search and filter age restricted tracks. This is currently not used because it is too slow."""

    result = await search(query)

    if result:
        return await youtube_service.filter_age_restricted(result[:count])

    return []


async def search(query: str) -> List[Track]:
    result = await lavalink.auto_search_tracks(query)
    if isinstance(result, PlayList):
        result = result.tracks

    if result is None:
        return []

    return result


async def get_first_result(query: str) -> Optional[Track]:
    tracks = await search(query)

    for track in tracks:
        if not await youtube_service.is_age_restricted(track):
            return track

    return None
