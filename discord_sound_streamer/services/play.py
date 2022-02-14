from typing import List

import tanjun
from discord_sound_streamer.bot import bot, lavalink
from discord_sound_streamer.config import CONFIG
from hikari import Snowflake
from lavaplayer import Track


async def get_queue(guild_id: Snowflake) -> List[Track]:
    if await lavalink.get_guild_node(guild_id):
        return await lavalink.queue(guild_id)    
    return []


async def play(ctx: tanjun.abc.Context, track: Track) -> None:
    guild = await ctx.fetch_guild()
    if guild:
        queue = await get_queue(guild.id)
        user_voice_state = guild.get_voice_state(ctx.author.id)
        bot_voice_state = guild.get_voice_state(CONFIG.BOT_ID)
        if user_voice_state:
            if queue and bot_voice_state and bot_voice_state.channel_id != user_voice_state.channel_id: 
                await ctx.respond('Already playing a track in another channel.')
                return
            await bot.update_voice_state(guild.id, user_voice_state.channel_id, self_deaf=True)
            await ctx.respond(f'Playing {track.title}...')
            await lavalink.play(guild.id, track, ctx.author.id)
