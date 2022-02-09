import tanjun
from lavaplayer import Track

from discord_sound_streamer.bot import bot
from discord_sound_streamer.bot import lavalink

async def play(ctx: tanjun.abc.Context, track: Track) -> None:
    guild = await ctx.fetch_guild()
    if guild:
        voice_state = guild.get_voice_state(ctx.author.id)
        if voice_state:
            await bot.update_voice_state(guild.id, voice_state.channel_id, self_deaf=True)
            await ctx.respond(f'Playing {track.title}...')
            await lavalink.play(guild.id, track, ctx.author.id)
