from typing import List

from lavaplayer import PlayList, Track

from discord_sound_streamer.bot import lavalink
from discord_sound_streamer.services import youtube as youtube_service


# TODO refactor this to keep looking for a valid result instead of filtering down from a count
# e.g. it will filter out the only track if you have count = 1 and it is age-restricted
async def search_and_filter_tracks(query: str, *, count: int = 1) -> List[Track]:
    result = await lavalink.auto_search_tracks(query)
    if isinstance(result, PlayList):
        result = result.tracks

    if result:
        if result[0].sourceName == "youtube":
            return await youtube_service.filter_age_restricted(result[:count])
        else:
            return result[:count]

    return []
