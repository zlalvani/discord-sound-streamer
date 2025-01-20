import asyncio
import os
import random
import time
from asyncio import StreamReader, StreamWriter
from typing import cast

import hikari
import tanjun

from hikari.interactions.base_interactions import InteractionType

import lavalink
from discord_sound_streamer.config import CONFIG
from discord_sound_streamer.datastore.operations import commands as commands_operations
from discord_sound_streamer.logger import logger
from discord_sound_streamer.services import embed as embed_service


bot = hikari.GatewayBot(token=CONFIG.BOT_TOKEN)

client = tanjun.Client.from_gateway_bot(
    bot,
    mention_prefix=True,
    declare_global_commands=CONFIG.GUILD_ID if CONFIG.GUILD_ID else False,
)


class EventHandler:
    """Events from the Lavalink server"""

    @lavalink.listener(lavalink.TrackStartEvent)
    async def track_start(self, event: lavalink.TrackStartEvent):
        async with commands_operations.get_last_command(
            hikari.Snowflake(event.player.guild_id)
        ) as command:
            if command:
                await bot.rest.create_message(
                    command.channel_id,
                    embed=embed_service.build_track_embed(event.track),
                )
        logger.info("Track started on guild: %s", event.player.guild_id)

    @lavalink.listener(lavalink.TrackEndEvent)
    async def track_end(self, event: lavalink.TrackEndEvent):
        logger.info("Track finished on guild: %s", event.player.guild_id)

    @lavalink.listener(lavalink.TrackExceptionEvent)
    async def track_exception(self, event: lavalink.TrackExceptionEvent):
        logger.warning(
            "Track exception event happened on guild: %d", event.player.guild_id
        )

    @lavalink.listener(lavalink.QueueEndEvent)
    async def queue_finish(self, event: lavalink.QueueEndEvent):
        async with commands_operations.get_last_command(
            hikari.Snowflake(event.player.guild_id)
        ) as command:
            if command:
                await bot.rest.create_message(
                    command.channel_id,
                    embed=embed_service.build_message_embed("Queue completed"),
                )
        logger.info("Queue finished on guild: %s", event.player.guild_id)


lavalink_client = lavalink.Client(CONFIG.BOT_ID)

lavalink_client.add_event_hooks(EventHandler())


# On voice state update the bot will update the lavalink node
@bot.listen()
async def voice_state_update(event: hikari.VoiceStateUpdateEvent) -> None:
    # the data needs to be transformed before being handed down to
    # voice_update_handler
    lavalink_data = {
        "t": "VOICE_STATE_UPDATE",
        "d": {
            "guild_id": event.state.guild_id,
            "user_id": event.state.user_id,
            "channel_id": event.state.channel_id,
            "session_id": event.state.session_id,
        },
    }
    await lavalink_client.voice_update_handler(lavalink_data)


@bot.listen()
async def voice_server_update(event: hikari.VoiceServerUpdateEvent) -> None:
    # the data needs to be transformed before being handed down to
    # voice_update_handler
    if event.endpoint:
        lavalink_data = {
            "t": "VOICE_SERVER_UPDATE",
            "d": {
                "guild_id": event.guild_id,
                "endpoint": event.endpoint[6:],  # get rid of wss://
                "token": event.token,
            },
        }
        await lavalink_client.voice_update_handler(lavalink_data)


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
    lavalink_client.add_node(
        host=CONFIG.LAVALINK_HOST,
        port=CONFIG.LAVALINK_PORT,
        password=CONFIG.LAVALINK_PASSWORD,
        region="us",
        name="default-node",
    )


@bot.listen()
async def handle_interaction(event: hikari.InteractionCreateEvent) -> None:
    # Avoid circular import
    from discord_sound_streamer.services import interaction as interaction_service

    if (interaction := event.interaction).type == InteractionType.MESSAGE_COMPONENT:
        await interaction_service.handle_component_interaction(
            cast(hikari.ComponentInteraction, interaction)
        )
    else:
        logger.warning(f"Unhandled interaction type: {interaction.type}")


async def health_check_handler(_: StreamReader, writer: StreamWriter) -> None:
    writer.write("healthy".encode("utf8"))
    await writer.drain()
    writer.close()


async def start_health_check_server() -> None:
    # Start TCP server
    server = await asyncio.start_server(
        health_check_handler, "0.0.0.0", CONFIG.HEALTH_CHECK_PORT
    )
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
    asyncio.get_event_loop_policy().get_event_loop().create_task(
        start_health_check_server()
    )

    bot.run()


if __name__ == "__main__":
    start()
