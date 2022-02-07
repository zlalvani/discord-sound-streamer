from discord_sound_streamer.bot import bot, lavalink

def start():
    lavalink.connect()
    bot.run()