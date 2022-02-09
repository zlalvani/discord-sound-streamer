import asyncio

import tanjun
from discord_sound_streamer.bot import bot
from discord_sound_streamer.bot import lavalink
from discord_sound_streamer.datastore.in_memory import SEARCH_WAIT_STORE, SEARCH_WAIT_STORE_LOCK, SearchWaitItem
from discord_sound_streamer.services import play as play_service

component = tanjun.Component()

@component.with_slash_command
@tanjun.with_str_slash_option("query", "search term")
@tanjun.as_slash_command("search", "search for music")
async def search(ctx: tanjun.abc.Context, query: str) -> None:
    if ctx.guild_id:
        key = SearchWaitItem(guild_id=ctx.guild_id, user_id=ctx.author.id)
        search_results = await lavalink.auto_search_tracks(query)
        async with SEARCH_WAIT_STORE_LOCK:
            if key in SEARCH_WAIT_STORE:
                await ctx.respond('You already have a search in progress')
                return

            if search_results:
                SEARCH_WAIT_STORE[key] = search_results[:10]
                await ctx.respond(f'Results: \n' + '\n'.join(f'{i}. {track.title}' for i, track in enumerate(search_results[:10], start=1)) + '\n\n Use /select <num> to choose')
            else:
                await ctx.respond(f'No results found for {query}...')
                return
        
        await asyncio.sleep(10)
        async with SEARCH_WAIT_STORE_LOCK:
            if key in SEARCH_WAIT_STORE:
                await ctx.respond('No selection given...')
                del SEARCH_WAIT_STORE[key]


@component.with_slash_command
@tanjun.with_int_slash_option("selection", "the number of your selection (must have open search)")
@tanjun.as_slash_command("select", "select a search result")
async def select(ctx: tanjun.abc.Context, selection: int) -> None:
    if ctx.guild_id:
        key = SearchWaitItem(guild_id=ctx.guild_id, user_id=ctx.author.id)
        async with SEARCH_WAIT_STORE_LOCK:
            search_results = SEARCH_WAIT_STORE.get(key)
            if search_results:
                if not (len(search_results) >= selection > 0):
                    await ctx.respond('Invalid selection...')
                    return

                song = search_results[selection - 1]
                await play_service.play(ctx, song)
                del SEARCH_WAIT_STORE[key]
            else:
                await ctx.respond('You don\'t have an open search')

loader = component.make_loader()