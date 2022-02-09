import time

from discord_sound_streamer.bot import bot, lavalink
from discord_sound_streamer.config import CONFIG


def start():
    if CONFIG.WAIT_FOR_LAVALINK:
        time.sleep(5)
    lavalink.connect()
    bot.run()