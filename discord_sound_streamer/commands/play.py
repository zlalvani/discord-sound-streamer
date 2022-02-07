import tanjun
from discord_sound_streamer.bot import bot
from discord_sound_streamer.bot import lavalink

component = tanjun.Component()

@component.with_slash_command
@tanjun.with_str_slash_option("name", "search term")
@tanjun.as_slash_command("play", "play audio")
async def play(ctx: tanjun.abc.Context, name: str) -> None:
    guild = await ctx.fetch_guild()
    if guild:
        voice_state = guild.get_voice_state(ctx.author.id)
        if voice_state:
            await bot.update_voice_state(guild.id, voice_state.channel_id, self_deaf=True)
            result = await lavalink.auto_search_tracks(name)
            if result:
                await lavalink.play(guild.id, result[0], ctx.author.id)
                await ctx.respond(f'Playing {result[0].title}...')
            else:
                await ctx.respond(f'No results found for {name}...')


@component.with_slash_command
@tanjun.as_slash_command("skip", "skip the current song")
async def skip(ctx: tanjun.abc.Context) -> None:
    if ctx.guild_id:
        queue = await lavalink.queue(ctx.guild_id)
        await ctx.respond(f'Skipping {queue[0].title}...')
        await lavalink.skip(ctx.guild_id)


@component.with_slash_command
@tanjun.as_slash_command("pause", "pause the current song")
async def pause(ctx: tanjun.abc.Context) -> None:
    if ctx.guild_id:
        await ctx.respond(f'Pausing...')
        await lavalink.pause(ctx.guild_id)

loader = component.make_loader()