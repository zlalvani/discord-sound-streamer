from lavalink import AudioTrack
from enum import Enum

from hikari.impl.special_endpoints import (
    MessageActionRowBuilder,
)
from hikari import ComponentInteraction, ComponentType

from discord_sound_streamer.datastore.models.search import SearchWaitKey
from discord_sound_streamer.logger import logger
from discord_sound_streamer.datastore.operations import search as search_operations
from discord_sound_streamer.polymorphs.responder import InteractionResponder
from discord_sound_streamer.services import youtube as youtube_service
from discord_sound_streamer.services import play as play_service


class InteractionMode(str, Enum):
    SEARCH_SELECT = "search_select"


def build_search_interaction(search_results: list[AudioTrack]):
    row = MessageActionRowBuilder()

    menu = row.add_text_menu(InteractionMode.SEARCH_SELECT)

    for i, track in enumerate(search_results[:8]):
        label = f"{i + 1}. {track.title}"

        if len(label) > 100:
            label = label[:97] + "..."

        menu.add_option(label, str(i), description=track.author)

    return [row]


async def handle_component_interaction(interaction: ComponentInteraction):
    if interaction.component_type == ComponentType.TEXT_SELECT_MENU:
        mode = interaction.custom_id
        if mode == InteractionMode.SEARCH_SELECT:
            selected = int(interaction.values[0])
            await _search_select(interaction, selected)
        else:
            logger.warning(f"Unknown interaction mode: {mode}")
    else:
        logger.warning(f"Unknown component type: {interaction.component_type}")


async def _search_select(interaction: ComponentInteraction, selected: int):
    guild_id = interaction.guild_id

    if not guild_id:
        return

    key = SearchWaitKey(guild_id=guild_id, user_id=interaction.user.id)
    responder = InteractionResponder(interaction)
    async with search_operations.get_search_wait_value(key) as data:
        if not data:
            await responder.respond_message("No search in progress", ephemeral=True)
            return

        if data.search_message_id != interaction.message.id:
            await responder.respond_message(
                "This search is no longer active. Please start a new search.",
                ephemeral=True,
            )
            return

        if selected < 0 or selected >= len(data.tracks):
            await responder.respond_message(
                f"Invalid selection. Please choose a number between 1 and {len(data.tracks)}",
                ephemeral=True,
            )
            return

        track = data.tracks[selected]
        if await youtube_service.is_age_restricted(track):
            await responder.respond_message(
                "Selection is age restricted. Please try another. ",
                ephemeral=True,
            )
        guild = await interaction.fetch_guild()
        await play_service.play_track(
            responder, guild, interaction.user.id, data.tracks[selected]
        )
        search_operations.remove_search_wait_value(key)

        await interaction.edit_message(
            interaction.message.id, embeds=interaction.message.embeds, components=[]
        )
