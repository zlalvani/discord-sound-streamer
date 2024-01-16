import asyncio
import os
import random
import time
from asyncio import StreamReader, StreamWriter

import hikari
import tanjun
from lavaplay.client import Lavalink

from discord_sound_streamer.config import CONFIG
from discord_sound_streamer.logger import logger

bot = hikari.GatewayBot(token=CONFIG.BOT_TOKEN)

client = tanjun.Client.from_gateway_bot(
    bot, mention_prefix=True, declare_global_commands=CONFIG.GUILD_ID if CONFIG.GUILD_ID else False
)

lavalink = Lavalink()

lavalink_node = lavalink.create_node(
    host=CONFIG.LAVALINK_HOST,  # Lavalink host
    port=CONFIG.LAVALINK_PORT,  # Lavalink port
    password=CONFIG.LAVALINK_PASSWORD,  # Lavalink password
    user_id=CONFIG.BOT_ID,  # Lavalink bot id
    ssl=False,
)

# On voice state update the bot will update the lavalink node
@bot.listen()
async def voice_state_update(event: hikari.VoiceStateUpdateEvent) -> None:
    player = lavalink_node.get_player(event.guild_id)

    if player:
        await player.raw_voice_state_update(
            event.state.user_id, event.state.session_id, event.state.channel_id
        )


@bot.listen()
async def voice_server_update(event: hikari.VoiceServerUpdateEvent) -> None:
    player = lavalink_node.get_player(event.guild_id)

    if player:
        await player.raw_voice_server_update(event.endpoint, event.token)


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


@bot.listen()
async def on_ready(event: hikari.ShardReadyEvent) -> None:
    lavalink_node.connect()


async def health_check_handler(_: StreamReader, writer: StreamWriter) -> None:
    writer.write("healthy".encode("utf8"))
    await writer.drain()
    writer.close()


async def start_health_check_server() -> None:
    # Start TCP server
    server = await asyncio.start_server(health_check_handler, "0.0.0.0", CONFIG.HEALTH_CHECK_PORT)
    async with server:
        await server.serve_forever()


def start():
    if CONFIG.WAIT_FOR_LAVALINK:
        time.sleep(15)

    # Do this here to avoid circular import problems
    from discord_sound_streamer.services.voice import leave_inactive_voice_channels

    async def loop() -> None:
        while True:
            await leave_inactive_voice_channels()
            await asyncio.sleep(30)

    asyncio.get_event_loop_policy().get_event_loop().create_task(loop())
    asyncio.get_event_loop_policy().get_event_loop().create_task(start_health_check_server())

    bot.run()


if __name__ == "__main__":
    start()
