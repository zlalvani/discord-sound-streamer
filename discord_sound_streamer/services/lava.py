from typing import List, Optional
from urllib.parse import urlparse

from lavaplay import PlayList, Track

from discord_sound_streamer.bot import lavalink_node
from discord_sound_streamer.services import youtube as youtube_service


async def get_and_filter_tracks(query: str, *, count: int = 1) -> List[Track]:
    """Search and filter age restricted tracks. This is currently not used because it is too slow."""

    result = await get_tracks(query)

    if result:
        return await youtube_service.filter_age_restricted(result[:count])

    return []


async def search(query: str) -> List[Track] | PlayList:
    # Transform youtube shorts URLs into normal youtube video URLs because lavaplayer doesn't like them
    # TODO Replace this with something more robust once dependencies are updated
    parsed = urlparse(query)
    if parsed.scheme and "youtube.com" in parsed.netloc and "/shorts/" in parsed.path:
        query = f"https://www.youtube.com/watch?v={parsed.path.split('/')[-1]}"

    result = await lavalink_node.auto_search_tracks(query)

    if result is None:
        return []

    return result


async def get_tracks(query: str) -> List[Track]:
    result = await search(query)
    if isinstance(result, PlayList):
        result = result.tracks

    return result


# TODO move to youtube_service
async def get_first_valid_track(tracks: List[Track]) -> Optional[Track]:

    for track in tracks:
        if not await youtube_service.is_age_restricted(track):
            return track

    return None
