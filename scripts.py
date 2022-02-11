import time

from discord_sound_streamer.bot import bot, lavalink
from discord_sound_streamer.config import CONFIG
from discord_sound_streamer.websocket import WS


def start():
    if CONFIG.WAIT_FOR_LAVALINK:
        time.sleep(15)

    lavalink._ws = WS(lavalink._ws)
    lavalink.connect()
    bot.run()