from typing import List

import tanjun
from hikari import Guild, Snowflake
from lavaplayer import PlayList, Track
from lavaplayer.exceptions import NodeError
from tenacity import (
    AsyncRetrying,
    RetryError,
    retry_if_exception_type,
    stop_after_attempt,
    wait_fixed,
)

from discord_sound_streamer.bot import bot, lavalink
from discord_sound_streamer.config import CONFIG
from discord_sound_streamer.logger import logger
from discord_sound_streamer.services import embed as embed_service
from discord_sound_streamer.services import youtube as youtube_service


async def get_queue(guild_id: Snowflake) -> List[Track]:
    if await lavalink.get_guild_node(guild_id):
        return await lavalink.queue(guild_id)
    return []


async def play_track(ctx: tanjun.abc.Context, track: Track) -> None:
    guild = await ctx.fetch_guild()
    if guild:
        await _play_tracks(ctx, guild, [track])


async def play_playlist(ctx: tanjun.abc.Context, playlist: PlayList) -> None:
    guild = await ctx.fetch_guild()
    if guild:
        await _play_tracks(ctx, guild, await youtube_service.filter_age_restricted(playlist.tracks))


async def _play_tracks(ctx: tanjun.abc.Context, guild: Guild, tracks: List[Track]) -> None:
    queue = await get_queue(guild.id)
    user_voice_state = guild.get_voice_state(ctx.author.id)
    bot_voice_state = guild.get_voice_state(CONFIG.BOT_ID)

    if not user_voice_state:
        await embed_service.reply_message(ctx, "You are not in a voice channel!")
        return

    if queue and bot_voice_state and bot_voice_state.channel_id != user_voice_state.channel_id:
        await embed_service.reply_message(ctx, "Already playing a track in another channel.")
        return

    await bot.update_voice_state(guild.id, user_voice_state.channel_id, self_deaf=True)

    if len(tracks) == 1:
        await ctx.respond(embed=embed_service.build_track_embed(tracks[0], title="Queueing..."))
    else:
        await ctx.respond(embed=embed_service.build_playlist_embed(tracks))

    for track in tracks:
        # There can be a race condition where the bot hasn't yet joined the voice channel
        # before attempting to play. In that case, we retry.
        try:
            async for attempt in AsyncRetrying(
                retry=retry_if_exception_type(NodeError),
                stop=stop_after_attempt(3),
                wait=wait_fixed(0.25),
            ):
                with attempt:
                    await lavalink.play(guild.id, track, ctx.author.id)
        except RetryError as re:
            logger.info("foo")
            logger.exception(re)
            pass


async def pause_control(ctx: tanjun.abc.Context, pause: bool) -> None:
    if ctx.guild_id:
        if await lavalink.get_guild_node(ctx.guild_id) and (queue := await get_queue(ctx.guild_id)):
            await embed_service.reply_message(
                ctx, f'{"Pausing" if pause else "Resuming"} {queue[0].title}...'
            )
            await lavalink.pause(ctx.guild_id, pause)
        else:
            await embed_service.reply_message(ctx, "Queue empty")
