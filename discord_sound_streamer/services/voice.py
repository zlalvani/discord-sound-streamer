from datetime import datetime

from discord_sound_streamer.bot import bot
from discord_sound_streamer.config import CONFIG
from discord_sound_streamer.datastore.operations import \
    commands as commands_operations
from discord_sound_streamer.logger import logger
from discord_sound_streamer.services import play as play_service


async def leave_inactive_voice_channels() -> None:
    for guild_id in commands_operations.get_last_command_times().keys():
        async with commands_operations.get_last_command_time(guild_id) as last_command_time:
            if last_command_time is None or (datetime.utcnow() - last_command_time).seconds > CONFIG.INACTIVE_TIMEOUT:
                queue = await play_service.get_queue(guild_id)
                if queue:
                    continue
                logger.info(f'Leaving inactive voice channel {guild_id}')
                await bot.update_voice_state(guild_id, None)
                commands_operations.remove_last_command_time(guild_id)
