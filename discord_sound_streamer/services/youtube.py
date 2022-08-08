import asyncio
from typing import List

from lavaplayer import Track
from pyyoutube import Api, Video, VideoListResponse

from discord_sound_streamer.clients.invidious import client as invidious_client
from discord_sound_streamer.config import CONFIG


async def filter_age_restricted(tracks: List[Track]) -> List[Track]:
    """
    Attempt to determine if a video is age restricted, which currently breaks Lavaplayer.

    When using the YouTube API, the ytRating field is inconsistently present so Invidious is used by default.
    Depending on the server, the Invidious API can be slow.
    """

    if CONFIG.USE_INVIDIOUS_AGE_RESTRICTED:
        return await _filter_age_restricted_invidious(tracks)

    return await _filter_age_restricted_youtube(tracks)


async def _filter_age_restricted_invidious(tracks: List[Track]) -> List[Track]:
    # This is a fanout, so it may be throttled
    track_lookup = {track.identifier: track for track in tracks}
    videos = [await f for f in [invidious_client.get_video(t.identifier) for t in tracks]]
    return [track_lookup[v.videoId] for v in videos if v.isFamilyFriendly]


async def _filter_age_restricted_youtube(tracks: List[Track]) -> List[Track]:
    api = Api(api_key=CONFIG.YOUTUBE_API_KEY)

    track_lookup = {track.identifier: track for track in tracks}

    def get_videos():
        result = api.get_video_by_id(video_id=[track.identifier for track in tracks])
        assert isinstance(result, VideoListResponse)
        return result.items

    videos = await asyncio.to_thread(get_videos)
    assert videos

    return [
        track_lookup[video.id]
        for video in videos
        if not _is_age_restricted_youtube(video) and video.id
    ]


def _is_age_restricted_youtube(video: Video) -> bool:
    if (
        (contentDetails := video.contentDetails)
        and (contentRating := contentDetails.contentRating)
        and contentRating.ytRating == "ytAgeRestricted"
    ):
        return True

    return False