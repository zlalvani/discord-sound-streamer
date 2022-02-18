from datetime import timedelta
from typing import List

import tanjun

from hikari import Embed
from lavaplayer import Track

# Discord embeds have max width of 3 inline fields, so they will automatically wrap after this
def _apply_track_info(embed: Embed, track: Track, ordinal: int = None) -> None:
    embed.add_field(name=f'{ordinal}.' if ordinal is not None else 'Title', value=track.title, inline=True)
    embed.add_field(name='Author', value=track.author, inline=True)
    embed.add_field(name='Length', value=str(timedelta(milliseconds=track.length)), inline=True)


def _build_message_embed(message: str) -> Embed:
    embed = Embed(title=message, color=0x000000)
    return embed


def build_track_embed(track: Track, title: str = 'Now Playing') -> Embed:
    embed = Embed(title=title, color=0x000000)
    _apply_track_info(embed, track)
    return embed


def build_queue_embed(tracks: List[Track]) -> Embed:
    embed = Embed(title='Queue', color=0x000000)
    if tracks:
        for i, track in enumerate(tracks[:8], start=1):
            _apply_track_info(embed, track, ordinal=i)
        if len(tracks) > 8:
            embed.add_field(name='...', value=f'{len(tracks) - 8} more items', inline=False)
        embed.set_footer(text=f'Total queue time: {str(timedelta(milliseconds=sum(t.length for t in tracks)))}')
    else:
        embed.description = 'Queue empty'
    return embed


def build_search_embed(query: str, search_results: List[Track]) -> Embed:
    embed = Embed(title='Search Results', description=f'Results for "{query}"', color=0x000000)
    for i, track in enumerate(search_results, start=1):
        _apply_track_info(embed, track, ordinal=i)
    embed.set_footer(text=f'Use /select <number> to select a track')
    return embed


async def reply_message(ctx: tanjun.abc.Context, message) -> None:
    await ctx.respond(embed=_build_message_embed(message))