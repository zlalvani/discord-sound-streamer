import asyncio
from typing import List

from pyyoutube import Api, Video, VideoListResponse

from discord_sound_streamer.clients.invidious import client as invidious_client
from discord_sound_streamer.config import CONFIG

# from lavaplay import Track
from lavalink import AudioTrack


async def is_age_restricted(track: AudioTrack) -> bool:
    """
    Attempt to determine if a video is age restricted, which currently breaks Lavaplayer.

    When using the YouTube API, the ytRating field is inconsistently present so Invidious is used by default.
    Depending on the server, the Invidious API can be slow.
    """

    if track.source_name != "youtube":
        return False

    if CONFIG.USE_INVIDIOUS_AGE_RESTRICTED:
        return await _is_age_restricted_invidious(track)

    return await _is_age_restricted_youtube(track)


async def _is_age_restricted_invidious(track: AudioTrack) -> bool:
    return not (await invidious_client.get_video(track.identifier)).isFamilyFriendly


async def _is_age_restricted_youtube(track: AudioTrack) -> bool:
    api = Api(api_key=CONFIG.YOUTUBE_API_KEY)

    def get_video():
        result = api.get_video_by_id(video_id=track.identifier)  # type: ignore
        assert isinstance(result, VideoListResponse)
        assert result.items
        return result.items[0]

    video = await asyncio.to_thread(get_video)

    return _video_age_restricted(video)


async def filter_age_restricted(tracks: List[AudioTrack]) -> List[AudioTrack]:

    # TODO bug: don't filter all non youtube here
    tracks = [t for t in tracks if t.source_name == "youtube"]

    if CONFIG.USE_INVIDIOUS_AGE_RESTRICTED:
        return await _filter_age_restricted_invidious(tracks)

    return await _filter_age_restricted_youtube(tracks)


async def _filter_age_restricted_invidious(tracks: List[AudioTrack]) -> List[AudioTrack]:
    # This is a fanout, so it may be throttled
    track_lookup = {track.identifier: track for track in tracks}
    videos = [await future for future in [invidious_client.get_video(t.identifier) for t in tracks]]
    return [track_lookup[v.videoId] for v in videos if v.isFamilyFriendly]


async def _filter_age_restricted_youtube(tracks: List[AudioTrack]) -> List[AudioTrack]:
    api = Api(api_key=CONFIG.YOUTUBE_API_KEY)

    track_lookup = {track.identifier: track for track in tracks}

    def get_videos():
        result = api.get_video_by_id(video_id=[track.identifier for track in tracks])  # type: ignore
        assert isinstance(result, VideoListResponse)
        return result.items

    videos = await asyncio.to_thread(get_videos)
    assert videos

    return [
        track_lookup[video.id] for video in videos if not _video_age_restricted(video) and video.id
    ]


def _video_age_restricted(video: Video) -> bool:
    if (
        (contentDetails := video.contentDetails)
        and (contentRating := contentDetails.contentRating)
        and contentRating.ytRating == "ytAgeRestricted"
    ):
        return True

    return False
