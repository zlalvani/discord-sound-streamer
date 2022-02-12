from datetime import datetime

import tanjun
from discord_sound_streamer.datastore.operations import commands as commands_operations
from discord_sound_streamer.logger import logger


async def update_last_command_time(ctx: tanjun.abc.Context) -> None:
    if ctx.guild_id:
        commands_operations.set_last_command_time(ctx.guild_id, datetime.utcnow())
        logger.info(f'Updated last command time for guild {ctx.guild_id}')
