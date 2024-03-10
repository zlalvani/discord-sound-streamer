from typing import Any

import tanjun

from discord_sound_streamer.bot import client
from discord_sound_streamer.services import commands as commands_service

component = tanjun.Component()

hooks: tanjun.Hooks[Any] = (
    tanjun.Hooks()
    .add_pre_execution(commands_service.update_last_command_time)  # type: ignore
    .add_on_error(commands_service.command_error_handler)  # type: ignore
)


client.set_slash_hooks(hooks)

loader = component.make_loader()
