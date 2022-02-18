from typing import Optional
import tanjun
from discord_sound_streamer.bot import bot, lavalink
from discord_sound_streamer.datastore.operations import \
    commands as commands_operations
from discord_sound_streamer.services import embed as embed_service
from discord_sound_streamer.services import play as play_service
from lavaplayer import TrackStartEvent

component = tanjun.Component()

@component.with_slash_command
@tanjun.with_str_slash_option("name", "search term")
@tanjun.as_slash_command("play", "play audio")
async def play(ctx: tanjun.abc.Context, name: str) -> None:
    if ctx.guild_id:
        result = await lavalink.auto_search_tracks(name)
        if result: 
            await play_service.play(ctx, result[0])
        else:
            await embed_service.reply_message(ctx, f'No results found for {name}...')


@component.with_slash_command
@tanjun.with_int_slash_option('selection', 'the number of your selection', default=1, min_value=1)
@tanjun.as_slash_command("skip", "skip the current song")
async def skip(ctx: tanjun.abc.Context, selection: int) -> None:
    if ctx.guild_id:
        guild_node = await lavalink.get_guild_node(ctx.guild_id)
        if guild_node and guild_node.queue:
            if selection == 1:
                await embed_service.reply_message(ctx, f'Skipping {guild_node.queue[0].title}...')
                await lavalink.skip(ctx.guild_id)
            else:
                try:
                    await embed_service.reply_message(ctx, f'Skipping {guild_node.queue[selection - 1].title}...')
                    guild_node.queue.pop(selection - 1)
                    await lavalink.set_guild_node(ctx.guild_id, guild_node)
                except IndexError:
                    await embed_service.reply_message(ctx, f'Selection {selection} not in queue')
        else:
            await embed_service.reply_message(ctx, 'Queue empty')


@component.with_slash_command
@tanjun.as_slash_command("pause", "pause the current song")
async def pause(ctx: tanjun.abc.Context) -> None:
    if ctx.guild_id:
        await embed_service.reply_message(ctx, 'Pausing...')
        await lavalink.pause(ctx.guild_id)


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
            await embed_service.reply_message(ctx, f'Clearing queue...')
            await lavalink.stop(ctx.guild_id)
        else:
            await embed_service.reply_message(ctx, 'Queue empty')


@component.with_slash_command
@tanjun.as_slash_command("shuffle", "shuffle the current queue")
async def shuffle(ctx: tanjun.abc.Context) -> None:
    if ctx.guild_id:
        if await play_service.get_queue(ctx.guild_id):
            await embed_service.reply_message(ctx, f'Shuffling queue...')
            node = await lavalink.shuffle(ctx.guild_id)
            if node.queue:
                await ctx.respond(embed=embed_service.build_queue_embed(node.queue))
        else:
            await embed_service.reply_message(ctx, 'Queue empty')


@lavalink.listen(TrackStartEvent)
async def handle_track_start_event(event: TrackStartEvent) -> None:
    async with commands_operations.get_last_command(event.guild_id) as command:
        if command:
            await bot.rest.create_message(command.channel_id, embed=embed_service.build_track_embed(event.track))


loader = component.make_loader()
