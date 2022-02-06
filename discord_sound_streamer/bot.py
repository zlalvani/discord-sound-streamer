import hikari
import tanjun
from lavaplayer import LavalinkClient
# from discord_sound_streamer.commands.play import component as play_component

from discord_sound_streamer.config import CONFIG

bot = hikari.GatewayBot(token=CONFIG.BOT_TOKEN)

client = ( 
    tanjun.Client.from_gateway_bot(
        bot,
        mention_prefix=True,
        declare_global_commands=CONFIG.GUILD_ID if CONFIG.GUILD_ID else False
    )
)

lavalink = LavalinkClient(
    host=CONFIG.LAVALINK_HOST,  # Lavalink host
    port=CONFIG.LAVALINK_PORT,  # Lavalink port
    password=CONFIG.LAVALINK_PASSWORD,  # Lavalink password
    user_id=CONFIG.BOT_ID,  # Lavalink bot id
    is_ssl=False
)


# On voice state update the bot will update the lavalink node
@bot.listen(hikari.VoiceStateUpdateEvent)
async def voice_state_update(event: hikari.VoiceStateUpdateEvent):
    await lavalink.raw_voice_state_update(event.guild_id, event.state.user_id, event.state.session_id, event.state.channel_id)


@bot.listen(hikari.VoiceServerUpdateEvent)
async def voice_server_update(event: hikari.VoiceServerUpdateEvent):
    await lavalink.raw_voice_server_update(event.guild_id, event.endpoint, event.token)


client.load_modules('discord_sound_streamer.commands.play')
