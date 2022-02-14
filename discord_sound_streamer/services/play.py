from typing import List

import tanjun
from discord_sound_streamer.bot import bot, lavalink
from hikari import Snowflake
from lavaplayer import Track
from discord_sound_streamer.logger import logger


async def get_queue(guild_id: Snowflake) -> List[Track]:
    if await lavalink.get_guild_node(guild_id):
        return await lavalink.queue(guild_id)    
    return []


async def play(ctx: tanjun.abc.Context, track: Track) -> None:
    guild = await ctx.fetch_guild()
    if guild:
        queue = await get_queue(guild.id)
        if queue: 
            await ctx.respond('Already a track playing in another channel.')
            return
        voice_state = guild.get_voice_state(ctx.author.id)
        if voice_state:
            await bot.update_voice_state(guild.id, voice_state.channel_id, self_deaf=True)
            await ctx.respond(f'Playing {track.title}...')
            await lavalink.play(guild.id, track, ctx.author.id)
