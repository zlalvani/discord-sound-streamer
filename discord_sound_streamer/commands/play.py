import tanjun

from discord_sound_streamer.polymorphs.responder import SlashCommandResponder
from discord_sound_streamer.services import embed as embed_service
from discord_sound_streamer.services import lava as lava_service
from discord_sound_streamer.services import play as play_service
from lavalink import LoadType

component = tanjun.Component()


@component.with_slash_command
@tanjun.with_str_slash_option("name", "search term or URL")
@tanjun.as_slash_command("play", "play audio")
async def play(ctx: tanjun.abc.Context, name: str) -> None:
    if ctx.guild_id:
        result = await lava_service.search(name)

        responder = SlashCommandResponder(ctx)
        guild = await ctx.fetch_guild()
        author_id = ctx.author.id

        if result.load_type == LoadType.PLAYLIST:
            await play_service.play_playlist(
                responder, guild, author_id, result.playlist_info, result.tracks
            )
            return

        track = await lava_service.get_first_valid_track(result.tracks)
        if track:
            await play_service.play_track(responder, guild, author_id, track)
        else:
            await embed_service.reply_message(ctx, f"No results found for {name}...")


@component.with_slash_command
@tanjun.with_int_slash_option(
    "selection", "the number of your selection", default=1, min_value=1
)
@tanjun.as_slash_command("skip", "skip the current song")
async def skip(ctx: tanjun.abc.Context, selection: int) -> None:
    if ctx.guild_id:
        player = play_service.get_player(ctx.guild_id)

        if selection == 1 and player.current:
            await embed_service.reply_message(
                ctx, f"Skipping {player.current.title}..."
            )
            await player.skip()
        elif player.queue:
            try:
                await embed_service.reply_message(
                    ctx, f"Skipping {player.queue[selection - 1].title}..."
                )
                player.queue.pop(selection - 2)
            except IndexError:
                await embed_service.reply_message(
                    ctx, f"Selection {selection} not in queue"
                )
        else:
            await embed_service.reply_message(ctx, "Queue empty")


@component.with_slash_command
@tanjun.as_slash_command("pause", "pause the current song")
async def pause(ctx: tanjun.abc.Context) -> None:
    await play_service.pause_control(ctx, True)


@component.with_slash_command
@tanjun.as_slash_command("unpause", "unpause the current song")
async def unpause(ctx: tanjun.abc.Context) -> None:
    await play_service.pause_control(ctx, False)


@component.with_slash_command
@tanjun.as_slash_command("queue", "show the current queue")
async def queue(ctx: tanjun.abc.Context) -> None:
    if ctx.guild_id:
        player = play_service.get_player(ctx.guild_id)
        await ctx.respond(
            embed=embed_service.build_queue_embed(
                [*([player.current] if player.current else []), *player.queue]
            )
        )


@component.with_slash_command
@tanjun.as_slash_command("clear", "clear the current queue")
async def clear(ctx: tanjun.abc.Context) -> None:
    if ctx.guild_id:
        player = play_service.get_player(ctx.guild_id)
        if player.is_playing or player.queue:
            await player.stop()
            player.queue.clear()
            await embed_service.reply_message(ctx, "Queue cleared")
        else:
            await embed_service.reply_message(ctx, "Queue empty")


@component.with_slash_command
@tanjun.as_slash_command("shuffle", "shuffle the current queue")
async def shuffle(ctx: tanjun.abc.Context) -> None:
    if ctx.guild_id:
        player = play_service.get_player(ctx.guild_id)
        if player.is_playing:
            player = play_service.get_player(ctx.guild_id)
            await embed_service.reply_message(
                ctx, f"{'Disabling' if player.shuffle else 'Enabling'} shuffle..."
            )
            player.set_shuffle(not player.shuffle)
        else:
            await embed_service.reply_message(ctx, "Queue empty")


@component.with_slash_command
@tanjun.with_str_slash_option("time", "time to seek to (hh:mm:ss)")
@tanjun.as_slash_command("seek", "seek to a specific time in the current song")
async def seek(ctx: tanjun.abc.Context, time: str) -> None:
    if ctx.guild_id:
        player = play_service.get_player(ctx.guild_id)

        # TODO This is ugly, rewrite this with a time parsing library
        try:
            time_parts = time.split(":")
            if len(time_parts) == 3:
                hours = int(time_parts[0])
                minutes = int(time_parts[1])
                seconds = int(time_parts[2])
            elif len(time_parts) == 2:
                hours = 0
                minutes = int(time_parts[0])
                seconds = int(time_parts[1])
            elif len(time_parts) == 1:
                hours = 0
                minutes = 0
                seconds = int(time_parts[0])
            else:
                raise ValueError

            if minutes > 59 or seconds > 59:
                raise ValueError

        except ValueError:
            await embed_service.reply_message(ctx, "Invalid time format")
            return

        if player.is_playing:
            seek_position = (hours * 3600 + minutes * 60 + seconds) * 1000
            await embed_service.reply_message(ctx, f"Seeking to {time}...")
            await player.seek(seek_position)
        else:
            await embed_service.reply_message(ctx, "Queue empty")


@component.with_slash_command
@tanjun.as_slash_command("current", "show the current song")
async def current(ctx: tanjun.abc.Context) -> None:
    if ctx.guild_id:
        player = play_service.get_player(ctx.guild_id)
        if player.current:
            await ctx.respond(
                embed=embed_service.build_track_embed(
                    player.current, show_time_remaining=True
                )
            )
        else:
            await embed_service.reply_message(ctx, "Queue empty")


loader = component.make_loader()
