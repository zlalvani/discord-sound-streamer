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


def _format_timedelta(ms: int) -> str:
    if ms > 2**31 - 1:
        return "∞"

    td = timedelta(milliseconds=ms)

    total_seconds = int(td.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    # Build the formatted string dynamically
    if hours > 0:
        return f"{hours}:{minutes:02}:{seconds:02}"
    else:
        return f"{minutes}:{seconds:02}"


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
            value=_format_timedelta(track.duration),
            inline=True,
        )


def build_message_embed(message: str) -> Embed:
    embed = Embed(title=message, color=0x000000)
    return embed


def build_track_embed(
    track: AudioTrack, title: str = "Now Playing", current_position: int | None = None
) -> Embed:
    embed = Embed(title=title, color=0x000000)
    embed.add_field(name="Title", value=track.title, inline=True)
    embed.add_field(name="Uploader", value=track.author, inline=True)
    embed.add_field(
        name="Elapsed" if current_position is not None else "Length",
        value=f"{_format_timedelta(
            current_position
            )} / {_format_timedelta(track.duration)}"
        if current_position is not None
        else _format_timedelta(track.duration),
        inline=True,
    )
    embed.add_field(name="Link", value=_build_track_link(track), inline=True)
    return embed


def build_queue_embed(current_position: int, tracks: List[AudioTrack]) -> Embed:
    embed = Embed(title="Queue", color=0x000000)
    if tracks:
        _apply_track_list_to_embed(embed, tracks[:8])
        if len(tracks) > 8:
            embed.add_field(
                name="...", value=f"{len(tracks) - 8} more items", inline=False
            )
        embed.set_footer(
            text=f"Total queue time remaining: {_format_timedelta(sum(t.duration for t in tracks) - current_position)}"
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
            text=f"Total playlist time: {_format_timedelta(sum(t.duration - (t.position * 1000) for t in tracks))}"
        )
    else:
        embed.description = "No tracks in playlist"
    return embed


def build_search_embed(
    query: str, search_results: List[AudioTrack], selected: int | None = None
) -> Embed:
    embed = Embed(
        title="Search Results", description=f'Results for "{query}"', color=0x000000
    )
    _apply_track_list_to_embed(embed, search_results)
    embed.set_footer(
        text="Use /select <number> to select a track in the next 30 seconds, or use the dropdown menu below"
        if selected is None
        else f"Selected: {selected + 1}. {search_results[selected].title}"
    )
    return embed


async def reply_message(ctx: tanjun.abc.Context, message: str) -> None:
    await ctx.respond(embed=build_message_embed(message))
