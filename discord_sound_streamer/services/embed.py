from datetime import timedelta
from typing import List
from urllib.parse import urlparse

import tanjun
from hikari import Embed

from lavalink import AudioTrack, PlaylistInfo

_DOMAIN_TITLES = {
    "youtube": "YouTube",
    "soundcloud": "SoundCloud",
    "bandcamp": "Bandcamp",
}


def _build_track_link(track: AudioTrack) -> str:
    domain = urlparse(track.uri).netloc.split(".")[-2]

    if domain in _DOMAIN_TITLES:
        return f"[{_DOMAIN_TITLES[domain]}]({track.uri})"
    else:
        return f"[Link]({track.uri})"


def _apply_track_list_to_embed(embed: Embed, tracks: List[AudioTrack]) -> None:
    for ordinal, track in enumerate(tracks, start=1):
        # Discord embeds have max width of 3 inline fields, so they will automatically wrap after this
        embed.add_field(
            name=f"{ordinal}. {track.title}",
            value=_build_track_link(track),
            inline=True,
        )
        embed.add_field(name="Uploader", value=track.author, inline=True)
        embed.add_field(
            name="Length",
            value=str(timedelta(milliseconds=track.duration)),
            inline=True,
        )


def build_message_embed(message: str) -> Embed:
    embed = Embed(title=message, color=0x000000)
    return embed


def build_track_embed(
    track: AudioTrack, title: str = "Now Playing", show_time_remaining: bool = False
) -> Embed:
    embed = Embed(title=title, color=0x000000)
    embed.add_field(name="Title", value=track.title, inline=True)
    embed.add_field(name="Uploader", value=track.author, inline=True)
    embed.add_field(
        name="Remaining" if show_time_remaining else "Length",
        value=str(
            timedelta(
                milliseconds=track.duration
                - (1000 * track.position if show_time_remaining else 0)
            )
        ).split(".")[0],
        inline=True,
    )
    embed.add_field(name="Link", value=_build_track_link(track), inline=True)
    return embed


def build_queue_embed(tracks: List[AudioTrack]) -> Embed:
    embed = Embed(title="Queue", color=0x000000)
    if tracks:
        _apply_track_list_to_embed(embed, tracks[:8])
        if len(tracks) > 8:
            embed.add_field(
                name="...", value=f"{len(tracks) - 8} more items", inline=False
            )
        embed.set_footer(
            text=f'Total queue time remaining: {str(timedelta(milliseconds=sum(t.duration - (t.position * 1000) for t in tracks))).split(".")[0]}'
        )
    else:
        embed.description = "Queue empty"
    return embed


def build_playlist_embed(
    playlist_info: PlaylistInfo, tracks: List[AudioTrack]
) -> Embed:
    embed = Embed(title=f"Queuing playlist {playlist_info.name}...", color=0x000000)
    if tracks:
        _apply_track_list_to_embed(embed, tracks[:8])
        if len(tracks) > 8:
            embed.add_field(
                name="...", value=f"{len(tracks) - 8} more items", inline=False
            )
        embed.set_footer(
            text=f'Total playlist time: {str(timedelta(milliseconds=sum(t.duration - (t.position * 1000) for t in tracks))).split(".")[0]}'
        )
    else:
        embed.description = "No tracks in playlist"
    return embed


def build_search_embed(query: str, search_results: List[AudioTrack]) -> Embed:
    embed = Embed(
        title="Search Results", description=f'Results for "{query}"', color=0x000000
    )
    _apply_track_list_to_embed(embed, search_results)
    embed.set_footer(
        text="Use /select <number> to select a track in the next 30 seconds"
    )
    return embed


async def reply_message(ctx: tanjun.abc.Context, message: str) -> None:
    await ctx.respond(embed=build_message_embed(message))
