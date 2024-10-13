import tanjun
import hikari
from hikari import ComponentInteraction, Embed
from hikari.api import ComponentBuilder
from attrs import define, field

from typing import Protocol

from discord_sound_streamer.services import embed as embed_service


class Responder(Protocol):
    async def respond(
        self,
        *,
        embed: Embed | None = None,
        embeds: list[Embed] | None = None,
        component: ComponentBuilder | None = None,
        components: list[ComponentBuilder] | None = None,
    ) -> None: ...

    async def respond_message(self, message: str, ephemeral: bool = False) -> None: ...


@define
class SlashCommandResponder:
    _context: tanjun.abc.Context = field(alias="context")

    async def respond(
        self,
        *,
        embed: Embed | None = None,
        embeds: list[Embed] | None = None,
        component: ComponentBuilder | None = None,
        components: list[ComponentBuilder] | None = None,
    ) -> None:
        await self._context.respond(
            embed=embed if embed is not None else hikari.UNDEFINED,
            embeds=embeds if embeds is not None else hikari.UNDEFINED,
            component=component if component is not None else hikari.UNDEFINED,
            components=components if components is not None else hikari.UNDEFINED,
        )

    async def respond_message(self, message: str, ephemeral: bool = False) -> None:
        await embed_service.reply_message(self._context, message)


@define
class InteractionResponder:
    _interaction: ComponentInteraction = field(alias="interaction")

    async def respond(
        self,
        *,
        embed: Embed | None = None,
        embeds: list[Embed] | None = None,
        component: ComponentBuilder | None = None,
        components: list[ComponentBuilder] | None = None,
    ) -> None:
        await self._interaction.create_initial_response(
            response_type=hikari.ResponseType.MESSAGE_CREATE,
            embed=embed if embed is not None else hikari.UNDEFINED,
            embeds=embeds if embeds is not None else hikari.UNDEFINED,
            component=component if component is not None else hikari.UNDEFINED,
            components=components if components is not None else hikari.UNDEFINED,
        )

    async def respond_message(self, message: str, ephemeral: bool = False) -> None:
        embed = embed_service.build_message_embed(message)

        await self._interaction.create_initial_response(
            response_type=hikari.ResponseType.MESSAGE_CREATE,
            flags=hikari.MessageFlag.EPHEMERAL if ephemeral else hikari.UNDEFINED,
            embed=embed,
        )
