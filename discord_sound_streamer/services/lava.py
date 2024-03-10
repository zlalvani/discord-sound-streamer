from typing import List, Optional
from urllib.parse import urlparse

from discord_sound_streamer.bot import lavalink_client
from discord_sound_streamer.services import youtube as youtube_service
from lavalink import AudioTrack, LoadResult


async def get_and_filter_tracks(query: str, *, count: int = 1) -> List[AudioTrack]:
    """Search and filter age restricted tracks. This is currently not used because it is too slow."""

    result = await get_tracks(query)

    if result:
        return await youtube_service.filter_age_restricted(result[:count])

    return []


async def search(query: str) -> LoadResult:
    # Transform youtube shorts URLs into normal youtube video URLs because lavaplayer doesn't like them
    # TODO Replace this with something more robust once dependencies are updated
    parsed = urlparse(query)
    if parsed.scheme and "youtube.com" in parsed.netloc and "/shorts/" in parsed.path:
        query = f"https://www.youtube.com/watch?v={parsed.path.split('/')[-1]}"
    if not parsed.scheme and not parsed.netloc:
        query = f"ytsearch:{query}"

    return await lavalink_client.get_tracks(query)


async def get_tracks(query: str) -> List[AudioTrack]:
    result = await search(query)

    return result.tracks


# TODO move to youtube_service
async def get_first_valid_track(tracks: List[AudioTrack]) -> Optional[AudioTrack]:

    for track in tracks:
        if not await youtube_service.is_age_restricted(track):
            return track

    return None
