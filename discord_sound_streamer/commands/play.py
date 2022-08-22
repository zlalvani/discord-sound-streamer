import tanjun
from lavaplayer import PlayList, TrackStartEvent

from discord_sound_streamer.bot import bot, lavalink
from discord_sound_streamer.datastore.operations import commands as commands_operations
from discord_sound_streamer.services import embed as embed_service
from discord_sound_streamer.services import lava as lava_service
from discord_sound_streamer.services import play as play_service

component = tanjun.Component()


@component.with_slash_command
@tanjun.with_str_slash_option("name", "search term")
@tanjun.as_slash_command("play", "play audio")
async def play(ctx: tanjun.abc.Context, name: str) -> None:
    if ctx.guild_id:
        results = await lava_service.search(name)

        if isinstance(results, PlayList):
            await play_service.play_playlist(ctx, results)
            return

        track = await lava_service.get_first_valid_track(results)
        if track:
            await play_service.play_track(ctx, track)
        else:
            await embed_service.reply_message(ctx, f"No results found for {name}...")


@component.with_slash_command
@tanjun.with_int_slash_option("selection", "the number of your selection", default=1, min_value=1)
@tanjun.as_slash_command("skip", "skip the current song")
async def skip(ctx: tanjun.abc.Context, selection: int) -> None:
    if ctx.guild_id:
        guild_node = await lavalink.get_guild_node(ctx.guild_id)
        if guild_node and guild_node.queue:
            if selection == 1:
                await embed_service.reply_message(ctx, f"Skipping {guild_node.queue[0].title}...")
                await lavalink.skip(ctx.guild_id)
            else:
                try:
                    await embed_service.reply_message(
                        ctx, f"Skipping {guild_node.queue[selection - 1].title}..."
                    )
                    guild_node.queue.pop(selection - 1)
                    await lavalink.set_guild_node(ctx.guild_id, guild_node)
                except IndexError:
                    await embed_service.reply_message(ctx, f"Selection {selection} not in queue")
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
        queue = await play_service.get_queue(ctx.guild_id)
        await ctx.respond(embed=embed_service.build_queue_embed(queue))


@component.with_slash_command
@tanjun.as_slash_command("clear", "clear the current queue")
async def clear(ctx: tanjun.abc.Context) -> None:
    if ctx.guild_id:
        if await play_service.get_queue(ctx.guild_id):
            await embed_service.reply_message(ctx, f"Clearing queue...")
            await lavalink.stop(ctx.guild_id)
        else:
            await embed_service.reply_message(ctx, "Queue empty")


@component.with_slash_command
@tanjun.as_slash_command("shuffle", "shuffle the current queue")
async def shuffle(ctx: tanjun.abc.Context) -> None:
    if ctx.guild_id:
        if await play_service.get_queue(ctx.guild_id):
            await embed_service.reply_message(ctx, f"Shuffling queue...")
            node = await lavalink.shuffle(ctx.guild_id)
            if node.queue:
                await ctx.respond(embed=embed_service.build_queue_embed(node.queue))
        else:
            await embed_service.reply_message(ctx, "Queue empty")


@component.with_slash_command
@tanjun.with_str_slash_option("time", "time to seek to (hh:mm:ss)")
@tanjun.as_slash_command("seek", "seek to a specific time in the current song")
async def seek(ctx: tanjun.abc.Context, time: str) -> None:
    if ctx.guild_id:
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

        if await play_service.get_queue(ctx.guild_id):
            seek_position = (hours * 3600 + minutes * 60 + seconds) * 1000
            await embed_service.reply_message(ctx, f"Seeking to {time}...")
            await lavalink.seek(ctx.guild_id, seek_position)
        else:
            await embed_service.reply_message(ctx, "Queue empty")


@component.with_slash_command
@tanjun.as_slash_command("current", "show the current song")
async def now_playing(ctx: tanjun.abc.Context) -> None:
    if ctx.guild_id:
        if queue := await play_service.get_queue(ctx.guild_id):
            await ctx.respond(
                embed=embed_service.build_track_embed(queue[0], show_time_remaining=True)
            )
        else:
            await embed_service.reply_message(ctx, "Queue empty")


@lavalink.listen(TrackStartEvent)
async def handle_track_start_event(event: TrackStartEvent) -> None:
    async with commands_operations.get_last_command(event.guild_id) as command:
        if command:
            await bot.rest.create_message(
                command.channel_id, embed=embed_service.build_track_embed(event.track)
            )


loader = component.make_loader()
