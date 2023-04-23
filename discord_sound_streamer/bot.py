import asyncio
import os
import random
import time

import hikari
import tanjun
from lavaplayer import LavalinkClient

from discord_sound_streamer.config import CONFIG
from discord_sound_streamer.logger import logger

bot = hikari.GatewayBot(token=CONFIG.BOT_TOKEN)

client = tanjun.Client.from_gateway_bot(
    bot, mention_prefix=True, declare_global_commands=CONFIG.GUILD_ID if CONFIG.GUILD_ID else False
)

lavalink = LavalinkClient(
    host=CONFIG.LAVALINK_HOST,  # Lavalink host
    port=CONFIG.LAVALINK_PORT,  # Lavalink port
    password=CONFIG.LAVALINK_PASSWORD,  # Lavalink password
    user_id=CONFIG.BOT_ID,  # Lavalink bot id
    is_ssl=False,
)

# On voice state update the bot will update the lavalink node
@bot.listen()
async def voice_state_update(event: hikari.VoiceStateUpdateEvent) -> None:
    await lavalink.raw_voice_state_update(
        event.guild_id, event.state.user_id, event.state.session_id, event.state.channel_id
    )


@bot.listen()
async def voice_server_update(event: hikari.VoiceServerUpdateEvent) -> None:
    await lavalink.raw_voice_server_update(event.guild_id, event.endpoint, event.token)


@bot.listen()
async def handle_message_create(event: hikari.MessageCreateEvent) -> None:
    if not event.message.guild_id and event.message.author.id != CONFIG.BOT_ID:
        logger.info(f"{event.message.author.username}: {event.message.content}")
        filename = random.choice(os.listdir(CONFIG.IMAGE_PATH))
        with open(CONFIG.IMAGE_PATH + filename, "rb") as fd:
            await event.message.respond(attachment=fd.read())


client.load_modules("discord_sound_streamer.commands.__init__")
client.load_modules("discord_sound_streamer.commands.play")
client.load_modules("discord_sound_streamer.commands.search")


def start():
    if CONFIG.WAIT_FOR_LAVALINK:
        time.sleep(15)

    lavalink.connect()

    # Do this here to avoid circular import problems
    from discord_sound_streamer.services.voice import leave_inactive_voice_channels

    async def loop() -> None:
        while True:
            await leave_inactive_voice_channels()
            await asyncio.sleep(30)

    asyncio.get_event_loop_policy().get_event_loop().create_task(loop())

    bot.run()


if __name__ == "__main__":
    start()
