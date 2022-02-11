import tanjun
from discord_sound_streamer.bot import lavalink
from discord_sound_streamer.services import play as play_service

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
            await ctx.respond(f'No results found for {name}...')


@component.with_slash_command
@tanjun.as_slash_command("skip", "skip the current song")
async def skip(ctx: tanjun.abc.Context) -> None:
    if ctx.guild_id:
        queue = await lavalink.queue(ctx.guild_id)
        if queue:
            await ctx.respond(f'Skipping {queue[0].title}...')
            if len(queue) > 1:
                await ctx.respond(f'Playing {queue[1].title}...')
            await lavalink.skip(ctx.guild_id)


@component.with_slash_command
@tanjun.as_slash_command("pause", "pause the current song")
async def pause(ctx: tanjun.abc.Context) -> None:
    if ctx.guild_id:
        await ctx.respond(f'Pausing...')
        await lavalink.pause(ctx.guild_id)


@component.with_slash_command
@tanjun.as_slash_command("queue", "show the current queue")
async def queue(ctx: tanjun.abc.Context) -> None:
    if ctx.guild_id:
        queue = await lavalink.queue(ctx.guild_id)
        if queue:
            await ctx.respond(f'Current queue: \n' + '\n'.join([t.title for t in queue]))
        else:
            await ctx.respond(f'Queue empty')


@component.with_slash_command
@tanjun.as_slash_command("clear", "clear the current queue")
async def clear(ctx: tanjun.abc.Context) -> None:
    if ctx.guild_id:
        await ctx.respond(f'Clearing queue...')
        await lavalink.stop(ctx.guild_id)


@component.with_slash_command
@tanjun.as_slash_command("shuffle", "shuffle the current queue")
async def shuffle(ctx: tanjun.abc.Context) -> None:
    if ctx.guild_id:
        await ctx.respond(f'Shuffling queue...')
        node = await lavalink.shuffle(ctx.guild_id)
        if node.queue:
            await ctx.respond(f'Current queue: \n' + '\n'.join([t.title for t in node.queue]))


loader = component.make_loader()
