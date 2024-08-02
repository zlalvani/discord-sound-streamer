import tanjun
from hikari import Guild, Snowflake

from discord_sound_streamer.bot import bot, lavalink_client
from discord_sound_streamer.config import CONFIG
from discord_sound_streamer.services import embed as embed_service
from discord_sound_streamer.services import youtube as youtube_service
from lavalink import AudioTrack, DefaultPlayer, PlaylistInfo


def get_player(guild_id: Snowflake) -> DefaultPlayer:
    player = lavalink_client.player_manager.get(guild_id)

    if not player:
        player = lavalink_client.player_manager.create(guild_id)

    return player


async def get_queue(guild_id: Snowflake) -> list[AudioTrack]:
    player = get_player(guild_id)

    return player.queue


async def play_track(ctx: tanjun.abc.Context, track: AudioTrack) -> None:
    guild = await ctx.fetch_guild()
    if guild:
        await _play_tracks(ctx, guild, [track])


async def play_playlist(
    ctx: tanjun.abc.Context, playlist_info: PlaylistInfo, tracks: list[AudioTrack]
) -> None:
    guild = await ctx.fetch_guild()
    if guild:
        await _play_tracks(
            ctx, guild, await youtube_service.filter_age_restricted(tracks), playlist_info
        )


async def _play_tracks(
    ctx: tanjun.abc.Context,
    guild: Guild,
    tracks: list[AudioTrack],
    playlist_info: PlaylistInfo | None = None,
) -> None:
    queue = await get_queue(guild.id)
    player = get_player(guild.id)

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
    elif playlist_info:
        await ctx.respond(embed=embed_service.build_playlist_embed(playlist_info, tracks))
    else:
        raise ValueError("No playlist info provided")

    for track in tracks:
        # There can be a race condition where the bot hasn't yet joined the voice channel
        # before attempting to play. In that case, we retry.
        # try:
        #     async for attempt in AsyncRetrying(
        #         retry=retry_if_exception_type(NodeError),
        #         stop=stop_after_attempt(3),
        #         wait=wait_fixed(0.25),
        #     ):
        #         with attempt:
        player.add(track)
        # except RetryError as re:
        #     logger.exception(re)

    if not player.is_playing:
        await player.play()  # type: ignore


async def pause_control(ctx: tanjun.abc.Context, pause: bool) -> None:
    if ctx.guild_id:
        player = get_player(ctx.guild_id)

        if queue := await get_queue(ctx.guild_id):
            await embed_service.reply_message(
                ctx, f'{"Pausing" if pause else "Resuming"} {queue[0].title}...'
            )
            await player.set_pause(pause)
            # await player.pause(pause)
        else:
            await embed_service.reply_message(ctx, "Queue empty")
