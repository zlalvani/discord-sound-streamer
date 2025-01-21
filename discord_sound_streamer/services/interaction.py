import asyncio
import math
from urllib.parse import parse_qs, urlencode, urlparse
from lavalink import AudioTrack, DefaultPlayer
from enum import Enum

from hikari.impl.special_endpoints import (
    MessageActionRowBuilder,
)
from pydantic import BaseModel
from hikari import ComponentInteraction, ComponentType, ButtonStyle, ResponseType

from discord_sound_streamer.datastore.models.search import SearchWaitKey
from discord_sound_streamer.logger import logger
from discord_sound_streamer.datastore.operations import search as search_operations
from discord_sound_streamer.polymorphs.responder import InteractionResponder
from discord_sound_streamer.services import youtube as youtube_service
from discord_sound_streamer.services import play as play_service
from discord_sound_streamer.services import embed as embed_service


class InteractionId:
    class Search(str, Enum):
        SELECT = "search.select"

    class Controls(str, Enum):
        SKIP = "controls.skip"
        REFRESH = "controls.refresh"
        SEEK_BACK_BIG = "controls.seek-back-big"
        SEEK_BACK_SMALL = "controls.seek-back-small"
        SEEK_FORWARD_SMALL = "controls.seek-forward-small"
        SEEK_FORWARD_BIG = "controls.seek-forward-big"

    class PageModel(BaseModel):
        page_number: int

    class Queue(str, Enum):
        PREVIOUS_PAGE = "queue.previous-page"
        NEXT_PAGE = "queue.next-page"
        SELECT_PAGE = "queue.select-page"


def _parse_query_string(query_string: str) -> dict[str, list[str] | str]:
    result: dict[str, list[str] | str] = {}

    for key, value in parse_qs(query_string).items():
        if len(value) == 1:
            result[key] = value[0]
        else:
            result[key] = value
    return result


def _encode_interaction_id(identifier: str, data: BaseModel | None = None) -> str:
    if not data:
        return identifier
    urlencoded = urlencode(data.model_dump())

    # can't use f-string here because of the way enums are serialized with __str__
    return identifier + "?" + urlencoded


def build_search_interaction(
    search_results: list[AudioTrack],
) -> list[MessageActionRowBuilder]:
    row = MessageActionRowBuilder()

    menu = row.add_text_menu(InteractionId.Search.SELECT)

    for i, track in enumerate(search_results[:8]):
        label = f"{i + 1}. {track.title}"

        if len(label) > 100:
            label = label[:97] + "..."

        menu.add_option(label, str(i), description=track.author)

    return [row]


def build_current_controls_interaction(
    player: DefaultPlayer, enabled: bool = True
) -> list[MessageActionRowBuilder]:
    if not enabled:
        return []

    commands_row = MessageActionRowBuilder()
    seek_row = MessageActionRowBuilder()

    progress_max_length = 32
    if player.current:
        progress = int(
            (player.position / player.current.duration) * progress_max_length
        )
    else:
        progress = 0

    commands_row.add_interactive_button(
        ButtonStyle.PRIMARY,
        InteractionId.Controls.REFRESH,
        label="█" * progress + "░" * (progress_max_length - progress),
    )

    seek_row.add_interactive_button(
        ButtonStyle.SECONDARY, InteractionId.Controls.SEEK_BACK_BIG, label="<<"
    )
    seek_row.add_interactive_button(
        ButtonStyle.SECONDARY, InteractionId.Controls.SEEK_BACK_SMALL, label="<"
    )
    seek_row.add_interactive_button(
        ButtonStyle.DANGER, InteractionId.Controls.SKIP, emoji="⏭️"
    )
    seek_row.add_interactive_button(
        ButtonStyle.SECONDARY, InteractionId.Controls.SEEK_FORWARD_SMALL, label=">"
    )
    seek_row.add_interactive_button(
        ButtonStyle.SECONDARY, InteractionId.Controls.SEEK_FORWARD_BIG, label=">>"
    )

    return [commands_row, seek_row]


def build_queue_paging_interaction(
    tracks: list[AudioTrack], current_page=0, page_size=8
) -> list[MessageActionRowBuilder]:
    if len(tracks) == 0:
        return []
    # if not player.queue and not player.current:
    #     return []

    select_row = MessageActionRowBuilder()
    button_row = MessageActionRowBuilder()

    # if current_page > 0:
    button_row.add_interactive_button(
        ButtonStyle.PRIMARY,
        _encode_interaction_id(
            InteractionId.Queue.PREVIOUS_PAGE,
            InteractionId.PageModel(page_number=current_page - 1),
        ),
        label="Previous Page",
        emoji="⬅️",
        is_disabled=current_page == 0,
    )

    page_count = math.ceil(len(tracks) / page_size)

    button_row.add_interactive_button(
        ButtonStyle.PRIMARY,
        _encode_interaction_id(
            InteractionId.Queue.NEXT_PAGE,
            InteractionId.PageModel(page_number=current_page + 1),
        ),
        label="Next Page",
        emoji="➡️",
        is_disabled=current_page == page_count - 1,
    )

    menu = select_row.add_text_menu(
        InteractionId.Queue.SELECT_PAGE,
        placeholder=f"Current page: {(current_page + 1)} of {page_count}",
    )

    for i in range(page_count):
        menu.add_option(
            f"{i + 1} of {page_count}",
            _encode_interaction_id(
                InteractionId.Queue.SELECT_PAGE, InteractionId.PageModel(page_number=i)
            ),
        )

    return [r for r in [select_row, button_row] if len(r.components) > 0]


async def handle_component_interaction(interaction: ComponentInteraction):
    parsed = urlparse(interaction.custom_id)
    mode = parsed.path
    if interaction.component_type == ComponentType.TEXT_SELECT_MENU:
        if mode == InteractionId.Search.SELECT:
            selected = int(interaction.values[0])
            await _search_select(interaction, selected)
        elif mode == InteractionId.Queue.SELECT_PAGE:
            data = InteractionId.PageModel.model_validate(
                _parse_query_string(urlparse(interaction.values[0]).query)
            )
            await _refresh_queue(interaction, data)
        else:
            logger.warning(f"Unknown interaction mode: {mode}")
    elif interaction.component_type == ComponentType.BUTTON:
        if mode == InteractionId.Controls.REFRESH:
            await _refresh_controls(interaction)
        elif mode == InteractionId.Controls.SKIP:
            await _skip(interaction)
        elif mode == InteractionId.Controls.SEEK_BACK_BIG:
            await _seek(interaction, -30000)
        elif mode == InteractionId.Controls.SEEK_BACK_SMALL:
            await _seek(interaction, -5000)
        elif mode == InteractionId.Controls.SEEK_FORWARD_BIG:
            await _seek(interaction, 30000)
        elif mode == InteractionId.Controls.SEEK_FORWARD_SMALL:
            await _seek(interaction, 5000)
        elif mode in [InteractionId.Queue.PREVIOUS_PAGE, InteractionId.Queue.NEXT_PAGE]:
            data = InteractionId.PageModel.model_validate(
                _parse_query_string(parsed.query)
            )
            await _refresh_queue(interaction, data)
        else:
            logger.warning(f"Unknown interaction mode: {mode}")
    else:
        logger.warning(f"Unknown component type: {interaction.component_type}")


async def _refresh_queue(
    interaction: ComponentInteraction, data: InteractionId.PageModel
):
    if not interaction.guild_id:
        return

    current_page = data.page_number

    player = play_service.get_player(interaction.guild_id)

    queued = [*([player.current] if player.current else []), *player.queue]

    await interaction.create_initial_response(
        ResponseType.MESSAGE_UPDATE,
        embed=embed_service.build_queue_embed(
            player.position,
            queued,
            current_page=current_page,
        ),
        components=build_queue_paging_interaction(queued, current_page),
    )


async def _refresh_controls(interaction: ComponentInteraction, initial: bool = True):
    if not interaction.guild_id:
        return

    player = play_service.get_player(interaction.guild_id)

    embed = (
        embed_service.build_track_embed(
            player.current, current_position=player.position
        )
        if player.current
        else embed_service.build_message_embed("No track playing")
    )

    if initial:
        await interaction.create_initial_response(
            ResponseType.MESSAGE_UPDATE,
            embed=embed,
            components=build_current_controls_interaction(
                player, enabled=player.current is not None
            ),
        )
    else:
        await interaction.edit_message(
            interaction.message.id,
            embeds=[
                embed,
            ],
            components=build_current_controls_interaction(
                player, enabled=player.current is not None
            ),
        )


async def _skip(interaction: ComponentInteraction):
    if not interaction.guild_id:
        return

    player = play_service.get_player(interaction.guild_id)
    if not player.current:
        await _refresh_controls(interaction)
        return

    responder = InteractionResponder(interaction)

    await responder.respond_message(f"Skipping {player.current.title}...")
    await player.skip()
    await _refresh_controls(interaction, initial=False)


async def _seek(interaction: ComponentInteraction, offset: int):
    if not interaction.guild_id:
        return

    player = play_service.get_player(interaction.guild_id)
    if not player.current:
        await _refresh_controls(interaction)
        return

    last_update = player._last_update
    await player.seek(max(0, min(player.position + offset, player.current.duration)))

    # Wait for the player to update to make sure we have the latest state
    attempts = 0
    while last_update == player._last_update and attempts < 5:
        await asyncio.sleep(0.1)
        attempts += 1

    await _refresh_controls(interaction)


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
            interaction.message.id,
            embeds=[
                embed_service.build_search_embed(data.query, data.tracks, selected)
            ],
            components=[],
        )
