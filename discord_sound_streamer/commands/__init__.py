import tanjun
from discord_sound_streamer.bot import client
from discord_sound_streamer.services import commands as commands_service

component = tanjun.Component()

hooks: tanjun.Hooks = tanjun.Hooks().add_on_success(commands_service.update_last_command_time)

client.set_slash_hooks(hooks)

loader = component.make_loader()