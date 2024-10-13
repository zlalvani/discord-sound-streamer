import asyncio
from datetime import UTC, datetime

import tanjun

from discord_sound_streamer.datastore.models.search import SearchWaitValue
from discord_sound_streamer.datastore.operations import search as search_operations
from discord_sound_streamer.datastore.operations.search import SearchWaitKey
from discord_sound_streamer.polymorphs.responder import SlashCommandResponder
from discord_sound_streamer.services import embed as embed_service
from discord_sound_streamer.services import lava as lava_service
from discord_sound_streamer.services import play as play_service
from discord_sound_streamer.services import youtube as youtube_service
from discord_sound_streamer.services import interaction as interaction_service

component = tanjun.Component()


@component.with_slash_command
@tanjun.with_str_slash_option("query", "search term")
@tanjun.as_slash_command("search", "search for music", default_to_ephemeral=True)
async def search(ctx: tanjun.abc.SlashContext, query: str) -> None:
    if not ctx.guild_id:
        return

    key = SearchWaitKey(guild_id=ctx.guild_id, user_id=ctx.author.id)

    # Truncate the search results to 8 because that's the max number of results we can display
    search_results = (await lava_service.get_tracks(query))[:8]
    searched_at = datetime.now(tz=UTC)

    if not search_results:
        await embed_service.reply_message(ctx, f"No results found for {query}...")
        return

    # First, create a search for the guildmember and store it
    async with search_operations.get_search_wait_value(key) as data:
        if data:
            original_message = await data.interaction.fetch_initial_response()

            await data.interaction.edit_initial_response(
                embeds=original_message.embeds,
                components=[],
            )

        await ctx.respond(
            embed=embed_service.build_search_embed(query, search_results),
            components=interaction_service.build_search_interaction(search_results),
        )

        res = await ctx.fetch_initial_response()

        if res is None:
            raise ValueError("Failed to send search message")
        data = SearchWaitValue(
            tracks=search_results,
            searched_at=searched_at,
            search_message_id=res.id,
            interaction=ctx.interaction,
        )
        search_operations.set_search_wait_value(key, data)

    # After 30 seconds, the search is considered expired. If it still exists, remove it.
    await asyncio.sleep(30)
    async with search_operations.get_search_wait_value(key) as data:
        if data and data.searched_at == searched_at:
            await embed_service.reply_message(ctx, "No selection given...")
            search_operations.remove_search_wait_value(key)
            if res:
                await ctx.edit_initial_response(embeds=res.embeds, components=[])


@component.with_slash_command
@tanjun.with_int_slash_option(
    "selection", "the number of your selection (must have open search)"
)
@tanjun.as_slash_command("select", "select a search result")
async def select(ctx: tanjun.abc.SlashContext, selection: int) -> None:
    if not ctx.guild_id:
        return

    key = SearchWaitKey(guild_id=ctx.guild_id, user_id=ctx.author.id)

    async with search_operations.get_search_wait_value(key) as data:
        if not data:
            await embed_service.reply_message(ctx, "No search in progress")
            return

        if 0 < selection <= len(data.tracks):
            # TODO investigate filtering age-restricted results here instead of in search (because it's slow)
            track = data.tracks[selection - 1]
            if await youtube_service.is_age_restricted(track):
                await embed_service.reply_message(
                    ctx, "Selection is age restricted. Please try another. "
                )
                return
            responder = SlashCommandResponder(ctx)
            guild = await ctx.fetch_guild()
            author_id = ctx.author.id
            await play_service.play_track(
                responder, guild, author_id, data.tracks[selection - 1]
            )
            search_operations.remove_search_wait_value(key)

            original_message = await data.interaction.fetch_initial_response()

            await data.interaction.edit_initial_response(
                embeds=original_message.embeds,
                components=[],
            )
        else:
            await embed_service.reply_message(
                ctx,
                f"Invalid selection. Please choose a number between 1 and {len(data.tracks)}",
            )


loader = component.make_loader()
