import tanjun
from hikari import Guild, Snowflake

from discord_sound_streamer.bot import bot, lavalink_client
from discord_sound_streamer.config import CONFIG
from discord_sound_streamer.services import embed as embed_service
from discord_sound_streamer.services import youtube as youtube_service
from discord_sound_streamer.polymorphs.responder import Responder
from lavalink import AudioTrack, DefaultPlayer, PlaylistInfo


def get_player(guild_id: Snowflake) -> DefaultPlayer:
    player = lavalink_client.player_manager.get(guild_id)

    if not player:
        player = lavalink_client.player_manager.create(guild_id)

    return player


async def get_queue(guild_id: Snowflake) -> list[AudioTrack]:
    player = get_player(guild_id)

    return player.queue


async def play_track(
    responder: Responder, guild: Guild | None, author_id: Snowflake, track: AudioTrack
) -> None:
    if guild:
        await _play_tracks(responder, guild, author_id, [track])


async def play_playlist(
    responder: Responder,
    guild: Guild | None,
    author_id: Snowflake,
    playlist_info: PlaylistInfo,
    tracks: list[AudioTrack],
) -> None:
    if guild:
        await _play_tracks(
            responder,
            guild,
            author_id,
            await youtube_service.filter_age_restricted(tracks),
            playlist_info,
        )


async def _play_tracks(
    responder: Responder,
    guild: Guild,
    author_id: Snowflake,
    tracks: list[AudioTrack],
    playlist_info: PlaylistInfo | None = None,
) -> None:
    queue = await get_queue(guild.id)
    player = get_player(guild.id)

    user_voice_state = guild.get_voice_state(author_id)
    bot_voice_state = guild.get_voice_state(CONFIG.BOT_ID)

    if not user_voice_state:
        await responder.respond_message(
            "You are not in a voice channel!", ephemeral=True
        )
        return

    if (
        queue
        and bot_voice_state
        and bot_voice_state.channel_id != user_voice_state.channel_id
    ):
        await responder.respond_message(
            "Already playing a track in another channel.", ephemeral=True
        )
        return

    await bot.update_voice_state(guild.id, user_voice_state.channel_id, self_deaf=True)

    if len(tracks) == 1:
        await responder.respond(
            embed=embed_service.build_track_embed(tracks[0], title="Queueing...")
        )
    elif playlist_info:
        await responder.respond(
            embed=embed_service.build_playlist_embed(playlist_info, tracks)
        )
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
        player.add(track, requester=author_id)
        # except RetryError as re:
        #     logger.exception(re)

    if not player.is_playing:
        await player.play()


async def pause_control(ctx: tanjun.abc.Context, pause: bool) -> None:
    if ctx.guild_id:
        player = get_player(ctx.guild_id)

        if queue := await get_queue(ctx.guild_id):
            await embed_service.reply_message(
                ctx, f'{"Pausing" if pause else "Resuming"} {queue[0].title}...'
            )
            await player.set_pause(pause)
        else:
            await embed_service.reply_message(ctx, "Queue empty")
