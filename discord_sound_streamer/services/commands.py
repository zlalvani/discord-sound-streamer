from datetime import UTC, datetime

import tanjun

from discord_sound_streamer.datastore.models.commands import LastCommandValue
from discord_sound_streamer.datastore.operations import commands as commands_operations
from discord_sound_streamer.logger import logger
from discord_sound_streamer.services import embed as embed_service


async def update_last_command_time(ctx: tanjun.abc.Context) -> None:
    if ctx.guild_id:
        commands_operations.set_last_command(
            ctx.guild_id,
            LastCommandValue(executed_at=datetime.now(UTC), channel_id=ctx.channel_id),
        )
        logger.info(f"Updated last command time for guild {ctx.guild_id}")


async def command_error_handler(ctx: tanjun.abc.Context, _: Exception) -> None:
    await embed_service.reply_message(ctx, "An error occurred. Please try again later.")
    return None
