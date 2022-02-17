import asyncio

import tanjun
from discord_sound_streamer.bot import lavalink
from discord_sound_streamer.datastore.models.search import SearchWaitValue
from discord_sound_streamer.datastore.operations.search import SearchWaitKey
from discord_sound_streamer.services import play as play_service
from discord_sound_streamer.services import embed as embed_service
from discord_sound_streamer.datastore.operations import search as search_operations

component = tanjun.Component()

@component.with_slash_command
@tanjun.with_str_slash_option("query", "search term")
@tanjun.as_slash_command("search", "search for music")
async def search(ctx: tanjun.abc.Context, query: str) -> None:
    if ctx.guild_id:
        key = SearchWaitKey(guild_id=ctx.guild_id, user_id=ctx.author.id)
        search_results = await lavalink.auto_search_tracks(query)

        # First, create a search for the guildmember and store it
        async with search_operations.get_search_wait_value(key) as data:
            if data:
                await embed_service.reply_message(ctx, 'You already have a search in progress')
                return

            if search_results:
                # Truncate the search results to 8 because that's the max number of results we can display
                search_results = search_results[:8]
                data = SearchWaitValue(tracks=search_results)
                search_operations.set_search_wait_value(key, data)
                await ctx.respond(embed=embed_service.build_search_embed(query, search_results))
            else:
                await embed_service.reply_message(ctx, f'No results found for {query}...')
                return
        
        # After 30 seconds, the search is considered expired. If it still exists, remove it. 
        await asyncio.sleep(30)
        async with search_operations.get_search_wait_value(key) as data:
            if data:
                await embed_service.reply_message(ctx, 'No selection given...')
                search_operations.remove_search_wait_value(key)


@component.with_slash_command
@tanjun.with_int_slash_option("selection", "the number of your selection (must have open search)")
@tanjun.as_slash_command("select", "select a search result")
async def select(ctx: tanjun.abc.Context, selection: int) -> None:
    if ctx.guild_id:
        key = SearchWaitKey(guild_id=ctx.guild_id, user_id=ctx.author.id)
        async with search_operations.get_search_wait_value(key) as data:
            if data:
                if 0 < selection <= len(data.tracks):
                    await play_service.play(ctx, data.tracks[selection - 1])
                    search_operations.remove_search_wait_value(key)
                else:
                    await embed_service.reply_message(ctx, f'Invalid selection. Please choose a number between 1 and {len(data.tracks)}')
            else:
                await embed_service.reply_message(ctx, 'No search in progress')


loader = component.make_loader()